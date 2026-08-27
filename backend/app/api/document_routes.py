from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    UploadFile
)

from sqlalchemy.orm import Session

from app.core.config import settings

from app.database.dependencies import get_db

from app.schemas.document import (
    DocumentListResponse,
    DocumentResponse,
    DocumentUploadResponse
)

from app.services.document_repository import (
    DocumentRepository
)

from app.services.document_service import (
    DocumentService
)


router = APIRouter(
    prefix="/api/documents",
    tags=["Documents"]
)


def get_document_service(
    db: Session = Depends(get_db)
) -> DocumentService:

    repository = DocumentRepository(db)

    return DocumentService(
        upload_dir=settings.upload_dir,
        repository=repository,
        max_file_size=settings.max_file_size
    )


@router.post(
    "/upload",
    response_model=DocumentUploadResponse
)
async def upload_document(
    file: UploadFile = File(...),
    service: DocumentService = Depends(
        get_document_service
    )
):

    if not file.filename:

        raise HTTPException(
            status_code=400,
            detail="No file was provided."
        )

    try:

        document = (
            await service.save_document(file)
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
async def get_documents(
    service: DocumentService = Depends(
        get_document_service
    )
):

    documents = service.get_all_documents()

    return {
        "documents": documents,
        "total": len(documents)
    }


@router.get(
    "/{document_id}",
    response_model=DocumentResponse
)
async def get_document(
    document_id: str,
    service: DocumentService = Depends(
        get_document_service
    )
):

    document = service.get_document(
        document_id
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
    document_id: str,
    service: DocumentService = Depends(
        get_document_service
    )
):

    deleted = service.delete_document(
        document_id
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