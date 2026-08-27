from datetime import datetime

from pydantic import BaseModel

from app.models.document import DocumentStatus


class DocumentUploadResponse(BaseModel):

    message: str
    document_id: str
    filename: str
    file_type: str
    file_size: int
    status: DocumentStatus


class DocumentResponse(BaseModel):

    document_id: str
    filename: str
    file_type: str
    file_size: int
    status: DocumentStatus
    created_at: datetime


class DocumentListResponse(BaseModel):

    documents: list[DocumentResponse]
    total: int