import pytesseract

from PIL import Image


class OCRService:

    def __init__(
        self,
        tesseract_cmd: str = "tesseract"
    ):

        self.tesseract_cmd = (
            tesseract_cmd
        )

        pytesseract.pytesseract.tesseract_cmd = (
            tesseract_cmd
        )

    def extract_text(
        self,
        file_path: str
    ) -> str:

        image = Image.open(
            file_path
        )

        try:

            return self.extract_text_from_image(
                image
            )

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