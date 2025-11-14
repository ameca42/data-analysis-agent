"""
Chat相关的Pydantic Schema定义
用于API请求和响应的数据验证
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime


# ========== Request Schemas ==========

class ChatQueryRequest(BaseModel):
    """
    聊天查询请求
    用户提问,系统将自然语言转换为SQL并执行
    """
    question: str = Field(..., description="用户的自然语言问题", min_length=1, max_length=1000)
    dataset_id: int = Field(..., description="数据集ID", gt=0)
    generate_explanation: bool = Field(default=True, description="是否生成自然语言解释")
    max_rows: int = Field(default=100, description="最大返回行数", ge=1, le=1000)

    class Config:
        json_schema_extra = {
            "example": {
                "question": "销售额最高的前5个产品是什么?",
                "dataset_id": 1,
                "generate_explanation": True,
                "max_rows": 100
            }
        }


class DirectSQLRequest(BaseModel):
    """
    直接SQL查询请求
    高级用户可以直接执行SQL查询
    """
    sql: str = Field(..., description="SQL查询语句", min_length=1)
    dataset_id: int = Field(..., description="数据集ID", gt=0)
    max_rows: int = Field(default=100, description="最大返回行数", ge=1, le=1000)

    class Config:
        json_schema_extra = {
            "example": {
                "sql": "SELECT product, SUM(sales) as total_sales FROM data GROUP BY product ORDER BY total_sales DESC LIMIT 5",
                "dataset_id": 1,
                "max_rows": 100
            }
        }


class ChatHistoryRequest(BaseModel):
    """
    获取聊天历史请求
    """
    dataset_id: int = Field(..., description="数据集ID", gt=0)
    limit: int = Field(default=50, description="返回的最大消息数", ge=1, le=200)
    offset: int = Field(default=0, description="偏移量(用于分页)", ge=0)


# ========== Response Schemas ==========

class SQLExecutionResult(BaseModel):
    """
    SQL执行结果
    """
    success: bool = Field(..., description="执行是否成功")
    sql: str = Field(..., description="执行的SQL语句")
    data: Optional[List[Dict[str, Any]]] = Field(None, description="查询结果数据")
    columns: Optional[List[str]] = Field(None, description="列名列表")
    row_count: int = Field(default=0, description="返回的行数")
    execution_time: Optional[float] = Field(None, description="执行时间(秒)")
    error: Optional[str] = Field(None, description="错误信息")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "sql": "SELECT category, COUNT(*) as count FROM data GROUP BY category LIMIT 5",
                "data": [
                    {"category": "Electronics", "count": 150},
                    {"category": "Clothing", "count": 120}
                ],
                "columns": ["category", "count"],
                "row_count": 2,
                "execution_time": 0.023,
                "error": None
            }
        }


class ChatQueryResponse(BaseModel):
    """
    聊天查询响应
    """
    question: str = Field(..., description="用户的问题")
    sql_generated: str = Field(..., description="生成的SQL查询")
    execution_result: SQLExecutionResult = Field(..., description="SQL执行结果")
    explanation: Optional[str] = Field(None, description="自然语言解释")
    session_id: int = Field(..., description="聊天会话ID")
    dataset_id: int = Field(..., description="数据集ID")
    created_at: datetime = Field(..., description="创建时间")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "question": "销售额最高的前5个产品是什么?",
                "sql_generated": "SELECT product, SUM(sales) as total_sales FROM data GROUP BY product ORDER BY total_sales DESC LIMIT 5",
                "execution_result": {
                    "success": True,
                    "sql": "SELECT product, SUM(sales) as total_sales FROM data GROUP BY product ORDER BY total_sales DESC LIMIT 5",
                    "data": [
                        {"product": "iPhone", "total_sales": 50000},
                        {"product": "MacBook", "total_sales": 45000}
                    ],
                    "columns": ["product", "total_sales"],
                    "row_count": 2,
                    "execution_time": 0.015,
                    "error": None
                },
                "explanation": "根据查询结果,销售额最高的产品是iPhone,总销售额为50000元。",
                "session_id": 123,
                "dataset_id": 1,
                "created_at": "2024-01-15T10:30:00Z"
            }
        }


class ChatMessageSchema(BaseModel):
    """
    单条聊天消息
    """
    id: int = Field(..., description="消息ID")
    role: str = Field(..., description="角色: user | assistant | system")
    question: Optional[str] = Field(None, description="用户问题")
    answer: Optional[str] = Field(None, description="助手回答")
    context: Optional[Dict[str, Any]] = Field(None, description="上下文信息(SQL、执行结果等)")
    message_type: str = Field(default="text", description="消息类型: text | query | error")
    created_at: datetime = Field(..., description="创建时间")

    class Config:
        from_attributes = True


class ChatHistoryResponse(BaseModel):
    """
    聊天历史响应
    """
    dataset_id: int = Field(..., description="数据集ID")
    total_messages: int = Field(..., description="总消息数")
    messages: List[ChatMessageSchema] = Field(..., description="消息列表")

    class Config:
        json_schema_extra = {
            "example": {
                "dataset_id": 1,
                "total_messages": 10,
                "messages": [
                    {
                        "id": 1,
                        "role": "user",
                        "question": "有多少行数据?",
                        "answer": None,
                        "context": None,
                        "message_type": "query",
                        "created_at": "2024-01-15T10:00:00Z"
                    },
                    {
                        "id": 2,
                        "role": "assistant",
                        "question": None,
                        "answer": "数据集共有1000行数据。",
                        "context": {
                            "sql": "SELECT COUNT(*) as count FROM data",
                            "result": [{"count": 1000}]
                        },
                        "message_type": "query",
                        "created_at": "2024-01-15T10:00:05Z"
                    }
                ]
            }
        }


class DatasetSchemaResponse(BaseModel):
    """
    数据集Schema响应
    """
    dataset_id: int = Field(..., description="数据集ID")
    dataset_name: str = Field(..., description="数据集名称")
    row_count: int = Field(..., description="总行数")
    schema: List[Dict[str, Any]] = Field(..., description="Schema信息")
    numeric_columns: List[str] = Field(..., description="数值类型列")
    all_columns: List[str] = Field(..., description="所有列名")

    class Config:
        json_schema_extra = {
            "example": {
                "dataset_id": 1,
                "dataset_name": "销售数据",
                "row_count": 1000,
                "schema": [
                    {
                        "name": "product",
                        "dtype": "VARCHAR",
                        "non_null_count": 1000,
                        "unique_count": 50
                    },
                    {
                        "name": "sales",
                        "dtype": "DOUBLE",
                        "non_null_count": 1000,
                        "unique_count": 500,
                        "min": 100.0,
                        "max": 5000.0,
                        "mean": 1500.0
                    }
                ],
                "numeric_columns": ["sales", "quantity"],
                "all_columns": ["product", "sales", "quantity", "date"]
            }
        }


class ErrorResponse(BaseModel):
    """
    错误响应
    """
    error: str = Field(..., description="错误消息")
    detail: Optional[str] = Field(None, description="详细错误信息")
    error_type: str = Field(default="ValidationError", description="错误类型")

    class Config:
        json_schema_extra = {
            "example": {
                "error": "SQL执行失败",
                "detail": "Column 'invalid_column' does not exist",
                "error_type": "SQLExecutionError"
            }
        }
