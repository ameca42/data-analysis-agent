"""
Chat API Router
提供自然语言查询和SQL执行的聊天接口
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List
import json

from backend.database import get_db
from backend.models.models import Dataset, ChatSession
from backend.schemas.chat import (
    ChatQueryRequest,
    ChatQueryResponse,
    DirectSQLRequest,
    SQLExecutionResult,
    ChatHistoryRequest,
    ChatHistoryResponse,
    DatasetSchemaResponse,
    ErrorResponse
)
from backend.utils.llm_client import get_nl2sql_converter, get_query_explainer
from backend.utils.sql_tools import SQLExecutor, SchemaRetriever
import os


router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/query", response_model=ChatQueryResponse, summary="Natural language query")
async def chat_query(
    request: ChatQueryRequest,
    db: Session = Depends(get_db)
):
    """
    自然语言查询接口

    工作流程:
    1. 获取数据集和schema信息
    2. 使用LLM将自然语言转换为SQL
    3. 执行SQL查询
    4. (可选)生成自然语言解释
    5. 保存到聊天会话表

    Args:
        request: 查询请求 (question, dataset_id, etc.)
        db: 数据库会话

    Returns:
        ChatQueryResponse: 查询结果和解释

    Raises:
        HTTPException: 数据集不存在或查询失败
    """
    # 1. 获取数据集
    dataset = db.query(Dataset).filter(Dataset.id == request.dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    # 检查文件是否存在
    if not os.path.exists(dataset.file_path):
        raise HTTPException(status_code=404, detail="Dataset file not found")

    try:
        # 2. 转换自然语言为SQL
        nl2sql = get_nl2sql_converter()
        sql_query = await nl2sql.convert(
            question=request.question,
            schema=dataset.schema_json,
            table_name="data"
        )

        # 3. 执行SQL查询
        with SQLExecutor(dataset.file_path) as executor:
            execution_result = executor.execute(
                sql=sql_query,
                max_rows=request.max_rows
            )

        # 检查执行是否成功
        if not execution_result["success"]:
            # 保存失败的查询到聊天记录
            chat_session = ChatSession(
                dataset_id=request.dataset_id,
                role="user",
                question=request.question,
                answer=f"Query failed: {execution_result.get('error', 'Unknown error')}",
                context={
                    "sql": sql_query,
                    "error": execution_result.get("error")
                },
                message_type="error"
            )
            db.add(chat_session)
            db.commit()

            raise HTTPException(
                status_code=400,
                detail=f"SQL execution failed: {execution_result.get('error')}"
            )

        # 4. 生成自然语言解释 (可选)
        explanation = None
        if request.generate_explanation and execution_result["success"]:
            try:
                explainer = get_query_explainer()
                explanation = await explainer.explain_results(
                    question=request.question,
                    sql_query=sql_query,
                    results=execution_result["data"]
                )
            except Exception as e:
                # 解释生成失败不影响主流程
                explanation = f"Results retrieved successfully. (Explanation generation failed: {str(e)})"

        # 5. 保存到聊天会话
        chat_session = ChatSession(
            dataset_id=request.dataset_id,
            role="assistant",
            question=request.question,
            answer=explanation or f"Query returned {execution_result['row_count']} rows.",
            context={
                "sql": sql_query,
                "execution_result": {
                    "row_count": execution_result["row_count"],
                    "execution_time": execution_result["execution_time"],
                    "columns": execution_result["columns"]
                }
            },
            message_type="query",
            tokens_used=None  # TODO: 从LLM响应中获取
        )
        db.add(chat_session)
        db.commit()
        db.refresh(chat_session)

        # 6. 构建响应
        return ChatQueryResponse(
            question=request.question,
            sql_generated=sql_query,
            execution_result=SQLExecutionResult(**execution_result),
            explanation=explanation,
            session_id=chat_session.id,
            dataset_id=request.dataset_id,
            created_at=chat_session.created_at
        )

    except HTTPException:
        raise
    except Exception as e:
        # 捕获其他异常
        import traceback
        error_detail = traceback.format_exc()
        print(f"Chat query error: {error_detail}")

        raise HTTPException(
            status_code=500,
            detail=f"Query processing failed: {str(e)}"
        )


@router.post("/sql", response_model=SQLExecutionResult, summary="Direct SQL execution")
async def execute_sql(
    request: DirectSQLRequest,
    db: Session = Depends(get_db)
):
    """
    直接SQL执行接口 (高级功能)

    允许用户直接执行SQL查询,适合高级用户

    Args:
        request: SQL查询请求
        db: 数据库会话

    Returns:
        SQLExecutionResult: SQL执行结果

    Raises:
        HTTPException: 数据集不存在或SQL执行失败
    """
    # 获取数据集
    dataset = db.query(Dataset).filter(Dataset.id == request.dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    if not os.path.exists(dataset.file_path):
        raise HTTPException(status_code=404, detail="Dataset file not found")

    try:
        # 执行SQL
        with SQLExecutor(dataset.file_path) as executor:
            execution_result = executor.execute(
                sql=request.sql,
                max_rows=request.max_rows
            )

        # 保存到聊天会话 (仅成功的查询)
        if execution_result["success"]:
            chat_session = ChatSession(
                dataset_id=request.dataset_id,
                role="user",
                question=f"[Direct SQL] {request.sql}",
                answer=f"Query returned {execution_result['row_count']} rows.",
                context={
                    "sql": request.sql,
                    "execution_result": {
                        "row_count": execution_result["row_count"],
                        "execution_time": execution_result["execution_time"]
                    }
                },
                message_type="direct_sql"
            )
            db.add(chat_session)
            db.commit()

        return SQLExecutionResult(**execution_result)

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"SQL execution failed: {str(e)}"
        )


@router.get("/history", response_model=ChatHistoryResponse, summary="Get chat history")
async def get_chat_history(
    dataset_id: int,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """
    获取聊天历史记录

    Args:
        dataset_id: 数据集ID
        limit: 返回的最大消息数 (默认50)
        offset: 偏移量,用于分页 (默认0)
        db: 数据库会话

    Returns:
        ChatHistoryResponse: 聊天历史

    Raises:
        HTTPException: 数据集不存在
    """
    # 检查数据集是否存在
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    # 查询聊天记录
    total_count = db.query(ChatSession).filter(
        ChatSession.dataset_id == dataset_id
    ).count()

    messages = db.query(ChatSession).filter(
        ChatSession.dataset_id == dataset_id
    ).order_by(
        ChatSession.created_at.desc()
    ).offset(offset).limit(limit).all()

    return ChatHistoryResponse(
        dataset_id=dataset_id,
        total_messages=total_count,
        messages=messages
    )


@router.delete("/history/{session_id}", summary="Delete chat message")
async def delete_chat_message(
    session_id: int,
    db: Session = Depends(get_db)
):
    """
    删除单条聊天记录

    Args:
        session_id: 聊天会话ID
        db: 数据库会话

    Returns:
        删除确认消息

    Raises:
        HTTPException: 消息不存在
    """
    chat_session = db.query(ChatSession).filter(ChatSession.id == session_id).first()

    if not chat_session:
        raise HTTPException(status_code=404, detail="Chat message not found")

    db.delete(chat_session)
    db.commit()

    return {"message": "Chat message deleted successfully", "id": session_id}


@router.delete("/history/dataset/{dataset_id}", summary="Clear dataset chat history")
async def clear_dataset_history(
    dataset_id: int,
    db: Session = Depends(get_db)
):
    """
    清空数据集的所有聊天记录

    Args:
        dataset_id: 数据集ID
        db: 数据库会话

    Returns:
        删除确认消息

    Raises:
        HTTPException: 数据集不存在
    """
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    # 删除所有聊天记录
    deleted_count = db.query(ChatSession).filter(
        ChatSession.dataset_id == dataset_id
    ).delete()

    db.commit()

    return {
        "message": f"Cleared chat history for dataset {dataset_id}",
        "deleted_count": deleted_count
    }


@router.get("/schema/{dataset_id}", response_model=DatasetSchemaResponse, summary="Get dataset schema")
async def get_dataset_schema(
    dataset_id: int,
    db: Session = Depends(get_db)
):
    """
    获取数据集Schema信息

    用于前端显示表结构,辅助用户提问

    Args:
        dataset_id: 数据集ID
        db: 数据库会话

    Returns:
        DatasetSchemaResponse: Schema信息

    Raises:
        HTTPException: 数据集不存在
    """
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    # 提取schema信息
    numeric_cols = SchemaRetriever.get_numeric_columns(dataset.schema_json)
    all_cols = SchemaRetriever.get_column_names(dataset.schema_json)

    return DatasetSchemaResponse(
        dataset_id=dataset.id,
        dataset_name=dataset.name,
        row_count=dataset.row_count,
        schema=dataset.schema_json,
        numeric_columns=numeric_cols,
        all_columns=all_cols
    )
