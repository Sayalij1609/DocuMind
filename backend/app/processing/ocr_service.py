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

    def extract_layout(
        self,
        image
    ) -> list[dict]:

        data = pytesseract.image_to_data(
            image,
            output_type=pytesseract.Output.DICT
        )

        layout = []

        total_items = len(
            data["text"]
        )

        for index in range(
            total_items
        ):

            text = data["text"][index].strip()

            if not text:
                continue

            raw_confidence = float(
                data["conf"][index]
            )

            confidence = (
                raw_confidence
                if raw_confidence >= 0
                else None
            )

            x = int(
                data["left"][index]
            )

            y = int(
                data["top"][index]
            )

            width = int(
                data["width"][index]
            )

            height = int(
                data["height"][index]
            )

            layout.append(
                {
                    "text": text,
                    "bbox": [
                        x,
                        y,
                        x + width,
                        y + height
                    ],
                    "confidence": confidence,
                    "source": "ocr"
                }
            )

        return layout