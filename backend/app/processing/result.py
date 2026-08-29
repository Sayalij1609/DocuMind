from dataclasses import dataclass


@dataclass
class ExtractionResult:

    text: str

    extraction_method: str

    page_count: int