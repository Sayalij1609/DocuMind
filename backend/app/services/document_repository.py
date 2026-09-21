from typing import Any, List, Optional
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.document import Document ,  DocumentStatus
from app.models.extraction_result import (
    ExtractionResultModel,
)


class DocumentRepository:

    def __init__(
        self,
        session: Session
    ):

        self.session = session


    def create(
        self,
        document: Document
    ) -> Document:

        self.session.add(document)

        self.session.commit()

        self.session.refresh(document)

        return document


    def get_by_id(
        self,
        document_id: str
    ) -> Optional[Document]:

        statement = select(
            Document
        ).where(
            Document.document_id == document_id
        )

        return self.session.scalar(
            statement
        )


    def get_all(
        self,
        skip: int = 0,
        limit: int = 20
    ) -> List[Document]:

        statement = (
            select(Document)
            .order_by(
                Document.created_at.desc()
            )
            .offset(skip)
            .limit(limit)
        )

        return list(
            self.session.scalars(
                statement
            ).all()
        )


    def count(self) -> int:

        statement = select(
            func.count()
        ).select_from(
            Document
        )

        return self.session.scalar(
            statement
        ) or 0


    def delete(
        self,
        document_id: str
    ) -> bool:

        document = self.get_by_id(
            document_id
        )

        if not document:

            return False

        self.session.delete(
            document
        )

        self.session.commit()

        return True

    def update_status(
        self,
        document_id: str,
        status: DocumentStatus
    ) -> Optional[Document]:

        document = self.get_by_id(
            document_id
        )

        if not document:

            return None

        document.status = status

        self.session.commit()

        self.session.refresh(
            document
        )

        return document

    def update_classification(
        self,
        document_id: str,
        document_type: str,
        confidence: float
    ) -> Optional[Document]:
        """
        Update classification results on
        a document.
        """

        document = self.get_by_id(
            document_id
        )

        if not document:

            return None

        document.document_type = document_type

        document.classification_confidence = (
            confidence
        )

        document.classified_at = (
            datetime.utcnow()
        )

        self.session.commit()

        self.session.refresh(
            document
        )

        return document

    # ----------------------------------------
    # AI Analysis Storage
    # ----------------------------------------

    def store_ai_analysis(
        self,
        document_id: str,
        ai_analysis: dict[str, Any],
    ) -> None:
        """
        Store AI analysis result inside the
        extraction_results JSON column.

        Uses the __ai_analysis__ key so it
        does not collide with field-level data.
        """

        statement = select(
            ExtractionResultModel
        ).where(
            ExtractionResultModel.document_id
            == document_id
        )

        record = self.session.scalar(statement)

        if record:
            # Merge into existing fields
            fields = dict(
                record.extracted_fields or {}
            )
            fields["__ai_analysis__"] = ai_analysis
            record.extracted_fields = fields

            from sqlalchemy.orm.attributes import (
                flag_modified,
            )
            flag_modified(
                record, "extracted_fields"
            )

            self.session.commit()
        else:
            # No extraction record yet — create one
            record = ExtractionResultModel(
                document_id=document_id,
                document_type="unknown",
                extracted_fields={
                    "__ai_analysis__": ai_analysis
                },
                extraction_method="ai_analysis",
                extraction_version="1.0.0",
                extracted_at=datetime.utcnow(),
            )
            self.session.add(record)
            self.session.commit()

    def get_ai_analysis(
        self,
        document_id: str,
    ) -> Optional[dict[str, Any]]:
        """
        Retrieve AI analysis from extraction result.
        """

        statement = select(
            ExtractionResultModel
        ).where(
            ExtractionResultModel.document_id
            == document_id
        )

        record = self.session.scalar(statement)

        if not record or not record.extracted_fields:
            return None

        return record.extracted_fields.get(
            "__ai_analysis__"
        )