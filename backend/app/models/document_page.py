from datetime import datetime

from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import JSON
from sqlalchemy import Text

from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from app.database.base import Base


class DocumentPage(Base):

    __tablename__ = "document_pages"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    document_id: Mapped[str] = mapped_column(
        ForeignKey(
            "documents.document_id",
            ondelete="CASCADE"
        ),
        nullable=False
    )

    page_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    raw_text: Mapped[str] = mapped_column(
        Text,
        default=""
    )

    cleaned_text: Mapped[str] = mapped_column(
        Text,
        default=""
    )

    image_path: Mapped[str] = mapped_column(
        nullable=False
    )

    image_width: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    image_height: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    layout_data: Mapped[dict] = mapped_column(
        JSON,
        default=dict
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    document = relationship(
        "Document",
        back_populates="pages"
    )