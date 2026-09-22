from typing import Optional

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Body,
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

from app.ml.extraction.registry import (
    ExtractionStrategyRegistry
)

from app.services.extraction_service import (
    ExtractionService
)

from app.services.extraction_result_repository import (
    ExtractionResultRepository
)

from app.services.validation_service import (
    ValidationService
)

from app.services.validation_result_repository import (
    ValidationResultRepository
)

from app.schemas.validation import (
    ValidationResultResponse,
    RuleResultResponse,
)

from app.schemas.duplicate import (
    DuplicateCheckResponse,
    DuplicateMatchResponse,
)

from app.dedup.service import (
    DuplicateDetectionService,
)

from app.services.duplicate_result_repository import (
    DuplicateResultRepository,
)

from app.schemas.anomaly import (
    AnomalyCheckResponse,
    AnomalyTrainResponse,
)

from app.anomaly.service import (
    AnomalyDetectionService,
)

from app.services.anomaly_result_repository import (
    AnomalyResultRepository,
)

from app.schemas.extraction import (
    AIAnalysisResponse,
    AIConfigRequest,
    AIStatusResponse,
    DocumentAnalysisResponse,
    DocumentQARequest,
    DocumentQAResponse,
    ExtractionResultResponse,
    FieldResultResponse,
    LayoutLMAnalysisResponse,
    LayoutLMEntityResponse,
    LayoutLMPageResponse,
    MultiDocumentQARequest,
    SourceCitation,
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

from app.services.ai_analysis_service import (
    get_ai_service,
    get_runtime_api_key,
    set_runtime_api_key,
)

from app.rag.pipeline import get_rag_pipeline


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

    # --------------------------------
    # Extraction
    # --------------------------------

    extraction_registry = (
        ExtractionStrategyRegistry()
    )

    extraction_repository = (
        ExtractionResultRepository(db)
    )

    extraction_service = ExtractionService(
        registry=extraction_registry,
        repository=extraction_repository
    )

    # --------------------------------
    # Validation
    # --------------------------------

    validation_repository = (
        ValidationResultRepository(db)
    )

    validation_service = ValidationService(
        repository=validation_repository
    )

    # --------------------------------
    # Duplicate Detection
    # --------------------------------

    duplicate_repository = (
        DuplicateResultRepository(db)
    )

    duplicate_service = (
        DuplicateDetectionService(
            session=db
        )
    )

    # --------------------------------
    # Anomaly Detection
    # --------------------------------

    anomaly_repository = (
        AnomalyResultRepository(db)
    )

    anomaly_service = (
        AnomalyDetectionService(
            session=db,
            repository=anomaly_repository,
        )
    )

    ai_analysis_service = get_ai_service()

    return DocumentProcessingService(
        repository=repository,
        pipeline=pipeline,
        classification_service=(
            classification_service
        ),
        extraction_service=(
            extraction_service
        ),
        validation_service=(
            validation_service
        ),
        duplicate_service=(
            duplicate_service
        ),
        duplicate_repository=(
            duplicate_repository
        ),
        anomaly_service=(
            anomaly_service
        ),
        ai_analysis_service=(
            ai_analysis_service
        ),
    )

@router.post(
    "/upload",
    response_model=DocumentUploadResponse
)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    auto_process: bool = Query(default=False),
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

    if auto_process:
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
        le=500
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


# ==========================================
# AI Config (must be before /{document_id})
# ==========================================


@router.get(
    "/ai/status",
    response_model=AIStatusResponse,
)
async def get_ai_status():
    """Check if Groq AI is configured."""

    runtime_key = get_runtime_api_key()
    env_key = settings.groq_api_key

    if runtime_key:
        return AIStatusResponse(
            configured=True,
            model=settings.groq_model,
            source="runtime",
        )
    elif env_key:
        return AIStatusResponse(
            configured=True,
            model=settings.groq_model,
            source="environment",
        )
    else:
        return AIStatusResponse(
            configured=False,
            model=settings.groq_model,
            source="none",
        )


@router.post(
    "/ai/config",
    response_model=AIStatusResponse,
)
async def update_ai_config(
    body: AIConfigRequest,
):
    """Save or update Groq API key at runtime."""

    set_runtime_api_key(body.api_key)

    return AIStatusResponse(
        configured=True,
        model=settings.groq_model,
        source="runtime",
    )

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


@router.post(
    "/{document_id}/process",
    response_model=DocumentResponse
)
async def process_document_endpoint(
    document_id: str,
    background_tasks: BackgroundTasks,
    service: DocumentService = Depends(
        get_document_service
    ),
    processing_service: DocumentProcessingService = Depends(
        get_processing_service
    ),
):
    """Trigger processing and analysis for an uploaded document."""
    document = service.get_document(
        document_id
    )

    if not document:
        raise HTTPException(
            status_code=404,
            detail="Document not found"
        )

    background_tasks.add_task(
        processing_service.process_document,
        document_id
    )

    return document


@router.get(
    "/{document_id}/content",
    response_model=DocumentContentResponse
)
async def get_document_content(
    document_id: str,
    db: Session = Depends(get_db),
    service: DocumentService = Depends(
        get_document_service
    )
):
    """Get extracted text and content for a document."""

    document = service.get_document(
        document_id
    )

    if not document:
        raise HTTPException(
            status_code=404,
            detail="Document not found"
        )

    content_repo = DocumentContentRepository(db)
    content = content_repo.get_by_document_id(document_id)

    if not content:
        raise HTTPException(
            status_code=404,
            detail="Document content not found"
        )

    return content


@router.get(
    "/{document_id}/analysis",
    response_model=DocumentAnalysisResponse
)
async def get_document_analysis(
    document_id: str,
    db: Session = Depends(get_db),
    service: DocumentService = Depends(
        get_document_service
    )
):
    """Get combined analysis for a document.

    Returns document metadata, classification
    results, and extracted fields.
    """

    document = service.get_document(
        document_id
    )

    if not document:

        raise HTTPException(
            status_code=404,
            detail="Document not found"
        )

    # Build extraction response
    extraction_repo = (
        ExtractionResultRepository(db)
    )

    extraction_record = (
        extraction_repo.get_by_document_id(
            document_id
        )
    )

    extraction_response = None

    if extraction_record:

        # Convert stored JSON fields to response
        fields_response = {}

        for name, fd in (
            extraction_record.extracted_fields
            or {}
        ).items():

            fields_response[name] = (
                FieldResultResponse(
                    value=fd.get("value"),
                    confidence=fd.get(
                        "confidence", 0.0
                    ),
                    source=fd.get(
                        "source", "none"
                    ),
                    bbox=fd.get("bbox"),
                )
            )

        extraction_response = (
            ExtractionResultResponse(
                document_type=(
                    extraction_record.document_type
                ),
                fields=fields_response,
                extraction_method=(
                    extraction_record
                    .extraction_method
                ),
                extraction_version=(
                    extraction_record
                    .extraction_version
                ),
                extracted_at=(
                    extraction_record.extracted_at
                ),
            )
        )

    # Validation results
    val_repo = ValidationResultRepository(db)
    val_record = (
        val_repo.get_by_document_id(document_id)
    )
    val_status = (
        val_record.status if val_record else None
    )
    val_error_count = (
        sum(
            1 for r in (val_record.rule_results or [])
            if r.get("status") == "FAIL"
        )
        if val_record and val_record.rule_results
        else None
    )

    # Duplicate results
    dup_repo = DuplicateResultRepository(db)
    dup_matches = (
        dup_repo.get_by_document_id(document_id)
    )
    has_dupes = (
        len(dup_matches) > 0 if dup_matches else False
    )
    dup_count = (
        len(dup_matches) if dup_matches else 0
    )

    # Anomaly results
    anomaly_repo = AnomalyResultRepository(db)
    anomaly_rec = (
        anomaly_repo.get_by_document_id(document_id)
    )
    is_anom = (
        anomaly_rec.is_anomaly if anomaly_rec else None
    )
    anom_score = (
        round(anomaly_rec.anomaly_score, 4)
        if anomaly_rec
        else None
    )

    # AI Semantic Analysis
    repo = DocumentRepository(db)
    ai_analysis = repo.get_ai_analysis(document_id)

    return DocumentAnalysisResponse(
        document_id=document.document_id,
        filename=document.filename,
        file_type=document.file_type,
        file_size=document.file_size,
        status=document.status,
        created_at=document.created_at,
        updated_at=document.updated_at,
        document_type=document.document_type,
        classification_confidence=(
            document.classification_confidence
        ),
        classified_at=document.classified_at,
        extraction=extraction_response,
        validation_status=val_status,
        validation_error_count=val_error_count,
        has_duplicates=has_dupes,
        duplicate_count=dup_count,
        is_anomaly=is_anom,
        anomaly_score=anom_score,
        ai_analysis=ai_analysis,
    )


@router.get(
    "/{document_id}/layoutlm",
    response_model=LayoutLMAnalysisResponse
)
async def get_layoutlm_analysis(
    document_id: str,
    db: Session = Depends(get_db),
    service: DocumentService = Depends(
        get_document_service
    )
):
    """Run LayoutLMv3 analysis on a document.

    Returns entity predictions from the
    multimodal model. Requires LayoutLMv3
    to be enabled and dependencies installed.
    """

    # Check feature flag
    if not settings.layoutlm_enabled:

        raise HTTPException(
            status_code=503,
            detail=(
                "LayoutLMv3 is not enabled. "
                "Set LAYOUTLM_ENABLED=true "
                "in .env and install: "
                "pip install -r "
                "requirements-layoutlm.txt"
            )
        )

    # Verify document exists
    document = service.get_document(
        document_id
    )

    if not document:

        raise HTTPException(
            status_code=404,
            detail="Document not found"
        )

    # Lazy import to avoid ImportError when
    # torch/transformers are not installed
    try:

        from app.ml.layoutlm.config import (
            LayoutLMConfig,
        )
        from app.ml.layoutlm.model_manager import (
            LayoutLMModelManager,
        )
        from app.ml.layoutlm.service import (
            LayoutLMService,
        )
        from app.services.document_page_repository import (
            DocumentPageRepository,
        )

    except ImportError:

        raise HTTPException(
            status_code=503,
            detail=(
                "LayoutLMv3 dependencies not "
                "installed. Run: pip install "
                "-r requirements-layoutlm.txt"
            )
        )

    # Initialize model manager
    config = LayoutLMConfig(
        device=settings.layoutlm_device,
    )

    manager = LayoutLMModelManager(config)

    model_source = (
        settings.layoutlm_model_dir
        or None
    )

    if not manager.load(model_source):

        raise HTTPException(
            status_code=503,
            detail=(
                "Failed to load LayoutLMv3 "
                "model. Check logs."
            )
        )

    # Run analysis
    page_repo = DocumentPageRepository(db)

    layoutlm_service = LayoutLMService(
        model_manager=manager,
        page_repository=page_repo,
    )

    result = layoutlm_service.analyze_document(
        document_id
    )

    if result is None:

        return LayoutLMAnalysisResponse(
            document_id=document_id,
            model_name=config.model_name,
            status="skipped",
            message="Model not loaded.",
        )

    # Build response
    pages_response = []

    for page_pred in result.pages:

        entities_response = [
            LayoutLMEntityResponse(
                label=e.label,
                text=e.text,
                confidence=e.confidence,
                bbox=e.bbox,
            )
            for e in page_pred.entities
        ]

        pages_response.append(
            LayoutLMPageResponse(
                page_number=(
                    page_pred.page_number
                ),
                entities=entities_response,
            )
        )

    return LayoutLMAnalysisResponse(
        document_id=document_id,
        model_name=result.model_name,
        is_finetuned=result.is_finetuned,
        pages=pages_response,
        status="completed",
        message=(
            "Pretrained model — predictions "
            "are generic. Fine-tune for "
            "production accuracy."
            if not result.is_finetuned
            else "Fine-tuned model."
        ),
    )


@router.get(
    "/{document_id}/validation",
    response_model=ValidationResultResponse
)
async def get_validation_result(
    document_id: str,
    db: Session = Depends(get_db),
    service: DocumentService = Depends(
        get_document_service
    )
):
    """Get validation result for a document.

    Returns stored validation results. If none
    exist yet, runs validation on-demand using
    the stored extraction results.
    """

    document = service.get_document(
        document_id
    )

    if not document:

        raise HTTPException(
            status_code=404,
            detail="Document not found"
        )

    validation_repo = (
        ValidationResultRepository(db)
    )

    # Check for stored result
    stored = (
        validation_repo.get_by_document_id(
            document_id
        )
    )

    if stored:

        rule_results = [
            RuleResultResponse(**r)
            for r in (stored.rule_results or [])
        ]

        error_count = sum(
            1 for r in rule_results
            if r.status == "FAIL"
        )

        warning_count = sum(
            1 for r in rule_results
            if r.status == "WARN"
        )

        return ValidationResultResponse(
            document_id=document_id,
            document_type=stored.document_type,
            status=stored.status,
            results=rule_results,
            validated_at=stored.validated_at,
            error_count=error_count,
            warning_count=warning_count,
        )

    # No stored result — run on-demand
    extraction_repo = (
        ExtractionResultRepository(db)
    )

    extraction_record = (
        extraction_repo.get_by_document_id(
            document_id
        )
    )

    if not extraction_record:

        raise HTTPException(
            status_code=404,
            detail=(
                "No extraction results found. "
                "Process the document first."
            )
        )

    validation_service = ValidationService(
        repository=validation_repo
    )

    result = (
        validation_service.validate_document(
            document_id=document_id,
            document_type=(
                extraction_record.document_type
            ),
            extracted_fields=(
                extraction_record.extracted_fields
            ),
        )
    )

    if result is None:

        return ValidationResultResponse(
            document_id=document_id,
            document_type=(
                extraction_record.document_type
            ),
            status="SKIPPED",
            results=[],
            error_count=0,
            warning_count=0,
        )

    rule_results = [
        RuleResultResponse(
            **r.to_dict()
        )
        for r in result.results
    ]

    return ValidationResultResponse(
        document_id=document_id,
        document_type=result.document_type,
        status=result.status.value,
        results=rule_results,
        validated_at=result.validated_at,
        error_count=len(result.errors),
        warning_count=len(result.warnings),
    )


@router.get(
    "/{document_id}/duplicates",
    response_model=DuplicateCheckResponse
)
async def check_duplicates(
    document_id: str,
    db: Session = Depends(get_db),
    service: DocumentService = Depends(
        get_document_service
    ),
    near_threshold: float = 0.85,
    exact_threshold: float = 0.99,
):
    """Check a document for duplicates.

    Runs TF-IDF cosine similarity against other
    documents of the same type. Returns exact
    and near duplicate matches.

    Query params:
        near_threshold: Min similarity for near
            duplicate (default: 0.85).
        exact_threshold: Min similarity for
            exact duplicate (default: 0.99).
    """

    document = service.get_document(
        document_id
    )

    if not document:

        raise HTTPException(
            status_code=404,
            detail="Document not found"
        )

    dedup_service = DuplicateDetectionService(
        session=db,
        exact_threshold=exact_threshold,
        near_threshold=near_threshold,
    )

    result = dedup_service.check_document(
        document_id
    )

    # Persist results
    if result.matches:

        repo = DuplicateResultRepository(db)

        repo.save_matches([
            m.to_dict() for m in result.matches
        ])

    # Build response
    matches_response = [
        DuplicateMatchResponse(
            matched_document_id=(
                m.matched_document_id
            ),
            similarity_score=round(
                m.similarity_score, 4
            ),
            duplicate_type=(
                m.duplicate_type.value
            ),
        )
        for m in result.matches
    ]

    return DuplicateCheckResponse(
        document_id=document_id,
        has_duplicates=result.has_duplicates,
        exact_count=len(result.exact_matches),
        near_count=len(result.near_matches),
        candidates_checked=(
            result.candidates_checked
        ),
        matches=matches_response,
    )


@router.get(
    "/{document_id}/anomaly",
    response_model=AnomalyCheckResponse
)
async def get_document_anomaly(
    document_id: str,
    db: Session = Depends(get_db),
    service: DocumentService = Depends(
        get_document_service
    ),
):
    """Check a document for structural or numerical anomalies.

    Evaluates document features using an Isolation Forest model.
    Flags mathematical outliers and unusual patterns without
    asserting fraud.
    """

    document = service.get_document(
        document_id
    )

    if not document:

        raise HTTPException(
            status_code=404,
            detail="Document not found"
        )

    anomaly_repo = AnomalyResultRepository(db)
    anomaly_service = AnomalyDetectionService(
        session=db,
        repository=anomaly_repo,
    )

    # Return stored evaluation if exists
    stored = anomaly_repo.get_by_document_id(
        document_id
    )

    if stored:

        return AnomalyCheckResponse(
            document_id=stored.document_id,
            is_anomaly=stored.is_anomaly,
            anomaly_score=round(
                stored.anomaly_score, 4
            ),
            decision_function_score=round(
                stored.decision_function_score, 4
            ),
            features=stored.features or {},
            model_version=stored.model_version,
            detected_at=stored.detected_at,
        )

    # Evaluate and persist on-demand
    result = anomaly_service.check_document(
        document_id=document_id,
        persist=True,
    )

    return AnomalyCheckResponse(
        document_id=result.document_id,
        is_anomaly=result.is_anomaly,
        anomaly_score=round(
            result.anomaly_score, 4
        ),
        decision_function_score=round(
            result.decision_function_score, 4
        ),
        features=result.features,
        model_version=result.model_version,
        detected_at=result.detected_at,
    )


@router.post(
    "/anomaly/train",
    response_model=AnomalyTrainResponse
)
async def train_anomaly_model(
    db: Session = Depends(get_db),
    contamination: Optional[float] = None,
    min_samples: Optional[int] = None,
):
    """Train or retrain Isolation Forest model on historical documents.

    Collects feature vectors from all completed documents in the database
    and fits an Isolation Forest model.
    """

    anomaly_service = AnomalyDetectionService(
        session=db
    )

    result = anomaly_service.train_on_historical_documents(
        min_samples=min_samples,
        contamination=contamination,
    )

    return AnomalyTrainResponse(**result)


# ==========================================
# AI Semantic Analysis Endpoints
# ==========================================


@router.post(
    "/qa",
    response_model=DocumentQAResponse,
)
async def ask_multi_document_question(
    body: MultiDocumentQARequest,
):
    """Ask a question across multiple documents or repository-wide using RAG."""
    rag_pipeline = get_rag_pipeline()
    result = rag_pipeline.query_documents(
        question=body.question,
        document_ids=body.document_ids,
    )
    return DocumentQAResponse(**result)


@router.post(
    "/{document_id}/qa",
    response_model=DocumentQAResponse,
)
async def ask_document_question(
    document_id: str,
    body: DocumentQARequest,
    db: Session = Depends(get_db),
    service: DocumentService = Depends(
        get_document_service
    ),
):
    """Ask a question about a specific document using RAG.

    Retrieves page-aware chunks from the vector store with
    metadata filtering, constructs a grounded context, and
    generates an answer with page source citations.
    """

    document = service.get_document(
        document_id
    )

    if not document:
        raise HTTPException(
            status_code=404,
            detail="Document not found"
        )

    rag_pipeline = get_rag_pipeline()

    # If document not yet indexed in vector store, auto-index it now
    existing = rag_pipeline.vector_store.get_by_document_id(document_id)
    if not existing:
        page_repo = DocumentPageRepository(db)
        pages = page_repo.get_by_document_id(document_id)

        content_repo = DocumentContentRepository(db)
        content = content_repo.get_by_document_id(document_id)
        fallback_text = content.cleaned_text if content else ""

        ext_repo = ExtractionResultRepository(db)
        ext_res = ext_repo.get_by_document_id(document_id)
        ext_data = ext_res.fields if ext_res and hasattr(ext_res, "fields") else None

        rag_pipeline.index_document(
            document_id=document_id,
            document_type=document.document_type or "unknown",
            filename=document.filename or "",
            pages=pages,
            fallback_text=fallback_text,
            extraction_data=ext_data,
        )

    result = rag_pipeline.query_document(
        document_id=document_id,
        question=body.question,
        document_type=document.document_type,
    )

    return DocumentQAResponse(**result)


@router.post(
    "/{document_id}/reindex",
)
async def reindex_document_rag(
    document_id: str,
    db: Session = Depends(get_db),
    service: DocumentService = Depends(
        get_document_service
    ),
):
    """Re-index a document's pages and extraction results into RAG vector store."""
    document = service.get_document(document_id)
    if not document:
        raise HTTPException(
            status_code=404,
            detail="Document not found"
        )

    rag_pipeline = get_rag_pipeline()
    page_repo = DocumentPageRepository(db)
    pages = page_repo.get_by_document_id(document_id)

    content_repo = DocumentContentRepository(db)
    content = content_repo.get_by_document_id(document_id)
    fallback_text = content.cleaned_text if content else ""

    ext_repo = ExtractionResultRepository(db)
    ext_res = ext_repo.get_by_document_id(document_id)
    ext_data = ext_res.fields if ext_res and hasattr(ext_res, "fields") else None

    count = rag_pipeline.index_document(
        document_id=document_id,
        document_type=document.document_type or "unknown",
        filename=document.filename or "",
        pages=pages,
        fallback_text=fallback_text,
        extraction_data=ext_data,
    )

    return {
        "document_id": document_id,
        "filename": document.filename,
        "indexed_chunks": count,
    }


@router.post(
    "/{document_id}/reanalyze",
    response_model=AIAnalysisResponse,
)
async def reanalyze_document(
    document_id: str,
    api_key: Optional[str] = Body(
        None, embed=True
    ),
    db: Session = Depends(get_db),
    service: DocumentService = Depends(
        get_document_service
    ),
):
    """Re-run AI analysis on a document.

    Optionally accepts an API key for one-time use.
    """

    document = service.get_document(
        document_id
    )

    if not document:
        raise HTTPException(
            status_code=404,
            detail="Document not found"
        )

    content_repo = DocumentContentRepository(db)
    content = content_repo.get_by_document_id(
        document_id
    )

    if not content or not content.cleaned_text:
        raise HTTPException(
            status_code=404,
            detail=(
                "Document content not found. "
                "Process the document first."
            )
        )

    ai_service = get_ai_service(api_key=api_key)
    result = ai_service.analyze_document(
        document_text=content.cleaned_text,
        document_type=document.document_type,
        filename=document.filename,
    )

    # Store updated analysis
    repo = DocumentRepository(db)
    repo.store_ai_analysis(
        document_id=document_id,
        ai_analysis=result,
    )

    return AIAnalysisResponse(**result)