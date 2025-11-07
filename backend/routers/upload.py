from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List
import os
import shutil
from datetime import datetime
import pandas as pd
from pathlib import Path

from backend.database import get_db
from backend.models.models import Dataset
from backend.schemas.dataset import DatasetResponse
from backend.config import get_settings

settings = get_settings()
router = APIRouter(prefix="/upload", tags=["upload"])


# 支持的文件类型
ALLOWED_EXTENSIONS = {
    '.csv', '.xlsx', '.xls', '.json', '.parquet'
}

# 文件类型对应的 MIME types
ALLOWED_CONTENT_TYPES = {
    'text/csv',
    'application/vnd.ms-excel',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'application/json',
    'application/octet-stream'  # parquet 文件
}


def validate_file(file: UploadFile) -> None:
    """
    验证上传的文件

    检查项：
    1. 文件扩展名是否支持
    2. 文件 MIME 类型是否允许
    3. 文件大小是否超过限制

    Args:
        file: 上传的文件对象

    Raises:
        HTTPException: 如果验证失败
    """
    # 检查文件扩展名
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件类型。支持的类型: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    # 检查 MIME 类型
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail="不支持的文件格式"
        )


def save_upload_file(file: UploadFile) -> tuple[str, int]:
    """
    保存上传的文件到服务器

    文件命名规则: timestamp_originalfilename
    例如: 20231106_123456_data.csv

    Args:
        file: 上传的文件对象

    Returns:
        tuple: (保存的文件路径, 文件大小)
    """
    # 确保上传目录存在
    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)

    # 生成唯一文件名（加时间戳避免重名）
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_filename = f"{timestamp}_{file.filename}"
    file_path = upload_dir / safe_filename

    # 保存文件
    file_size = 0
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        file_size = file_path.stat().st_size

    # 检查文件大小
    if file_size > settings.max_file_size:
        # 删除超大文件
        file_path.unlink()
        raise HTTPException(
            status_code=400,
            detail=f"文件大小超过限制 ({settings.max_file_size / 1024 / 1024}MB)"
        )

    return str(file_path), file_size


def analyze_dataset(file_path: str) -> dict:
    """
    分析数据集，提取元数据

    提取信息：
    1. 行数
    2. 列信息（列名、数据类型、非空数量等）
    3. 基本统计信息

    Args:
        file_path: 文件路径

    Returns:
        dict: 包含 schema 和 row_count 的字典
    """
    file_ext = Path(file_path).suffix.lower()

    try:
        # 根据文件类型读取数据
        if file_ext == '.csv':
            df = pd.read_csv(file_path)
        elif file_ext in ['.xlsx', '.xls']:
            df = pd.read_excel(file_path)
        elif file_ext == '.json':
            df = pd.read_json(file_path)
        elif file_ext == '.parquet':
            df = pd.read_parquet(file_path)
        else:
            raise ValueError(f"不支持的文件类型: {file_ext}")

        # 提取 schema 信息
        schema = []
        for col in df.columns:
            col_info = {
                "name": col,
                "dtype": str(df[col].dtype),
                "non_null_count": int(df[col].count()),
                "null_count": int(df[col].isna().sum()),
                "unique_count": int(df[col].nunique())
            }

            # 如果是数值类型，添加统计信息
            if pd.api.types.is_numeric_dtype(df[col]):
                col_info.update({
                    "min": float(df[col].min()) if not pd.isna(df[col].min()) else None,
                    "max": float(df[col].max()) if not pd.isna(df[col].max()) else None,
                    "mean": float(df[col].mean()) if not pd.isna(df[col].mean()) else None,
                })

            schema.append(col_info)

        return {
            "schema_json": schema,
            "row_count": len(df)
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"解析文件失败: {str(e)}"
        )


@router.post("/", response_model=DatasetResponse)
async def upload_file(
    file: UploadFile = File(...),
    name: str = None,
    description: str = None,
    db: Session = Depends(get_db)
):
    """
    上传数据文件

    支持的文件格式：
    - CSV (.csv)
    - Excel (.xlsx, .xls)
    - JSON (.json)
    - Parquet (.parquet)

    工作流程：
    1. 验证文件类型和大小
    2. 保存文件到服务器
    3. 解析文件，提取 schema 信息
    4. 将元数据保存到数据库
    5. 返回数据集信息

    Args:
        file: 上传的文件
        name: 数据集名称（可选，默认使用文件名）
        description: 数据集描述（可选）
        db: 数据库会话

    Returns:
        DatasetResponse: 创建的数据集信息
    """
    # 1. 验证文件
    validate_file(file)

    # 2. 保存文件
    file_path, file_size = save_upload_file(file)

    try:
        # 3. 分析数据集
        analysis_result = analyze_dataset(file_path)

        # 4. 创建数据库记录
        dataset = Dataset(
            name=name or file.filename,
            description=description,
            file_path=file_path,
            original_filename=file.filename,
            file_size=file_size,
            file_type=Path(file.filename).suffix.lower(),
            schema_json=analysis_result["schema_json"],
            row_count=analysis_result["row_count"],
            status="active"
        )

        db.add(dataset)
        db.commit()
        db.refresh(dataset)

        return dataset

    except Exception as e:
        # 如果出错，删除已上传的文件
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(
            status_code=500,
            detail=f"处理文件时出错: {str(e)}"
        )


@router.get("/datasets", response_model=List[DatasetResponse])
async def list_datasets(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    获取所有数据集列表

    支持分页查询

    Args:
        skip: 跳过的记录数（用于分页）
        limit: 返回的最大记录数
        db: 数据库会话

    Returns:
        List[DatasetResponse]: 数据集列表
    """
    datasets = db.query(Dataset)\
        .filter(Dataset.status == "active")\
        .order_by(Dataset.created_at.desc())\
        .offset(skip)\
        .limit(limit)\
        .all()

    return datasets


@router.get("/datasets/{dataset_id}", response_model=DatasetResponse)
async def get_dataset(dataset_id: int, db: Session = Depends(get_db)):
    """
    获取单个数据集的详细信息

    Args:
        dataset_id: 数据集ID
        db: 数据库会话

    Returns:
        DatasetResponse: 数据集信息
    """
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()

    if not dataset:
        raise HTTPException(status_code=404, detail="数据集不存在")

    return dataset


@router.delete("/datasets/{dataset_id}")
async def delete_dataset(dataset_id: int, db: Session = Depends(get_db)):
    """
    删除数据集

    同时删除：
    1. 数据库记录（软删除，设置 status 为 deleted）
    2. 服务器上的文件

    Args:
        dataset_id: 数据集ID
        db: 数据库会话

    Returns:
        dict: 删除结果
    """
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()

    if not dataset:
        raise HTTPException(status_code=404, detail="数据集不存在")

    # 软删除数据库记录
    dataset.status = "deleted"

    # 删除文件
    if os.path.exists(dataset.file_path):
        os.remove(dataset.file_path)

    db.commit()

    return {"message": f"数据集 {dataset.name} 已删除"}
