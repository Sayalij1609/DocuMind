from fastapi import (
    APIRouter,
    UploadFile,
    File,
    HTTPException
)

from app.core.config import settings

from app.schemas.document import (
    DocumentUploadResponse,
    DocumentResponse,
    DocumentListResponse
)

from app.services.document_service import (
    DocumentService
)

from app.services.document_repository import (
    DocumentRepository
)


router = APIRouter(
    prefix="/api/documents",
    tags=["Documents"]
)


repository = DocumentRepository()

document_service = DocumentService(
    upload_dir=settings.upload_dir,
    repository=repository,
    max_file_size=settings.max_file_size
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

        document = (
            await document_service.save_document(
                file
            )
        )

    except ValueError as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc)
        )

    return {
        "message": "Document uploaded successfully",
        "document_id": document.document_id,
        "filename": document.filename,
        "file_type": document.file_type,
        "file_size": document.file_size,
        "status": document.status
    }


@router.get(
    "",
    response_model=DocumentListResponse
)
async def get_documents():

    documents = (
        document_service.get_all_documents()
    )

    return {
        "documents": documents,
        "total": len(documents)
    }


@router.get(
    "/{document_id}",
    response_model=DocumentResponse
)
async def get_document(
    document_id: str
):

    document = (
        document_service.get_document(
            document_id
        )
    )

    if not document:

        raise HTTPException(
            status_code=404,
            detail="Document not found"
        )

    return document


@router.delete(
    "/{document_id}"
)
async def delete_document(
    document_id: str
):

    deleted = (
        document_service.delete_document(
            document_id
        )
    )

    if not deleted:

        raise HTTPException(
            status_code=404,
            detail="Document not found"
        )

    return {
        "message": "Document deleted successfully",
        "document_id": document_id
    }