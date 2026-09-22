from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DocumentResponse(BaseModel):

    document_id: str

    filename: str

    file_type: str

    file_size: int

    file_path: str

    status: str

    created_at: datetime

    updated_at: datetime

    document_type: str | None = None

    classification_confidence: float | None = None

    classified_at: datetime | None = None

    model_config = ConfigDict(
        from_attributes=True
    )


class DocumentUploadResponse(BaseModel):

    message: str

    document_id: str

    filename: str

    file_type: str

    file_size: int

    status: str


class DocumentListResponse(BaseModel):

    documents: list[DocumentResponse]

    total: int

    page: int

    page_size: int


class BatchItemStatusResponse(BaseModel):
    document_id: str
    filename: str
    status: str
    error: str | None = None
    started_at: str | None = None
    completed_at: str | None = None


class BatchUploadResponse(BaseModel):
    message: str
    batch_id: str
    total: int
    document_ids: list[str]


class BatchStatusResponse(BaseModel):
    batch_id: str
    status: str
    total: int
    pending: int
    processing: int
    completed: int
    failed: int
    progress_percent: float
    created_at: str
    items: list[BatchItemStatusResponse]