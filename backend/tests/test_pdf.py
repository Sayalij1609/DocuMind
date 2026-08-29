from app.processing.pdf_processor import PDFProcessor


processor = PDFProcessor()

text = processor.extract_text(
    "uploads/sample_invoice.pdf"
)

print(text)

print(
    "Has extractable text:",
    processor.has_extractable_text(
        "uploads/sample_invoice.pdf"
    )
)