
from enum import Enum
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid


class TaskType(str, Enum):

    pdf2image = "pdf2image"
    img2markdown = "img2markdown"
    full_pipeline = "full_pipeline"  # PDF -> Image -> Markdown


class TaskStatus(str, Enum):

    created = "created"
    running = "running"
    paused = "paused"
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"


class FileStatus(str, Enum):

    pending = "pending"
    processing = "processing"
    completed = "completed"
    failed = "failed"
    skipped = "skipped"


class FileRecord(BaseModel):

    file_path: str
    status: FileStatus = FileStatus.pending
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    error_message: Optional[str] = None
    output_path: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TaskInfo(BaseModel):

    task_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    task_type: TaskType
    status: TaskStatus = TaskStatus.created
    created_time: datetime = Field(default_factory=datetime.now)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    input_path: str
    output_path: str
    total_files: int = 0
    processed_files: int = 0
    failed_files: int = 0
    files: Dict[str, FileRecord] = Field(default_factory=dict)
    config: Dict[str, Any] = Field(default_factory=dict)
    error_message: Optional[str] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }