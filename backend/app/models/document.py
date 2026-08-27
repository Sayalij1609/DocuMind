from dataclasses import dataclass
from enum import Enum
from datetime import datetime


class DocumentStatus(str, Enum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class Document:

    document_id: str
    filename: str
    file_type: str
    file_size: int
    file_path: str
    status: DocumentStatus
    created_at: datetime