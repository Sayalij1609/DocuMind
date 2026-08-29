from pathlib import Path

from PIL import Image

import pytesseract


class OCRService:

    def __init__(
        self,
        tesseract_cmd: str | None = None
    ):

        if tesseract_cmd:

            pytesseract.pytesseract.tesseract_cmd = (
                tesseract_cmd
            )


    def extract_text(
        self,
        image_path: str
    ) -> str:

        path = Path(
            image_path
        )

        if not path.exists():

            raise FileNotFoundError(
                f"Image not found: {image_path}"
            )

        image = Image.open(
            image_path
        )

        try:

            text = pytesseract.image_to_string(
                image
            )

            return text.strip()

        finally:

            image.close()

    def extract_text_from_image(
        self,
        image: Image.Image
    ) -> str:

        text = pytesseract.image_to_string(
            image
        )

        return text.strip()