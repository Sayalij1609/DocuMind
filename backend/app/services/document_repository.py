from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.document import Document


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
        self
    ) -> List[Document]:

        statement = select(
            Document
        ).order_by(
            Document.created_at.desc()
        )

        return list(
            self.session.scalars(
                statement
            ).all()
        )


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