from datetime import datetime

from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import Text

from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column


from app.database.base import Base


class DocumentContent(Base):

    __tablename__ = "document_contents"


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
        nullable=False,
        unique=True
    )


    raw_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default=""
    )


    cleaned_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default=""
    )


    extraction_method: Mapped[str] = mapped_column(
        nullable=False
    )


    page_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1
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