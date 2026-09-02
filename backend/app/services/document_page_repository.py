from typing import List

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.document_page import (
    DocumentPage
)


class DocumentPageRepository:

    def __init__(
        self,
        session: Session
    ):

        self.session = session

    def create(
        self,
        page: DocumentPage
    ) -> DocumentPage:

        self.session.add(
            page
        )

        self.session.commit()

        self.session.refresh(
            page
        )

        return page

    def create_many(
        self,
        pages: List[DocumentPage]
    ) -> List[DocumentPage]:

        self.session.add_all(
            pages
        )

        self.session.commit()

        for page in pages:

            self.session.refresh(
                page
            )

        return pages

    def get_by_document_id(
        self,
        document_id: str
    ) -> List[DocumentPage]:

        statement = (
            select(DocumentPage)
            .where(
                DocumentPage.document_id
                == document_id
            )
            .order_by(
                DocumentPage.page_number
            )
        )

        return list(
            self.session.scalars(
                statement
            ).all()
        )