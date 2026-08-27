# Document API routes
from fastapi import APIRouter, UploadFile, File, HTTPException

from app.core.config import settings
from app.schemas.document import DocumentUploadResponse
from app.services.document_service import DocumentService


router = APIRouter(
    prefix="/api/documents",
    tags=["Documents"]
)


document_service = DocumentService(
    upload_dir=settings.upload_dir
)


@router.post(
    "/upload",
    response_model=DocumentUploadResponse
)
async def upload_document(
    file: UploadFile = File(...)
):

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="No file was provided."
        )

    try:
        result = await document_service.save_document(file)

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc)
        )

    return {
        "message": "Document uploaded successfully",
        "document_id": result["document_id"],
        "filename": result["filename"],
        "file_type": result["file_type"],
        "file_size": result["file_size"],
        "status": "uploaded"
    }