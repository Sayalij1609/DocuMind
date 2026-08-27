from typing import Dict, List, Optional

from app.models.document import Document


class DocumentRepository:

    def __init__(self):
        self.documents: Dict[str, Document] = {}


    def create(self, document: Document) -> Document:

        self.documents[document.document_id] = document

        return document


    def get_by_id(
        self,
        document_id: str
    ) -> Optional[Document]:

        return self.documents.get(document_id)


    def get_all(self) -> List[Document]:

        return list(self.documents.values())


    def delete(self, document_id: str) -> bool:

        if document_id not in self.documents:
            return False

        del self.documents[document_id]

        return True