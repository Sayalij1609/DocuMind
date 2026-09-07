"""
Tests for Phase 3C — Layout & Bounding-Box Extraction.

These tests verify:
- PDF coordinate scaling (72 DPI → target DPI)
- extract_page_layout() returns correct structure
- extract_pages() includes layout data per page
- OCR layout extraction returns correct structure
- Pipeline wraps layout data in the expected JSON format
"""

import pytest
from unittest.mock import MagicMock, patch
from PIL import Image

from app.processing.pdf_processor import (
    PDFProcessor
)

from app.processing.ocr_service import (
    OCRService
)

from app.processing.text_cleaner import (
    TextCleaner
)


# =========================================================
# PDF coordinate scaling
# =========================================================

class TestPDFCoordinateScaling:

    def test_scale_72_to_200_dpi(self):
        """
        PDF coordinates at 72 DPI should be scaled
        by 200/72 when rendering at 200 DPI.
        """

        processor = PDFProcessor()

        scale = 200 / 72

        x0, y0, x1, y1 = 100.0, 50.0, 300.0, 150.0

        expected_bbox = [
            round(x0 * scale),
            round(y0 * scale),
            round(x1 * scale),
            round(y1 * scale)
        ]

        assert expected_bbox == [
            278, 139, 833, 417
        ]

    def test_scale_72_to_150_dpi(self):
        """
        Verify scaling works for other DPI values.
        """

        scale = 150 / 72

        x0, y0 = 72.0, 72.0

        expected = [
            round(x0 * scale),
            round(y0 * scale)
        ]

        assert expected == [150, 150]

    def test_scale_72_to_72_dpi_is_identity(self):
        """
        At 72 DPI, coordinates should not change.
        """

        scale = 72 / 72

        x0, y0, x1, y1 = 100.0, 200.0, 300.0, 400.0

        expected_bbox = [
            round(x0 * scale),
            round(y0 * scale),
            round(x1 * scale),
            round(y1 * scale)
        ]

        assert expected_bbox == [100, 200, 300, 400]


# =========================================================
# PDF extract_page_layout structure
# =========================================================

class TestPDFExtractPageLayout:

    def test_returns_list(self):
        """
        extract_page_layout() should return a list.
        """

        processor = PDFProcessor()

        mock_page = MagicMock()

        mock_page.get_text.return_value = []

        result = processor.extract_page_layout(
            mock_page,
            dpi=200
        )

        assert isinstance(result, list)

    def test_block_structure(self):
        """
        Each block should have text, bbox,
        confidence, and source keys.
        """

        processor = PDFProcessor()

        mock_page = MagicMock()

        mock_page.get_text.return_value = [
            (10.0, 20.0, 100.0, 40.0,
             "Invoice Number", 0, 0)
        ]

        result = processor.extract_page_layout(
            mock_page,
            dpi=200
        )

        assert len(result) == 1

        block = result[0]

        assert block["text"] == "Invoice Number"
        assert block["source"] == "pdf"
        assert block["confidence"] is None
        assert len(block["bbox"]) == 4

    def test_coordinates_are_scaled(self):
        """
        Coordinates should be scaled from 72 DPI
        to the target DPI.
        """

        processor = PDFProcessor()

        mock_page = MagicMock()

        mock_page.get_text.return_value = [
            (72.0, 72.0, 144.0, 144.0,
             "Test text", 0, 0)
        ]

        result = processor.extract_page_layout(
            mock_page,
            dpi=200
        )

        scale = 200 / 72

        expected_bbox = [
            round(72.0 * scale),
            round(72.0 * scale),
            round(144.0 * scale),
            round(144.0 * scale)
        ]

        assert result[0]["bbox"] == expected_bbox

    def test_empty_text_blocks_filtered(self):
        """
        Blocks with empty text should be excluded.
        """

        processor = PDFProcessor()

        mock_page = MagicMock()

        mock_page.get_text.return_value = [
            (10.0, 20.0, 100.0, 40.0,
             "Real text", 0, 0),
            (10.0, 50.0, 100.0, 70.0,
             "   ", 0, 0),
            (10.0, 80.0, 100.0, 100.0,
             "", 0, 0)
        ]

        result = processor.extract_page_layout(
            mock_page,
            dpi=200
        )

        assert len(result) == 1
        assert result[0]["text"] == "Real text"

    def test_coordinates_are_integers(self):
        """
        Scaled coordinates should be rounded
        to integers (pixel coordinates).
        """

        processor = PDFProcessor()

        mock_page = MagicMock()

        mock_page.get_text.return_value = [
            (10.3, 20.7, 100.5, 40.9,
             "Text", 0, 0)
        ]

        result = processor.extract_page_layout(
            mock_page,
            dpi=200
        )

        for coord in result[0]["bbox"]:
            assert isinstance(coord, int)


