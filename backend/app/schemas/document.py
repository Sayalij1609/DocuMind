# Document schemas
from pydantic import BaseModel
class DocumentUploadResponse(BaseModel):
    message: str
    document_id: str
    filename: str
    file_type: str
    file_size: int
    status: str

    