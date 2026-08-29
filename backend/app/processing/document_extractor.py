from pathlib import Path

from app.processing.ocr_service import OCRService
from app.processing.pdf_processor import PDFProcessor


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
    ) -> str:

        extension = (
            file_type.lower()
        )

        if extension == ".pdf":

            return self._extract_pdf(
                file_path
            )

        if extension in {
            ".jpg",
            ".jpeg",
            ".png"
        }:

            return (
                self.ocr_service
                .extract_text(
                    file_path
                )
            )

        raise ValueError(
            f"Unsupported document type: "
            f"{file_type}"
        )


    def _extract_pdf(
        self,
        file_path: str
    ) -> str:

        has_text = (
            self.pdf_processor
            .has_extractable_text(
                file_path
            )
        )

        if has_text:

            return (
                self.pdf_processor
                .extract_text(
                    file_path
                )
            )

        return (
            self.pdf_processor
            .extract_text_with_ocr(
                file_path,
                self.ocr_service
            )
        )