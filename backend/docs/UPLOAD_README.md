# 数据分析 Agent - 文件上传功能

## 功能概述

文件上传功能允许用户上传各种格式的数据文件（CSV、Excel、JSON、Parquet），系统会自动：
1. 验证文件类型和大小
2. 保存文件到服务器
3. 分析数据结构（schema）
4. 提取统计信息
5. 将元数据存储到数据库

---

## 架构说明

### 1. **核心文件**

```
backend/
├── models/
│   └── models.py          # 数据库模型（SQLAlchemy ORM）
├── schemas/
│   └── dataset.py         # API 数据模型（Pydantic）
├── routers/
│   └── upload.py          # 上传路由和业务逻辑
├── database.py            # 数据库连接配置
├── config.py              # 应用配置
└── main.py                # FastAPI 应用入口
```

### 2. **数据流程**

```
用户上传文件
    ↓
验证文件（类型、大小）
    ↓
保存到服务器（./backend/uploads/）
    ↓
解析文件（pandas）
    ↓
提取 schema 信息
    ↓
保存元数据到数据库
    ↓
返回数据集信息
```

---

## API 端点

### 1. 上传文件
```http
POST /upload/
```

**请求参数：**
- `file`: 文件（必需）
- `name`: 数据集名称（可选，默认使用文件名）
- `description`: 数据集描述（可选）

**支持的文件格式：**
- CSV (`.csv`)
- Excel (`.xlsx`, `.xls`)
- JSON (`.json`)
- Parquet (`.parquet`)

**响应示例：**
```json
{
  "id": 1,
  "name": "员工数据",
  "description": "包含员工信息的数据集",
  "file_path": "./backend/uploads/20231106_123456_data.csv",
  "original_filename": "data.csv",
  "file_size": 1024,
  "file_type": ".csv",
  "row_count": 100,
  "schema_json": [
    {
      "name": "id",
      "dtype": "int64",
      "non_null_count": 100,
      "null_count": 0,
      "unique_count": 100,
      "min": 1,
      "max": 100,
      "mean": 50.5
    },
    {
      "name": "name",
      "dtype": "object",
      "non_null_count": 100,
      "null_count": 0,
      "unique_count": 100
    }
  ],
  "status": "active",
  "created_at": "2023-11-06T12:34:56"
}
```

### 2. 获取数据集列表
```http
GET /upload/datasets?skip=0&limit=100
```

**查询参数：**
- `skip`: 跳过的记录数（分页）
- `limit`: 返回的最大记录数

### 3. 获取单个数据集详情
```http
GET /upload/datasets/{dataset_id}
```

### 4. 删除数据集
```http
DELETE /upload/datasets/{dataset_id}
```

注意：删除操作会：
- 软删除数据库记录（设置 status='deleted'）
- 删除服务器上的文件

---

## 关键功能详解

### 1. **文件验证** (`validate_file`)

```python
def validate_file(file: UploadFile) -> None:
    # 检查文件扩展名
    # 检查 MIME 类型
```

**作用：**
- 防止上传不支持的文件类型
- 提前拦截恶意文件

### 2. **文件保存** (`save_upload_file`)

```python
def save_upload_file(file: UploadFile) -> tuple[str, int]:
    # 生成唯一文件名（时间戳 + 原始文件名）
    # 保存到 uploads 目录
    # 返回文件路径和大小
```

**特点：**
- 使用时间戳避免文件名冲突
- 自动创建 uploads 目录
- 检查文件大小限制

### 3. **数据分析** (`analyze_dataset`)

```python
def analyze_dataset(file_path: str) -> dict:
    # 使用 pandas 读取文件
    # 提取列信息（类型、非空数量、唯一值等）
    # 对数值列计算统计信息（min, max, mean）
```

**提取的信息：**
- 行数
- 列名和数据类型
- 非空值数量
- 唯一值数量
- 数值列的统计信息（最小值、最大值、平均值）

---

## 配置说明

在 `.env` 文件中配置：

```env
# 文件上传配置
UPLOAD_DIR=./backend/uploads      # 上传目录
MAX_FILE_SIZE=10485760            # 最大文件大小（10MB）

# 数据库配置
DATABASE_URL=sqlite:///./data.db  # SQLite 数据库路径
```

---

## 使用示例

### Python 示例（使用 requests）

```python
import requests

# 上传文件
with open('data.csv', 'rb') as f:
    files = {'file': ('data.csv', f, 'text/csv')}
    data = {
        'name': '我的数据集',
        'description': '这是一个测试数据集'
    }
    response = requests.post('http://localhost:8000/upload/', files=files, data=data)
    dataset = response.json()
    print(f"上传成功！数据集 ID: {dataset['id']}")

# 获取数据集列表
response = requests.get('http://localhost:8000/upload/datasets')
datasets = response.json()
for ds in datasets:
    print(f"{ds['id']}: {ds['name']} ({ds['row_count']} 行)")
```

### cURL 示例

```bash
# 上传文件
curl -X POST "http://localhost:8000/upload/" \
  -F "file=@data.csv" \
  -F "name=我的数据集" \
  -F "description=测试数据"

# 获取数据集列表
curl -X GET "http://localhost:8000/upload/datasets"

# 获取单个数据集
curl -X GET "http://localhost:8000/upload/datasets/1"

# 删除数据集
curl -X DELETE "http://localhost:8000/upload/datasets/1"
```

---

## 启动服务

```bash
# 安装依赖
pip install -r requirements.txt

# 启动服务器
uvicorn backend.main:app --reload

# 测试功能
python test_upload.py
```

访问 API 文档：http://localhost:8000/docs

---

## 数据库模型

### Dataset 表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| name | String(100) | 数据集名称 |
| description | Text | 数据集描述 |
| file_path | String(255) | 文件路径 |
| original_filename | String(255) | 原始文件名 |
| file_size | Integer | 文件大小（字节） |
| file_type | String(50) | 文件类型（扩展名） |
| schema_json | JSON | 数据结构信息 |
| row_count | Integer | 行数 |
| tags | JSON | 标签 |
| status | String(20) | 状态（active/deleted） |
| created_at | DateTime | 创建时间 |
| updated_at | DateTime | 更新时间 |

---

## 安全性考虑

1. **文件类型验证**：只允许特定的文件扩展名和 MIME 类型
2. **文件大小限制**：默认限制 10MB，可在配置中调整
3. **文件名处理**：添加时间戳避免冲突和覆盖
4. **错误处理**：上传失败时自动清理已保存的文件
5. **软删除**：删除操作不直接删除数据库记录，方便恢复

---

## 未来扩展

1. **文件预览**：添加数据预览接口
2. **数据转换**：支持不同格式之间的转换
3. **数据清洗**：自动检测和处理缺失值、异常值
4. **权限控制**：添加用户认证和权限管理
5. **云存储**：支持 S3、OSS 等云存储服务
6. **异步处理**：对大文件使用后台任务处理
