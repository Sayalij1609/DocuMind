# Document service
from pathlib import Path
from uuid import uuid4
import shutil

from fastapi import UploadFile


class DocumentService:

    ALLOWED_EXTENSIONS = {
        ".pdf",
        ".jpg",
        ".jpeg",
        ".png"
    }

    def __init__(self, upload_dir: str):
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    def validate_file(self, filename: str) -> str:
        extension = Path(filename).suffix.lower()

        if extension not in self.ALLOWED_EXTENSIONS:
            raise ValueError(
                f"Unsupported file type: {extension}"
            )

        return extension

    async def save_document(
        self,
        file: UploadFile
    ) -> dict:

        extension = self.validate_file(file.filename)

        document_id = str(uuid4())

        safe_filename = (
            f"{document_id}{extension}"
        )

        file_path = self.upload_dir / safe_filename

        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        file_size = file_path.stat().st_size

        return {
            "document_id": document_id,
            "filename": file.filename,
            "file_type": extension,
            "file_size": file_size,
            "file_path": str(file_path)
        }