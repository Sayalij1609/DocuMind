import pytest

from app.services.document_service import (
    DocumentService
)

# file validation
def test_valid_pdf():

    service = DocumentService(
        upload_dir="uploads",
        repository=None,
        max_file_size=10 * 1024 * 1024
    )

    extension = service.validate_file(
        "invoice.pdf",
        "application/pdf"
    )

    assert extension == ".pdf"

# Test invalid extension
def test_invalid_extension():

    service = DocumentService(
        upload_dir="uploads",
        repository=None,
        max_file_size=10 * 1024 * 1024
    )

    with pytest.raises(ValueError):

        service.validate_file(
            "virus.exe",
            "application/x-executable"
        )

# Test MIME mismatch
def test_invalid_mime_type():

    service = DocumentService(
        upload_dir="uploads",
        repository=None,
        max_file_size=10 * 1024 * 1024
    )

    with pytest.raises(ValueError):

        service.validate_file(
            "invoice.pdf",
            "image/png"
        )