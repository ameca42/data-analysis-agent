from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime


class DatasetBase(BaseModel):
    name: str
    description: Optional[str] = None


class DatasetCreate(DatasetBase):
    pass


class DatasetResponse(DatasetBase):
    id: int
    file_path: str
    original_filename: str
    file_size: int
    file_type: str
    schema_json: Optional[List[Dict[str, Any]]] = None
    row_count: int
    tags: Optional[List[str]] = None
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class AnalysisBase(BaseModel):
    analysis_type: str
    title: Optional[str] = None
    description: Optional[str] = None
    input_params: Optional[Dict[str, Any]] = None


class AnalysisCreate(AnalysisBase):
    dataset_id: int


class AnalysisResponse(AnalysisBase):
    id: int
    dataset_id: int
    result_json: Optional[Dict[str, Any]] = None
    status: str
    execution_time: Optional[float] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ChatMessage(BaseModel):
    role: str
    content: str
    analysis_id: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True
