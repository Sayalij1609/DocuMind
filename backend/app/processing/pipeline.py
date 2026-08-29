from app.models.document import Document
from app.models.document_content import (
    DocumentContent
)

from app.processing.document_extractor import (
    DocumentExtractor
)

from app.processing.text_cleaner import (
    TextCleaner
)

from app.services.document_content_repository import (
    DocumentContentRepository
)


class DocumentProcessingPipeline:

    def __init__(
        self,
        extractor: DocumentExtractor,
        cleaner: TextCleaner,
        content_repository: DocumentContentRepository
    ):

        self.extractor = extractor

        self.cleaner = cleaner

        self.content_repository = (
            content_repository
        )


    def process(
        self,
        document: Document
    ) -> DocumentContent:

        result = self.extractor.extract(
            document.file_path,
            document.file_type
        )

        cleaned_text = self.cleaner.clean(
            result.text
        )

        content = DocumentContent(

            document_id=document.document_id,

            raw_text=result.text,

            cleaned_text=cleaned_text,

            extraction_method=(
                result.extraction_method
            ),

            page_count=result.page_count
        )

        return self.content_repository.create(
            content
        )

    def _get_extraction_method(
        self,
        document: Document,
        raw_text: str
    ) -> str:

        if document.file_type == ".pdf":

            return "pdf_text_or_ocr"

        return "image_ocr"