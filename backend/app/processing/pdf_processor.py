from app.models import document_content
from app.models import document_content
from app.models import document_content
from app.models import document_content
from app.models import document_content
from app.models import document_content
from app.models import document_content
from app.models import document_content
from pathlib import Path
from PIL import Image
import io
import fitz

class PDFProcessor:

    def __init__(
        self,
        minimum_text_length: int = 20
    ):

        self.minimum_text_length = (
            minimum_text_length
        )


    def extract_text(
        self,
        file_path: str
    ) -> str:

        path = Path(file_path)

        if not path.exists():

            raise FileNotFoundError(
                f"File not found: {file_path}"
            )

        document = fitz.open(
            file_path
        )

        try:

            pages = []

            for page in document:

                text = page.get_text()

                if text:
                    pages.append(text)

            return "\n".join(pages).strip()

        finally:

            document.close()


    def has_extractable_text(
        self,
        file_path: str
    ) -> bool:

        text = self.extract_text(
            file_path
        )

        return len(text.strip()) >= (
            self.minimum_text_length
        )

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

    def extract_text_with_ocr(
        self,
        file_path: str,
        ocr_service,
        dpi: int = 200
    ) -> str:

        document = fitz.open(
            file_path
        )

        pages = []

        try:

            for page in document:

                image = self.render_page_as_image(
                    page,
                    dpi=dpi
                )

                try:

                    text = (
                    ocr_service
                        .extract_text_from_image(
                            image
                        )
                    )

                    if text:

                        pages.append(text)

                finally:

                    image.close()

            return "\n\n".join(
                pages
            ).strip()

        finally:

            document.close()
            
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

