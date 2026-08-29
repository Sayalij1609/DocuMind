from app.processing.ocr_service import OCRService


ocr = OCRService(
    tesseract_cmd="tesseract"
)

text = ocr.extract_text(
   "uploads/19.jpeg"
)

print(text)