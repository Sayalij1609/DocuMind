from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from app.models.document import (
    Document,
    DocumentStatus
)

from app.services.document_repository import (
    DocumentRepository
)


class DocumentService:

    ALLOWED_EXTENSIONS = {
        ".pdf",
        ".jpg",
        ".jpeg",
        ".png"
    }

    ALLOWED_MIME_TYPES = {
        ".pdf": {
            "application/pdf"
        },
        ".jpg": {
            "image/jpeg"
        },
        ".jpeg": {
            "image/jpeg"
        },
        ".png": {
            "image/png"
        }
    }

    CHUNK_SIZE = 1024 * 1024

    def __init__(
        self,
        upload_dir: str,
        repository: DocumentRepository,
        max_file_size: int
    ):

        self.upload_dir = Path(upload_dir)

        self.upload_dir.mkdir(
            parents=True,
            exist_ok=True
        )

        self.repository = repository

        self.max_file_size = max_file_size

    def validate_file(
        self,
        filename: str,
        content_type: str | None
    ) -> str:

        extension = Path(
            filename
        ).suffix.lower()

        if extension not in self.ALLOWED_EXTENSIONS:

            raise ValueError(
                f"Unsupported file type: {extension}"
            )

        allowed_mime_types = (
            self.ALLOWED_MIME_TYPES[extension]
        )

        if content_type not in allowed_mime_types:

            raise ValueError(
                f"Invalid MIME type '{content_type}' "
                f"for {extension} file."
            )

        return extension

    async def save_document(
        self,
        file: UploadFile
    ) -> Document:

        extension = self.validate_file(
            file.filename,
            file.content_type
        )

        document_id = str(uuid4())

        safe_filename = (
            f"{document_id}{extension}"
        )

        file_path = (
            self.upload_dir /
            safe_filename
        )

        file_size = 0

        # --------------------------------
        # Save uploaded file
        # --------------------------------

        try:

            with file_path.open("wb") as buffer:

                while True:

                    chunk = await file.read(
                        self.CHUNK_SIZE
                    )

                    if not chunk:
                        break

                    file_size += len(chunk)

                    if file_size > self.max_file_size:

                        raise ValueError(
                            f"File exceeds the maximum "
                            f"allowed size of "
                            f"{self.max_file_size / (1024 * 1024):.1f} MB."
                        )

                    buffer.write(chunk)

        except Exception:

            if file_path.exists():
                file_path.unlink()

            raise

        # --------------------------------
        # Create database record
        # --------------------------------

        document = Document(
            document_id=document_id,
            filename=file.filename,
            file_type=extension,
            file_size=file_size,
            file_path=str(file_path),
            status=DocumentStatus.UPLOADED
        )

        self.repository.create(
            document
        )

        return document

    def get_document(
        self,
        document_id: str
    ):

        return self.repository.get_by_id(
            document_id
        )

    def get_all_documents(
        self,
        skip: int = 0,
        limit: int = 20
    ):

        documents = self.repository.get_all(
            skip=skip,
            limit=limit
        )

        total = self.repository.count()

        return documents, total

    def delete_document(
        self,
        document_id: str
    ) -> bool:

        document = (
            self.repository.get_by_id(
                document_id
            )
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