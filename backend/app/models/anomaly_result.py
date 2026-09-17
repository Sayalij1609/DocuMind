"""
Anomaly result database model.

Stores document-level anomaly detection outcomes:
- whether the document was evaluated as an outlier (is_anomaly)
- the continuous anomaly score
- the decision function score
- the full snapshot of extracted features for explainability
- model version and detection timestamp
"""

from datetime import datetime, timezone

from sqlalchemy import Boolean
from sqlalchemy import DateTime
from sqlalchemy import Float
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import JSON
from sqlalchemy import String

from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from app.database.base import Base


class AnomalyResultModel(Base):

    __tablename__ = "anomaly_results"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    document_id: Mapped[str] = mapped_column(
        ForeignKey(
            "documents.document_id",
            ondelete="CASCADE",
        ),
        nullable=False,
        unique=True,
        index=True,
    )

    is_anomaly: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        index=True,
    )

    anomaly_score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    decision_function_score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    features: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )

    model_version: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="isolation_forest_v1",
    )

    detected_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
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

    document = relationship(
        "Document",
        back_populates="anomaly",
    )
