from datetime import datetime, timezone
from enum import Enum
from uuid import uuid4

from sqlalchemy import DateTime, Enum as SQLEnum
from sqlalchemy import Float, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class DocumentStatus(str, Enum):

    UPLOADED = "uploaded"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Document(Base):

    __tablename__ = "documents"

    __table_args__ = (
        Index("ix_documents_status", "status"),
        Index("ix_documents_document_type", "document_type"),
        Index("ix_documents_created_at", "created_at"),
        Index(
            "ix_documents_type_status",
            "document_type",
            "status",
        ),
    )

    document_id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4()),
    )

    user_id: Mapped[str | None] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
        default=None,
    )

    filename: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    file_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    file_size: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    file_path: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    status: Mapped[DocumentStatus] = mapped_column(
        SQLEnum(DocumentStatus),
        default=DocumentStatus.UPLOADED,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    document_type: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        default=None,
    )

    classification_confidence: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
        default=None,
    )

    classified_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
        default=None,
    )

    # Relationships
    user = relationship(
        "UserModel",
        back_populates="documents",
    )

    content = relationship(
        "DocumentContent",
        back_populates="document",
        cascade="all, delete-orphan",
        uselist=False,
    )

    pages = relationship(
        "DocumentPage",
        back_populates="document",
        cascade="all, delete-orphan",
    )

    classification = relationship(
        "ClassificationResultModel",
        back_populates="document",
        cascade="all, delete-orphan",
        uselist=False,
    )

    extraction = relationship(
        "ExtractionResultModel",
        back_populates="document",
        cascade="all, delete-orphan",
        uselist=False,
    )

    validation = relationship(
        "ValidationResultModel",
        back_populates="document",
        cascade="all, delete-orphan",
        uselist=False,
    )

    anomaly = relationship(
        "AnomalyResultModel",
        back_populates="document",
        cascade="all, delete-orphan",
        uselist=False,
    )

    reviews = relationship(
        "DocumentReviewModel",
        back_populates="document",
        cascade="all, delete-orphan",
    )