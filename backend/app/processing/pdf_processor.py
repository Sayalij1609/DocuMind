from pathlib import Path
import io

import fitz
from PIL import Image


class PDFProcessor:

    def __init__(
        self,
        minimum_text_length: int = 20
    ):

        self.minimum_text_length = (
            minimum_text_length
        )

    # =========================================================
    # DOCUMENT-LEVEL TEXT EXTRACTION
    # =========================================================

    def extract_text(
        self,
        file_path: str
    ) -> str:

        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(
                f"File not found: {file_path}"
            )

        document = fitz.open(file_path)

        try:

            pages = []

            for page in document:

                text = page.get_text()

                if text:
                    pages.append(text)

            return "\n".join(
                pages
            ).strip()

        finally:

            document.close()

    # =========================================================
    # CHECK WHETHER PDF HAS ENOUGH NATIVE TEXT
    # =========================================================

    def has_extractable_text(
        self,
        file_path: str
    ) -> bool:

        text = self.extract_text(
            file_path
        )

        return len(
            text.strip()
        ) >= self.minimum_text_length

    # =========================================================
    # GET NUMBER OF PAGES
    # =========================================================

    def get_page_count(
        self,
        file_path: str
    ) -> int:

        document = fitz.open(
            file_path
        )

        try:

            return len(document)

        finally:

            document.close()

    # =========================================================
    # RENDER PDF PAGE
    # =========================================================

    def render_page(
        self,
        page,
        dpi: int = 200
    ):

        zoom = dpi / 72

        matrix = fitz.Matrix(
            zoom,
            zoom
        )

        pixmap = page.get_pixmap(
            matrix=matrix,
            alpha=False
        )

        return pixmap

    # =========================================================
    # RENDER PAGE AS PIL IMAGE
    # =========================================================

    def render_page_as_image(
        self,
        page,
        dpi: int = 200
    ):

        pixmap = self.render_page(
            page,
            dpi=dpi
        )

        image_bytes = pixmap.tobytes(
            "png"
        )

        return Image.open(
            io.BytesIO(
                image_bytes
            )
        )

    # =========================================================
    # DOCUMENT-LEVEL OCR
    #
    # This method is required by DocumentExtractor.
    # =========================================================

    def extract_text_with_ocr(
        self,
        file_path: str,
        ocr_service
    ) -> str:

        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(
                f"File not found: {file_path}"
            )

        document = fitz.open(
            file_path
        )

        page_texts = []

        try:

            for page in document:

                image = (
                    self.render_page_as_image(
                        page,
                        dpi=200
                    )
                )

                try:

                    text = (
                        ocr_service
                        .extract_text_from_image(
                            image
                        )
                    )

                    if text:
                        page_texts.append(
                            text
                        )

                finally:

                    image.close()

        finally:

            document.close()

        return "\n\n".join(
            page_texts
        ).strip()

    # =========================================================
    # PAGE-LEVEL EXTRACTION
    #
    # Each page independently decides whether to use:
    # PDF native text or OCR.
    # =========================================================

    def extract_pages(
        self,
        file_path: str,
        ocr_service=None,
        dpi: int = 200
    ) -> list[dict]:

        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(
                f"File not found: {file_path}"
            )

        document = fitz.open(
            file_path
        )

        pages = []

        try:

            for index, page in enumerate(
                document
            ):

                page_number = index + 1

                # -----------------------------------------
                # Try native PDF text first
                # -----------------------------------------

                text = page.get_text().strip()

                extraction_method = (
                    "pdf_text"
                )

                # -----------------------------------------
                # If native text is insufficient,
                # use OCR for this individual page.
                # -----------------------------------------

                if (
                    len(text)
                    < self.minimum_text_length
                    and ocr_service is not None
                ):

                    ocr_image = (
                        self.render_page_as_image(
                            page,
                            dpi=dpi
                        )
                    )

                    try:

                        text = (
                            ocr_service
                            .extract_text_from_image(
                                ocr_image
                            )
                        )

                        extraction_method = "ocr"

                        layout = (
                            ocr_service
                            .extract_layout(
                                ocr_image
                            )
                        )

                    finally:

                        ocr_image.close()

                else:

                    # -----------------------------------------
                    # Extract layout from native PDF text
                    # with coordinates scaled to image space
                    # -----------------------------------------

                    layout = (
                        self.extract_page_layout(
                            page,
                            dpi=dpi
                        )
                    )

                # -----------------------------------------
                # Render final page image
                # -----------------------------------------

                page_image = (
                    self.render_page_as_image(
                        page,
                        dpi=dpi
                    )
                )

                # -----------------------------------------
                # Store page information
                # -----------------------------------------

                pages.append(
                    {
                        "page_number": page_number,
                        "text": text.strip(),
                        "image": page_image,
                        "extraction_method": (
                            extraction_method
                        ),
                        "layout": layout
                    }
                )

        finally:

            document.close()

        return pages

    #--------------------------------
    # Extract PDF page layout
    #--------------------------------   

    def extract_page_layout(
        self,
        page,
        dpi: int = 200
    ) -> list[dict]:

        scale = dpi / 72

        blocks = page.get_text(
            "blocks"
        )

        layout = []

        for block in blocks:

            x0, y0, x1, y1, text, *_ = block

            text = text.strip()

            if not text:
                continue

            layout.append(
                {
                    "text": text,
                    "bbox": [
                        round(x0 * scale),
                        round(y0 * scale),
                        round(x1 * scale),
                        round(y1 * scale)
                    ],
                    "confidence": None,
                    "source": "pdf"
                }
            )

        return layout