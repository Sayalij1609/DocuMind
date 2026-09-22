import logging
from typing import Any, Optional

from app.models.document import DocumentStatus

from app.processing.pipeline import (
    DocumentProcessingPipeline
)

from app.services.classification_service import (
    ClassificationService
)

from app.services.extraction_service import (
    ExtractionService
)

from app.services.validation_service import (
    ValidationService
)

from app.dedup.service import (
    DuplicateDetectionService
)

from app.anomaly.service import (
    AnomalyDetectionService
)

from app.services.duplicate_result_repository import (
    DuplicateResultRepository
)

from app.services.document_repository import (
    DocumentRepository
)

from app.services.ai_analysis_service import (
    AIAnalysisService,
    get_ai_service,
)

from app.services.ocr_correction_service import (
    OCRCorrectionService,
    get_ocr_correction_service,
)


logger = logging.getLogger(__name__)


class DocumentProcessingService:

    def __init__(
        self,
        repository: DocumentRepository,
        pipeline: DocumentProcessingPipeline,
        classification_service: Optional[
            ClassificationService
        ] = None,
        extraction_service: Optional[
            ExtractionService
        ] = None,
        validation_service: Optional[
            ValidationService
        ] = None,
        duplicate_service: Optional[
            DuplicateDetectionService
        ] = None,
        duplicate_repository: Optional[
            DuplicateResultRepository
        ] = None,
        anomaly_service: Optional[
            AnomalyDetectionService
        ] = None,
        ai_analysis_service: Optional[
            AIAnalysisService
        ] = None,
        ocr_correction_service: Optional[
            OCRCorrectionService
        ] = None,
    ):

        self.repository = repository

        self.pipeline = pipeline

        self.classification_service = (
            classification_service
        )

        self.extraction_service = (
            extraction_service
        )

        self.validation_service = (
            validation_service
        )

        self.duplicate_service = (
            duplicate_service
        )

        self.duplicate_repository = (
            duplicate_repository
        )

        self.anomaly_service = (
            anomaly_service
        )

        self.ai_analysis_service = (
            ai_analysis_service
            or get_ai_service()
        )

        self.ocr_correction_service = (
            ocr_correction_service
            or get_ocr_correction_service()
        )

    def process_document(
        self,
        document_id: str
    ):

        logger.info(
            "Starting document processing: %s",
            document_id
        )

        document = (
            self.repository.get_by_id(
                document_id
            )
        )

        if not document:

            logger.warning(
                "Document not found: %s",
                document_id
            )

            return

        self.repository.update_status(
            document_id,
            DocumentStatus.PROCESSING
        )

        try:

            content = self.pipeline.process(
                document
            )

            # --------------------------------
            # OCR Post-Processing Correction
            # --------------------------------

            cleaned_text = content.cleaned_text or ""
            corrected_text = self._correct_ocr(
                cleaned_text
            )

            # --------------------------------
            # Classification (non-blocking)
            # --------------------------------

            classification_result = (
                self._classify_document(
                    document_id,
                    corrected_text
                )
            )

            # --------------------------------
            # Extraction (non-blocking)
            # --------------------------------

            extraction_result = None

            if classification_result:
                extraction_result = (
                    self._extract_document(
                        document_id,
                        classification_result.document_type,
                        corrected_text
                    )
                )

            # --------------------------------
            # Validation (non-blocking)
            # --------------------------------

            if (
                classification_result
                and extraction_result
            ):
                self._validate_document(
                    document_id,
                    classification_result.document_type,
                    extraction_result
                )

            self.repository.update_status(
                document_id,
                DocumentStatus.COMPLETED
            )

            # --------------------------------
            # Duplicate Detection (non-blocking)
            # --------------------------------

            self._detect_duplicates(document_id)

            # --------------------------------
            # Anomaly Detection (non-blocking)
            # --------------------------------

            self._detect_anomalies(document_id)

            # --------------------------------
            # AI Semantic Analysis (non-blocking)
            # --------------------------------

            self._run_ai_analysis(
                document_id,
                corrected_text,
                (
                    classification_result.document_type
                    if classification_result
                    else None
                ),
                document.filename,
            )

            # --------------------------------
            # RAG Vector Store Indexing (non-blocking)
            # --------------------------------

            self._index_for_rag(
                document_id,
                (
                    classification_result.document_type
                    if classification_result
                    else "unknown"
                ),
                document.filename or "",
                corrected_text or "",
                extraction_result,
            )

            logger.info(
                "Document processing completed: %s",
                document_id
            )

        except Exception:

            self.repository.update_status(
                document_id,
                DocumentStatus.FAILED
            )

            logger.exception(
                "Document processing failed: %s",
                document_id
            )

    def _classify_document(
        self,
        document_id: str,
        cleaned_text: str
    ):
        """
        Run classification on extracted text.

        This is non-blocking: if classification
        fails, the document processing still
        completes successfully.

        Returns:
            ClassificationResult or None.
        """

        if self.classification_service is None:

            logger.debug(
                "No classification service "
                "configured, skipping."
            )

            return None

        try:

            result = (
                self.classification_service
                .classify_document(
                    document_id=document_id,
                    document_text=cleaned_text
                )
            )

            logger.info(
                "Document %s classified: "
                "%s (%.4f)",
                document_id,
                result.document_type,
                result.confidence
            )

            return result

        except Exception:

            logger.exception(
                "Classification failed for "
                "document %s (non-blocking)",
                document_id
            )

            return None

    def _extract_document(
        self,
        document_id: str,
        document_type: str,
        cleaned_text: str
    ):
        """
        Run information extraction on text.

        This is non-blocking: if extraction fails,
        document processing still completes.

        Returns:
            ExtractionResult or None.
        """

        if self.extraction_service is None:

            logger.debug(
                "No extraction service "
                "configured, skipping."
            )

            return None

        try:

            result = (
                self.extraction_service
                .extract_document(
                    document_id=document_id,
                    document_type=document_type,
                    cleaned_text=cleaned_text
                )
            )

            if result:

                logger.info(
                    "Document %s extraction "
                    "completed: %d fields",
                    document_id,
                    len(result.fields)
                )

            return result

        except Exception:

            logger.exception(
                "Extraction failed for "
                "document %s (non-blocking)",
                document_id
            )

            return None

    def _validate_document(
        self,
        document_id: str,
        document_type: str,
        extraction_result
    ):
        """
        Run validation on extracted fields.

        This is non-blocking: if validation fails,
        document processing still completes.
        """

        if self.validation_service is None:

            logger.debug(
                "No validation service "
                "configured, skipping."
            )

            return

        try:

            # Convert ExtractionResult to the
            # field dict format expected by rules
            extracted_fields = (
                extraction_result.to_dict()
                .get("fields", {})
            )

            result = (
                self.validation_service
                .validate_document(
                    document_id=document_id,
                    document_type=document_type,
                    extracted_fields=(
                        extracted_fields
                    )
                )
            )

            if result:

                logger.info(
                    "Document %s validation: "
                    "%s (%d rules, %d errors)",
                    document_id,
                    result.status.value,
                    len(result.results),
                    len(result.errors)
                )

        except Exception:

            logger.exception(
                "Validation failed for "
                "document %s (non-blocking)",
                document_id
            )

    def _detect_duplicates(
        self,
        document_id: str
    ):
        """
        Run duplicate detection against existing completed documents.

        This is non-blocking: if duplicate detection fails,
        document processing still completes successfully.
        """

        if self.duplicate_service is None:

            logger.debug(
                "No duplicate detection service "
                "configured, skipping."
            )

            return

        try:

            result = (
                self.duplicate_service
                .check_document(document_id)
            )

            if result and result.matches:

                if self.duplicate_repository:

                    self.duplicate_repository.save_matches([
                        m.to_dict()
                        for m in result.matches
                    ])

                logger.info(
                    "Document %s duplicate check: "
                    "%d matches (%d exact, %d near)",
                    document_id,
                    len(result.matches),
                    len(result.exact_matches),
                    len(result.near_matches),
                )

        except Exception:

            logger.exception(
                "Duplicate detection failed for "
                "document %s (non-blocking)",
                document_id
            )

    def _detect_anomalies(
        self,
        document_id: str
    ):
        """
        Run anomaly detection on extracted document features.

        This is non-blocking: if anomaly detection fails,
        document processing remains completed.
        """

        if self.anomaly_service is None:

            logger.debug(
                "No anomaly detection service "
                "configured, skipping."
            )

            return

        try:

            result = (
                self.anomaly_service
                .check_document(
                    document_id=document_id,
                    persist=True,
                )
            )

            if result:

                logger.info(
                    "Document %s anomaly check: "
                    "is_anomaly=%s (score=%.4f)",
                    document_id,
                    result.is_anomaly,
                    result.anomaly_score,
                )

        except Exception:

            logger.exception(
                "Anomaly detection failed for "
                "document %s (non-blocking)",
                document_id
            )

    def _correct_ocr(
        self,
        raw_text: str,
    ) -> str:
        """
        Run OCR post-processing correction.

        This is non-blocking: if correction fails,
        the original text is returned unchanged.
        """
        if self.ocr_correction_service is None:
            return raw_text

        try:
            return (
                self.ocr_correction_service
                .correct_text(raw_text)
            )
        except Exception:
            logger.exception(
                "OCR correction failed "
                "(non-blocking, using original)"
            )
            return raw_text

    def _run_ai_analysis(
        self,
        document_id: str,
        cleaned_text: str,
        document_type: str | None,
        filename: str | None,
    ):
        """
        Run AI semantic analysis on extracted text.

        This is non-blocking: if analysis fails,
        document processing still completes.
        """

        if self.ai_analysis_service is None:

            logger.debug(
                "No AI analysis service "
                "configured, skipping."
            )

            return

        try:

            ai_result = (
                self.ai_analysis_service
                .analyze_document(
                    document_text=cleaned_text,
                    document_type=document_type,
                    filename=filename,
                )
            )

            # Store AI analysis in repository
            # as a special extraction field
            self.repository.store_ai_analysis(
                document_id=document_id,
                ai_analysis=ai_result,
            )

            logger.info(
                "Document %s AI analysis: "
                "method=%s",
                document_id,
                ai_result.get(
                    "analysis_method", "unknown"
                ),
            )

        except Exception:

            logger.exception(
                "AI analysis failed for "
                "document %s (non-blocking)",
                document_id
            )

    def _index_for_rag(
        self,
        document_id: str,
        document_type: str,
        filename: str,
        fallback_text: str,
        extraction_result: Any = None,
    ):
        """
        Index document pages and structured extraction entities into RAG vector store.

        This is non-blocking: if indexing encounters an issue,
        document processing still completes successfully.
        """
        try:
            from app.rag.pipeline import get_rag_pipeline

            rag_pipeline = get_rag_pipeline()

            pages = []
            if hasattr(self.pipeline, "page_repository") and self.pipeline.page_repository:
                pages = self.pipeline.page_repository.get_by_document_id(document_id)

            ext_data = None
            if extraction_result:
                if hasattr(extraction_result, "fields"):
                    ext_data = getattr(extraction_result, "fields")
                elif isinstance(extraction_result, dict):
                    ext_data = extraction_result

            count = rag_pipeline.index_document(
                document_id=document_id,
                document_type=document_type,
                filename=filename,
                pages=pages,
                fallback_text=fallback_text,
                extraction_data=ext_data,
            )

            logger.info(
                "RAG indexed %d chunks for document %s",
                count,
                document_id,
            )

        except Exception:
            logger.exception(
                "RAG indexing failed for document %s (non-blocking)",
                document_id,
            )

