"""
Model metadata database model.

Tracks versioned machine learning models, hyperparameters, training metrics,
and active production deployment flags.
"""

from datetime import datetime, timezone

from sqlalchemy import Boolean
from sqlalchemy import DateTime
from sqlalchemy import Integer
from sqlalchemy import JSON
from sqlalchemy import String
from sqlalchemy import UniqueConstraint
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from app.database.base import Base


class ModelMetadataModel(Base):

    __tablename__ = "model_metadata"

    __table_args__ = (
        UniqueConstraint(
            "name",
            "version",
            name="uq_model_metadata_name_version",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    version: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    model_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    artifact_path: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    parameters: Mapped[dict] = mapped_column(
        JSON,
        default=dict,
        nullable=False,
    )

    metrics: Mapped[dict | None] = mapped_column(
        JSON,
        default=None,
        nullable=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
    )

    trained_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
        default=None,
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
