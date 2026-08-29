from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.document_content import (
    DocumentContent
)


class DocumentContentRepository:

    def __init__(
        self,
        session: Session
    ):

        self.session = session


    def create(
        self,
        content: DocumentContent
    ) -> DocumentContent:

        self.session.add(content)

        self.session.commit()

        self.session.refresh(content)

        return content


    def get_by_document_id(
        self,
        document_id: str
    ) -> Optional[DocumentContent]:

        statement = select(
            DocumentContent
        ).where(
            DocumentContent.document_id
            == document_id
        )

        return self.session.scalar(
            statement
        )


    def update(
        self,
        content: DocumentContent
    ) -> DocumentContent:

        self.session.commit()

        self.session.refresh(content)

        return content

        