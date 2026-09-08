from datetime import datetime
from enum import Enum
from uuid import uuid4
from sqlalchemy.orm import relationship
from sqlalchemy import DateTime, Enum as SQLEnum
from sqlalchemy import Float, Integer, String

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


    document_type: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        default=None
    )


    classification_confidence: Mapped[
        float | None
    ] = mapped_column(
        Float,
        nullable=True,
        default=None
    )


    classified_at: Mapped[
        datetime | None
    ] = mapped_column(
        DateTime,
        nullable=True,
        default=None
    )

    pages = relationship(
        "DocumentPage",
        back_populates="document",
        cascade="all, delete-orphan"
    )