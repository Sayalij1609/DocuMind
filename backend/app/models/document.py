from datetime import datetime
from enum import Enum
from uuid import uuid4

from sqlalchemy import DateTime, Enum as SQLEnum
from sqlalchemy import Integer, String

from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from app.database.base import Base


class DocumentStatus(str, Enum):

    UPLOADED = "uploaded"

    PROCESSING = "processing"

    COMPLETED = "completed"

    FAILED = "failed"


class Document(Base):

    __tablename__ = "documents"


    document_id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4())
    )


    filename: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )


    file_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False
    )


    file_size: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )


    file_path: Mapped[str] = mapped_column(
        String(500),
        nullable=False
    )


    status: Mapped[DocumentStatus] = mapped_column(
        SQLEnum(DocumentStatus),
        default=DocumentStatus.UPLOADED,
        nullable=False
    )


    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )


    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )