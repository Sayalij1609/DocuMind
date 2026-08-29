from app.processing.ocr_service import (
    OCRService
)

from app.processing.pdf_processor import (
    PDFProcessor
)

from app.processing.result import (
    ExtractionResult
)


class DocumentExtractor:

    def __init__(
        self,
        tesseract_cmd: str = "tesseract"
    ):

        self.pdf_processor = (
            PDFProcessor()
        )

        self.ocr_service = (
            OCRService(
                tesseract_cmd=tesseract_cmd
            )
        )


    def extract(
        self,
        file_path: str,
        file_type: str
    ) -> ExtractionResult:

        extension = file_type.lower()

        if extension == ".pdf":

            return self._extract_pdf(
                file_path
            )

        if extension in {
            ".jpg",
            ".jpeg",
            ".png"
        }:

            text = (
                self.ocr_service
                .extract_text(
                    file_path
                )
            )

            return ExtractionResult(
                text=text,
                extraction_method="image_ocr",
                page_count=1
            )

        raise ValueError(
            f"Unsupported document type: "
            f"{file_type}"
        )


    def _extract_pdf(
        self,
        file_path: str
    ) -> ExtractionResult:

        page_count = (
            self.pdf_processor
            .get_page_count(
                file_path
            )
        )

        has_text = (
            self.pdf_processor
            .has_extractable_text(
                file_path
            )
        )

        if has_text:

            text = (
                self.pdf_processor
                .extract_text(
                    file_path
                )
            )

            return ExtractionResult(
                text=text,
                extraction_method="pdf_text",
                page_count=page_count
            )

        text = (
            self.pdf_processor
            .extract_text_with_ocr(
                file_path,
                self.ocr_service
            )
        )

        return ExtractionResult(
            text=text,
            extraction_method="pdf_ocr",
            page_count=page_count
        )