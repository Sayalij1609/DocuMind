from app.models.document import Document
from app.models.document_content import (
    DocumentContent
)
from app.models.document_page import (
    DocumentPage
)

from app.processing.document_extractor import (
    DocumentExtractor
)

from app.processing.page_storage import (
    PageStorageService
)

from app.processing.text_cleaner import (
    TextCleaner
)

from app.services.document_content_repository import (
    DocumentContentRepository
)

from app.services.document_page_repository import (
    DocumentPageRepository
)


class DocumentProcessingPipeline:

    def __init__(
        self,
        extractor: DocumentExtractor,
        cleaner: TextCleaner,
        content_repository: DocumentContentRepository,
        page_repository: DocumentPageRepository,
        page_storage: PageStorageService
    ):

        self.extractor = extractor

        self.cleaner = cleaner

        self.content_repository = (
            content_repository
        )

        self.page_repository = (
            page_repository
        )

        self.page_storage = (
            page_storage
        )

    def process(
        self,
        document: Document
    ) -> DocumentContent:

        extraction_result = (
            self.extractor.extract(
                document.file_path,
                document.file_type
            )
        )

        cleaned_text = self.cleaner.clean(
            extraction_result.text
        )

        document_content = (
            DocumentContent(
                document_id=document.document_id,
                raw_text=extraction_result.text,
                cleaned_text=cleaned_text,
                extraction_method=(
                    extraction_result
                    .extraction_method
                ),
                page_count=(
                    extraction_result
                    .page_count
                )
            )
        )

        saved_content = (
            self.content_repository.create(
                document_content
            )
        )

        self._process_pages(
            document
        )

        return saved_content

    def _process_pages(
        self,
        document: Document
    ):

        pages = (
            self._extract_page_data(
                document
            )
        )

        page_models = []

        for page_data in pages:

            image_path, width, height = (
                self.page_storage
                .save_page_image(
                    document.document_id,
                    page_data["page_number"],
                    page_data["image"]
                )
            )

            raw_text = page_data["text"]

            cleaned_text = (
                self.cleaner.clean(
                    raw_text
                )
            )

            page = DocumentPage(

                document_id=(
                    document.document_id
                ),

                page_number=(
                    page_data["page_number"]
                ),

                raw_text=raw_text,

                cleaned_text=cleaned_text,

                extraction_method=(
                    page_data.get(
                        "extraction_method",
                        "unknown"
                    )
                ),

                image_path=image_path,

                image_width=width,

                image_height=height,

                layout_data={}
            )

            page_models.append(
                page
            )

            page_data["image"].close()

        if page_models:

            self.page_repository.create_many(
                page_models
            )

    def _extract_page_data(
        self,
        document: Document
    ):

        if document.file_type == ".pdf":

            return (
                self.extractor
                .pdf_processor
                .extract_pages(
                    document.file_path ,
                    ocr_service=self.extractor.ocr_service
                )
            )

        return [
            {
                "page_number": 1,
                "text": (
                    self.extractor
                    .ocr_service
                    .extract_text(
                        document.file_path
                    )
                ),
                "image": self._load_image(
                    document.file_path
                )
            }
        ]

    def _load_image(
        self,
        file_path: str
    ):

        from PIL import Image

        return Image.open(
            file_path
        )