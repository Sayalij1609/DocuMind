from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DocumentContentResponse(BaseModel):

    document_id: str

    raw_text: str

    cleaned_text: str

    extraction_method: str

    page_count: int

    created_at: datetime

    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )