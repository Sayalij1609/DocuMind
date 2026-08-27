from pathlib import Path
from uuid import uuid4
import shutil
from datetime import datetime

from fastapi import UploadFile

from app.models.document import Document, DocumentStatus
from app.services.document_repository import DocumentRepository


class DocumentService:

    ALLOWED_EXTENSIONS = {
        ".pdf",
        ".jpg",
        ".jpeg",
        ".png"
    }

    def __init__(
        self,
        upload_dir: str,
        repository: DocumentRepository
    ):

        self.upload_dir = Path(upload_dir)

        self.upload_dir.mkdir(
            parents=True,
            exist_ok=True
        )

        self.repository = repository


    def validate_file(
        self,
        filename: str
    ) -> str:

        extension = Path(
            filename
        ).suffix.lower()

        if extension not in self.ALLOWED_EXTENSIONS:

            raise ValueError(
                f"Unsupported file type: {extension}"
            )

        return extension


    async def save_document(
        self,
        file: UploadFile
    ) -> Document:

        extension = self.validate_file(
            file.filename
        )

        document_id = str(uuid4())

        safe_filename = (
            f"{document_id}{extension}"
        )

        file_path = (
            self.upload_dir /
            safe_filename
        )

        with file_path.open("wb") as buffer:

            shutil.copyfileobj(
                file.file,
                buffer
            )

        file_size = file_path.stat().st_size

        document = Document(
            document_id=document_id,
            filename=file.filename,
            file_type=extension,
            file_size=file_size,
            file_path=str(file_path),
            status=DocumentStatus.UPLOADED,
            created_at=datetime.utcnow()
        )

        self.repository.create(document)

        return document


    def get_document(
        self,
        document_id: str
    ):

        return self.repository.get_by_id(
            document_id
        )


    def get_all_documents(self):

        return self.repository.get_all()


    def delete_document(
        self,
        document_id: str
    ) -> bool:

        document = self.repository.get_by_id(
            document_id
        )

        if not document:
            return False

        file_path = Path(
            document.file_path
        )

        if file_path.exists():
            file_path.unlink()

        return self.repository.delete(
            document_id
        )