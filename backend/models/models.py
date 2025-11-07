from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON, Boolean, Float
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from backend.database import Base


class Dataset(Base):
    """数据集表"""
    __tablename__ = "datasets"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)

    file_path = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_size = Column(Integer, nullable=False)
    file_type = Column(String(50), nullable=False)

    schema_json = Column(JSON, nullable=True)
    row_count = Column(Integer, default=0)

    tags = Column(JSON, nullable=True)
    status = Column(String(20), default="active")

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    analyses = relationship("Analysis", back_populates="dataset", cascade="all, delete-orphan")
    chat_sessions = relationship("ChatSession", back_populates="dataset", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Dataset(id={self.id}, name={self.name})>"


class Analysis(Base):
    """分析任务表"""
    __tablename__ = "analyses"

    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(Integer, ForeignKey("datasets.id"), nullable=False)

    analysis_type = Column(String(50), nullable=False)
    title = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)

    input_params = Column(JSON, nullable=True)
    result_json = Column(JSON, nullable=True)

    code_generated = Column(Text, nullable=True)
    execution_time = Column(Float, nullable=True)
    status = Column(String(20), default="pending")
    error_message = Column(Text, nullable=True)

    is_cached = Column(Boolean, default=False)
    access_count = Column(Integer, default=0)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    dataset = relationship("Dataset", back_populates="analyses")
    chat_sessions = relationship("ChatSession", back_populates="analysis")

    def __repr__(self):
        return f"<Analysis(id={self.id}, type={self.analysis_type})>"


class ChatSession(Base):
    """对话会话表"""
    __tablename__ = "chat_sessions"

    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(Integer, ForeignKey("datasets.id"), nullable=False)
    analysis_id = Column(Integer, ForeignKey("analyses.id"), nullable=True)

    role = Column(String(20), nullable=False)
    question = Column(Text, nullable=True)
    answer = Column(Text, nullable=True)

    context = Column(JSON, nullable=True)
    message_type = Column(String(50), default="text")
    tokens_used = Column(Integer, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    dataset = relationship("Dataset", back_populates="chat_sessions")
    analysis = relationship("Analysis", back_populates="chat_sessions")

    def __repr__(self):
        return f"<ChatSession(id={self.id}, role={self.role})>"
