from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    HTTPException,
    Query,
    UploadFile
)
from app.services.document_page_repository import (
    DocumentPageRepository
)

from app.processing.page_storage import (
    PageStorageService
)

from sqlalchemy.orm import Session

from app.core.config import settings

from app.database.dependencies import get_db

from app.schemas.document import (
    DocumentListResponse,
    DocumentResponse,
    DocumentUploadResponse
)

from app.schemas.document_content import (
    DocumentContentResponse
)

from app.services.document_repository import (
    DocumentRepository
)

from app.services.document_service import (
    DocumentService
)

from app.services.document_content_repository import (
    DocumentContentRepository
)

from app.services.document_processing_service import (
    DocumentProcessingService
)

from app.services.classification_service import (
    ClassificationService
)

from app.ml.classification.predictor import (
    DocumentClassifier
)

from app.processing.document_extractor import (
    DocumentExtractor
)

from app.processing.text_cleaner import (
    TextCleaner
)

from app.processing.pipeline import (
    DocumentProcessingPipeline
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


def get_processing_service(
    db: Session = Depends(get_db)
) -> DocumentProcessingService:

    content_repository = (
        DocumentContentRepository(
            db
        )
    )

    page_repository = (
        DocumentPageRepository(
            db
        )
    )

    extractor = DocumentExtractor(
        tesseract_cmd=settings.tesseract_cmd
    )

    cleaner = TextCleaner()

    page_storage = PageStorageService(
        storage_dir="storage/pages"
    )

    pipeline = DocumentProcessingPipeline(
        extractor=extractor,
        cleaner=cleaner,
        content_repository=content_repository,
        page_repository=page_repository,
        page_storage=page_storage
    )

    repository = DocumentRepository(
        db
    )

    # --------------------------------
    # Classification
    # --------------------------------

    classifier = DocumentClassifier(
        confidence_threshold=(
            settings
            .classification_confidence_threshold
        )
    )

    classifier.load(
        settings.classification_model_dir
    )

    classification_service = (
        ClassificationService(
            classifier=classifier,
            repository=repository
        )
    )

    return DocumentProcessingService(
        repository=repository,
        pipeline=pipeline,
        classification_service=(
            classification_service
        )
    )

@router.post(
    "/upload",
    response_model=DocumentUploadResponse
)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    service: DocumentService = Depends(
        get_document_service
    ),
    processing_service: DocumentProcessingService = Depends(
        get_processing_service
    )
):

    if not file.filename:

        raise HTTPException(
            status_code=400,
            detail="No file was provided."
        )

    try:

        document = await service.save_document(
            file
        )

    except ValueError as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc)
        )

    background_tasks.add_task(
        processing_service.process_document,
        document.document_id
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
    page: int = Query(
        default=1,
        ge=1
    ),
    page_size: int = Query(
        default=20,
        ge=1,
        le=100
    ),
    service: DocumentService = Depends(
        get_document_service
    )
):

    skip = (
        page - 1
    ) * page_size

    documents, total = (
        service.get_all_documents(
            skip=skip,
            limit=page_size
        )
    )

    return {
        "documents": documents,
        "total": total,
        "page": page,
        "page_size": page_size
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