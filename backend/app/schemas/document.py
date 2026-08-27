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