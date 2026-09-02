from pathlib import Path

from PIL import Image


class PageStorageService:

    def __init__(
        self,
        storage_dir: str
    ):

        self.storage_dir = Path(
            storage_dir
        )

        self.storage_dir.mkdir(
            parents=True,
            exist_ok=True
        )

    def save_page_image(
        self,
        document_id: str,
        page_number: int,
        image: Image.Image
    ) -> tuple[str, int, int]:

        document_dir = (
            self.storage_dir /
            document_id
        )

        document_dir.mkdir(
            parents=True,
            exist_ok=True
        )

        filename = (
            f"page_{page_number:03d}.png"
        )

        file_path = (
            document_dir /
            filename
        )

        image.save(
            file_path,
            format="PNG"
        )

        width, height = image.size

        return (
            str(file_path),
            width,
            height
        )