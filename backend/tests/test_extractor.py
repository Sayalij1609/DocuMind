from app.processing.document_extractor import (
    DocumentExtractor
)


extractor = DocumentExtractor(
    tesseract_cmd="tesseract"
)


text = extractor.extract(
    "uploads/sample_invoice_image.pdf",
    ".pdf"
)


print("=" * 60)

print(text)

print("=" * 60)