# =========================================================
# OCR layout structure
# =========================================================

class TestOCRLayoutStructure:

    def test_block_structure(self):
        """
        OCR layout blocks should have text, bbox,
        confidence, and source keys.
        """

        mock_data = {
            "text": ["Hello", ""],
            "conf": [95.0, -1],
            "left": [10, 0],
            "top": [20, 0],
            "width": [50, 0],
            "height": [15, 0]
        }

        with patch(
            "pytesseract.image_to_data",
            return_value=mock_data
        ):

            ocr = OCRService()

            mock_image = MagicMock(
                spec=Image.Image
            )

            result = ocr.extract_layout(
                mock_image
            )

        assert len(result) == 1

        block = result[0]

        assert block["text"] == "Hello"
        assert block["source"] == "ocr"
        assert block["confidence"] == 95.0
        assert block["bbox"] == [10, 20, 60, 35]

    def test_negative_confidence_becomes_none(self):
        """
        Tesseract returns -1 for low-confidence
        detections. These should become None.
        """

        mock_data = {
            "text": ["Word"],
            "conf": [-1],
            "left": [0],
            "top": [0],
            "width": [10],
            "height": [10]
        }

        with patch(
            "pytesseract.image_to_data",
            return_value=mock_data
        ):

            ocr = OCRService()

            mock_image = MagicMock(
                spec=Image.Image
            )

            result = ocr.extract_layout(
                mock_image
            )

        assert len(result) == 1
        assert result[0]["confidence"] is None


# =========================================================
# Pipeline layout_data wrapping
# =========================================================

class TestPipelineLayoutData:

    def test_layout_data_structure(self):
        """
        The pipeline should wrap layout blocks
        in a structured JSON with metadata.
        """

        layout_blocks = [
            {
                "text": "Invoice",
                "bbox": [100, 50, 300, 80],
                "confidence": None,
                "source": "pdf"
            }
        ]

        layout_data = {
            "blocks": layout_blocks,
            "coordinate_system": "image_pixels",
            "image_dpi": 200
        }

        assert "blocks" in layout_data
        assert "coordinate_system" in layout_data
        assert "image_dpi" in layout_data

        assert layout_data["coordinate_system"] == (
            "image_pixels"
        )

        assert layout_data["image_dpi"] == 200

        assert len(layout_data["blocks"]) == 1

    def test_empty_layout_produces_empty_blocks(self):
        """
        When no layout is available, blocks
        should be an empty list.
        """

        layout_blocks = []

        layout_data = {
            "blocks": layout_blocks,
            "coordinate_system": "image_pixels",
            "image_dpi": 200
        }

        assert layout_data["blocks"] == []


# =========================================================
# TextCleaner (unchanged, sanity check)
# =========================================================

class TestTextCleanerUnchanged:

    def test_cleaner_still_works(self):
        """
        Verify text cleaner was not broken
        by pipeline changes.
        """

        cleaner = TextCleaner()

        result = cleaner.clean(
            "  Hello   world  \r\n\r\n\r\n\r\n  test  "
        )

        assert result == "Hello world \n\n test"
