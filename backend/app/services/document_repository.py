from typing import List, Optional
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.document import Document ,  DocumentStatus


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