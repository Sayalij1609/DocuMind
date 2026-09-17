# Documind

**Intelligent Document Processing & Document Intelligence Platform**

Documind is a production-oriented AI/ML system that accepts documents, extracts text and layout information, classifies document types, validates compliance rules, detects duplicates and anomalies, and provides structured analysis — all through a FastAPI backend with PostgreSQL storage and a modern React dashboard.

---

## Table of Contents

- [Features](#features)
- [Architecture Overview](#architecture-overview)
- [Tech Stack](#tech-stack)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Environment Configuration](#environment-configuration)
- [Database Setup](#database-setup)
- [Running the Server](#running-the-server)
- [API Reference](#api-reference)
- [Phase 1 — Document Ingestion & Storage](#phase-1--document-ingestion--storage)
- [Phase 2 — Text Extraction & OCR](#phase-2--text-extraction--ocr)
- [Phase 3 — Layout Extraction & Bounding Boxes](#phase-3--layout-extraction--bounding-boxes)
- [Phase 4 — Document Classification](#phase-4--document-classification)
- [Testing](#testing)
- [Project Structure](#project-structure)
- [Roadmap](#roadmap)
- [License](#license)

---

## Features

| Phase | Capability | Status |
|-------|-----------|--------|
| **Phase 1** | Document upload, validation & storage | ✅ Completed |
| **Phase 2** | Text extraction (native PDF + OCR) | ✅ Completed |
| **Phase 3** | Layout extraction, bounding boxes, page images | ✅ Completed |
| **Phase 4** | Document classification (TF-IDF + Logistic Regression) | ✅ Completed |
| **Phase 5** | Structured information extraction | 🔜 Planned |
| **Phase 6** | LayoutLMv3 document understanding | 🔜 Planned |
| **Phase 7** | Validation & business rules | 🔜 Planned |
| **Phase 8** | Duplicate & anomaly detection | 🔜 Planned |
| **Phase 9** | React dashboard | 🔜 Planned |
| **Phase 10** | Semantic search & RAG-based Q&A | 🔜 Planned |

---

## Architecture Overview

```
┌──────────────────────────────────────────────────────────────┐
│                        Client / API                          │
│                    (REST — FastAPI + Uvicorn)                 │
└──────────────────────┬───────────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────────┐
│                    Document Routes                           │
│              POST /upload  GET /  GET /{id}                  │
└──────────────────────┬───────────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────────┐
│                   Service Layer                              │
│  DocumentService  →  DocumentProcessingService               │
│                   →  ClassificationService                   │
└──────────┬───────────────┬──────────────────┬────────────────┘
           │               │                  │
           ▼               ▼                  ▼
┌────────────────┐ ┌───────────────┐ ┌──────────────────┐
│  Processing    │ │   ML Module   │ │   Repositories   │
│  Pipeline      │ │  (TF-IDF +   │ │  (SQLAlchemy +   │
│  (Extract,     │ │   LogReg)    │ │   PostgreSQL)    │
│   OCR, Layout) │ │              │ │                  │
└────────────────┘ └───────────────┘ └──────────────────┘
```

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| **API Framework** | FastAPI 0.141 |
| **Language** | Python 3.12+ |
| **Database** | PostgreSQL + SQLAlchemy 2.0 |
| **Migrations** | Alembic |
| **PDF Processing** | PyMuPDF (fitz) |
| **OCR** | Tesseract (via pytesseract) |
| **Image Processing** | Pillow |
| **ML — Classification** | scikit-learn (TF-IDF + LogisticRegression) |
| **Model Serialization** | joblib |
| **Testing** | pytest |
| **Server** | Uvicorn |

---

## Prerequisites

1. **Python 3.12+** — [Download](https://www.python.org/downloads/)
2. **PostgreSQL** — [Download](https://www.postgresql.org/download/)
3. **Tesseract OCR** — [Download](https://github.com/UB-Mannheim/tesseract/wiki)
   - Default install path on Windows: `C:\Program Files\Tesseract-OCR\tesseract.exe`
4. **Git** — [Download](https://git-scm.com/downloads)

---

## Installation

```bash
# Clone the repository
git clone https://github.com/Sayalij1609/Nexora.git
cd Nexora

# Create and activate virtual environment
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# Linux / macOS
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Key Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `fastapi` | 0.141.1 | REST API framework |
| `uvicorn` | 0.52.4 | ASGI server |
| `sqlalchemy` | 2.0.52 | ORM |
| `alembic` | 1.19.1 | Database migrations |
| `pymupdf` | 1.28.2 | PDF text & layout extraction |
| `pytesseract` | 0.3.13 | OCR engine interface |
| `pillow` | 12.3.0 | Image processing |
| `scikit-learn` | 1.9.0 | ML classification |
| `joblib` | 1.6.0 | Model serialization |
| `psycopg2-binary` | 2.9.12 | PostgreSQL driver |
| `pytest` | 9.1.1 | Testing framework |

---

## Environment Configuration

Create a `.env` file inside the `backend/` directory:

```env
APP_NAME=Nexora
APP_VERSION=1.0.0
DEBUG=true
UPLOAD_DIR=uploads
MAX_FILE_SIZE=10485760

# Database
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost:5432/nexora

# Tesseract OCR path (Windows)
TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe

# Classification model
CLASSIFICATION_MODEL_DIR=../ml/artifacts/classification
CLASSIFICATION_CONFIDENCE_THRESHOLD=0.5
```

| Variable | Description | Default |
|----------|------------|---------|
| `APP_NAME` | Application name | `Nexora` |
| `APP_VERSION` | Semantic version | `1.0.0` |
| `DEBUG` | Enable debug mode | `true` |
| `UPLOAD_DIR` | Directory for uploaded files | `uploads` |
| `MAX_FILE_SIZE` | Max upload size in bytes | `10485760` (10 MB) |
| `DATABASE_URL` | PostgreSQL connection string | — |
| `TESSERACT_CMD` | Path to Tesseract binary | — |
| `CLASSIFICATION_MODEL_DIR` | Path to trained model artifacts | `../ml/artifacts/classification` |
| `CLASSIFICATION_CONFIDENCE_THRESHOLD` | Minimum confidence to assign a class | `0.5` |

---

## Database Setup

```bash
# Create the database in PostgreSQL
psql -U postgres
CREATE DATABASE nexora;
\q

# Run migrations
cd backend
venv\Scripts\activate
alembic upgrade head
```

### Migration History

| Migration | Description |
|-----------|-------------|
| `e38e8df06ee0` | Create `documents` table |
| `684d1d37d82b` | Add `document_contents` table |
| `b075e90f23ed` | Add document contents fields |
| `2cfc3752d81d` | Create `document_pages` table |
| `5dc00aeb1959` | Add page extraction method field |
| `cf538797a342` | Add classification fields (`document_type`, `classification_confidence`, `classified_at`) |

---

## Running the Server

```bash
cd backend
venv\Scripts\activate
python -m uvicorn app.main:app --reload
```

The server starts at **http://localhost:8000**.

| Endpoint | Description |
|----------|-------------|
| `http://localhost:8000/` | Application info |
| `http://localhost:8000/health` | Health check |
| `http://localhost:8000/docs` | Swagger UI (interactive API docs) |
| `http://localhost:8000/redoc` | ReDoc (API documentation) |

---

## API Reference

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/documents/upload` | Upload a document (PDF, PNG, JPG, JPEG, TIFF) |
| `GET` | `/api/documents/` | List all documents |
| `GET` | `/api/documents/{id}` | Get document details (includes classification) |
| `GET` | `/api/documents/{id}/content` | Get extracted text content |
| `DELETE` | `/api/documents/{id}` | Delete a document |

### Upload a Document

```bash
curl -X POST http://localhost:8000/api/documents/upload -F "file=@invoice.pdf"
```

### Example Response — GET `/api/documents/{id}`

```json
{
    "document_id": "abc-123",
    "filename": "invoice.pdf",
    "file_type": ".pdf",
    "file_size": 52340,
    "status": "completed",
    "document_type": "invoice",
    "classification_confidence": 0.94,
    "classified_at": "2026-09-07T19:00:00",
    "page_count": 2,
    "created_at": "2026-09-07T18:59:00",
    "updated_at": "2026-09-07T19:00:00"
}
```

---

## Phase 1 — Document Ingestion & Storage

### What It Does

- Accepts document uploads via REST API (`POST /api/documents/upload`)
- Validates file type (PDF, PNG, JPG, JPEG, TIFF) and file size (max 10 MB)
- Stores files on disk in the `uploads/` directory
- Creates a database record with metadata (filename, size, type, upload time)
- Assigns a UUID to each document

### Key Files

| File | Purpose |
|------|---------|
| `app/api/document_routes.py` | FastAPI route handlers |
| `app/services/document_service.py` | Upload logic, validation, file storage |
| `app/services/document_repository.py` | Database CRUD operations |
| `app/models/document.py` | SQLAlchemy `Document` model |
| `app/schemas/document.py` | Pydantic request/response schemas |
| `app/core/config.py` | Application settings from `.env` |

### Document Lifecycle

```
Upload → Validate → Store on Disk → Save to DB (status: "pending")
                                     → Trigger Processing Pipeline
                                     → Update status: "completed" / "failed"
```

---

## Phase 2 — Text Extraction & OCR

### What It Does

- Extracts text from PDF documents using **PyMuPDF** (native PDF extraction)
- Falls back to **Tesseract OCR** for image-based PDFs or image uploads
- Preserves **page-level information** (each page's text stored separately)
- Cleans and normalizes extracted text (whitespace, encoding issues)
- Stores extracted content in `document_contents` and `document_pages` tables

### Extraction Strategy

| Document Type | Method | Details |
|---------------|--------|---------|
| Native PDF (text-based) | PyMuPDF `page.get_text()` | Fast, preserves formatting |
| Scanned PDF (image-based) | PyMuPDF renders page → Tesseract OCR | Slower, depends on scan quality |
| Image files (PNG, JPG, TIFF) | Tesseract OCR directly | Single-page extraction |

### Key Files

| File | Purpose |
|------|---------|
| `app/processing/pipeline.py` | Orchestrates the full processing pipeline |
| `app/processing/pdf_processor.py` | PDF text + layout extraction (PyMuPDF) |
| `app/processing/ocr_service.py` | Tesseract OCR wrapper |
| `app/processing/document_extractor.py` | Routing logic: PDF vs image |
| `app/processing/text_cleaner.py` | Text normalization and cleaning |
| `app/processing/page_storage.py` | Saves page data to database |
| `app/models/document_content.py` | SQLAlchemy `DocumentContent` model |
| `app/models/document_page.py` | SQLAlchemy `DocumentPage` model |

---

## Phase 3 — Layout Extraction & Bounding Boxes

### What It Does

- Extracts **structural layout blocks** from each PDF page (headings, paragraphs, tables, lists)
- Preserves **bounding box coordinates** for each text block (`x0, y0, x1, y1`)
- Renders each page as a **200 DPI image** and stores it
- Scales coordinates from PDF space (72 DPI) to image space (200 DPI)
- Stores layout data as structured JSON in the `document_pages` table

### Layout Block Structure

Each block contains:

```json
{
    "block_index": 0,
    "type": "text",
    "bbox": {
        "x0": 100.5,
        "y0": 72.0,
        "x1": 500.3,
        "y1": 96.8
    },
    "text": "Invoice Number: INV-2026-001",
    "line_count": 1,
    "word_count": 3
}
```

### Coordinate System

| Property | Value |
|----------|-------|
| Origin | Top-left corner `(0, 0)` |
| Units | Pixels (at 200 DPI) |
| Image DPI | 200 |
| Scale Factor | `200 / 72 = 2.778` (from PDF points to pixels) |

### Key Files

| File | Purpose |
|------|---------|
| `app/processing/pdf_processor.py` | Layout extraction via PyMuPDF `page.get_text("dict")` |
| `app/processing/pipeline.py` | Integrates layout extraction into page processing |
| `app/models/document_page.py` | Stores `layout_data` JSON column |

---

## Phase 4 — Document Classification

### What It Does

Automatically determines the type of every uploaded document using a trained **TF-IDF + Logistic Regression** classifier.

**Supported classes:** `invoice`, `purchase_order`, `other` (expandable to `receipt`, `bank_statement`, `insurance`)

### Why TF-IDF + Logistic Regression First?

This serves as the **production baseline** before introducing deep learning models:

| Advantage | Details |
|-----------|---------|
| **Fast training** | Seconds, not hours |
| **Fast inference** | Microseconds per prediction |
| **No GPU required** | Runs on any machine |
| **Interpretable** | Inspect which words drive predictions |
| **Strong baseline** | 85–95% accuracy on text classification |

### How the Pipeline Works

```
Document Upload
    │
    ▼
Text Extraction (Phase 2)
    │
    ▼
Layout Extraction (Phase 3)
    │
    ▼
Text Preprocessing
  • Lowercase
  • Normalize whitespace
  • Remove noise (URLs, emails, headers)
  • Preserve financial tokens (amounts, dates, GST, PO refs)
    │
    ▼
TF-IDF Vectorization
  • Max 10,000 features
  • Unigrams + bigrams
  • Sublinear TF scaling
    │
    ▼
Logistic Regression Prediction
  • predict_proba() → class probabilities
  • Highest probability → document_type
  • If confidence < threshold → "unclassified"
    │
    ▼
Store Results in Database
  • document_type
  • classification_confidence
  • classified_at
```

### Training the Classifier

#### Step 1 — Prepare Training Data

Organize labeled text files:

```
data/classification/
├── invoice/
│   ├── doc_0001.txt
│   └── ...
├── purchase_order/
│   └── ...
└── other/
    └── ...
```

Or use the dataset preparation script with a CSV:

```bash
cd backend
venv\Scripts\activate
python scripts/prepare_classification_data.py --csv ../data/company-document-text.csv --output ../data/classification
```

#### Step 2 — Train the Model

**Basic training (default settings):**

```bash
python -m app.ml.classification.trainer --data-dir ../data/classification --output-dir ../ml/artifacts/classification
```

**With larger test set (30%):**

```bash
python -m app.ml.classification.trainer --data-dir ../data/classification --output-dir ../ml/artifacts/classification --test-size 0.3
```

**With stratified 5-fold cross-validation:**

```bash
python -m app.ml.classification.trainer --data-dir ../data/classification --output-dir ../ml/artifacts/classification --k-fold 5
```

**With regularization tuning:**

```bash
python -m app.ml.classification.trainer --data-dir ../data/classification --output-dir ../ml/artifacts/classification --C 0.1 --penalty l2
```

**With shuffled-label baseline (chance performance estimate):**

```bash
python -m app.ml.classification.trainer --data-dir ../data/classification --output-dir ../ml/artifacts/classification --shuffle-baseline
```

**With external validation data:**

```bash
python -m app.ml.classification.trainer --data-dir ../data/classification --output-dir ../ml/artifacts/classification --external-data-dir ../data/external_classification
```

**Combined (all options):**

```bash
python -m app.ml.classification.trainer --data-dir ../data/classification --output-dir ../ml/artifacts/classification --k-fold 5 --C 0.2 --penalty elasticnet --shuffle-baseline
```

#### Trainer CLI Reference

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `--data-dir` | `str` | *required* | Path to labeled training data |
| `--output-dir` | `str` | *required* | Path to save model artifacts |
| `--test-size` | `float` | `0.2` | Test split fraction |
| `--max-features` | `int` | `10000` | Max TF-IDF vocabulary size |
| `--random-state` | `int` | `42` | Random seed |
| `--k-fold` | `int` | `0` | If >1, perform stratified K-Fold CV |
| `--C` | `float` | `1.0` | Inverse regularization strength |
| `--penalty` | `str` | `l2` | Penalty term (`l1`, `l2`, `elasticnet`, `none`) |
| `--shuffle-baseline` | flag | `false` | Train on shuffled labels for chance estimate |
| `--external-data-dir` | `str` | `""` | Path to external validation dataset |

#### Step 3 — Model Artifacts

After training, the following files are saved to `ml/artifacts/classification/`:

| File | Description |
|------|-------------|
| `vectorizer.joblib` | Fitted TF-IDF vectorizer |
| `classifier.joblib` | Trained Logistic Regression model |
| `metadata.json` | Class labels, metrics, training configuration |

### How Confidence Works

The classifier returns `predict_proba()` — the probability distribution across all classes. The highest probability becomes the confidence score.

```json
{
    "document_type": "invoice",
    "classification_confidence": 0.94
}
```

If `confidence < CLASSIFICATION_CONFIDENCE_THRESHOLD` (default 0.5) → `document_type = "unclassified"`.

### Evaluation Results

| Experiment | Accuracy | F1 (macro) | Notes |
|------------|----------|------------|-------|
| Default (`C=1.0`, `l2`, `test_size=0.2`) | 1.0 | 1.0 | Classes well-separated in Kaggle dataset |
| Larger test set (`test_size=0.3`) | 1.0 | 1.0 | Not a small-sample fluke |
| L1 penalty (`C=0.1`, `l1`) | 0.985 | 0.986 | Sparse features, more realistic |
| 5-fold CV (`k-fold=5`) | 1.0 | 1.0 | Consistent across all folds |
| **Shuffled baseline** | **0.306** | **0.306** | ≈ random chance (1/3) — confirms real signal |

### Limitations

- **Text only** — does not use visual layout or image features
- **Vocabulary dependent** — new domain-specific terms may need retraining
- **Linear model** — cannot capture complex non-linear patterns
- **No transfer learning** — each domain needs its own training data

### Future Model Comparison

| Model | Text | Layout | Image | Training Time | Expected Accuracy |
|-------|------|--------|-------|---------------|-------------------|
| TF-IDF + LR *(current)* | ✅ | ❌ | ❌ | Seconds | 85–95% |
| BERT | ✅ | ❌ | ❌ | Hours | 90–97% |
| DistilBERT | ✅ | ❌ | ❌ | ~1 Hour | 88–95% |
| LayoutLMv3 | ✅ | ✅ | ✅ | Hours | 93–98% |

### Key Files (Phase 4)

| File | Purpose |
|------|---------|
| `app/ml/classification/preprocessing.py` | Text preprocessing for TF-IDF |
| `app/ml/classification/predictor.py` | Loads model, predicts document type |
| `app/ml/classification/trainer.py` | Training script with CV, regularization, baselines |
| `app/ml/classification/metrics.py` | Accuracy, precision, recall, F1, confusion matrix |
| `app/services/classification_service.py` | Integrates classifier into processing pipeline |
| `app/services/document_processing_service.py` | Orchestrates extraction → classification |
| `scripts/prepare_classification_data.py` | Converts CSV datasets to training directory |
| `tests/test_classification.py` | 22 unit tests for classification module |

---

## Testing

### Run All Tests

```bash
cd backend
venv\Scripts\activate
python -m pytest tests/ -v
```

### Run Specific Test Files

```bash
# Classification tests (22 tests)
python -m pytest tests/test_classification.py -v

# Layout extraction tests (13 tests)
python -m pytest tests/test_layout_extraction.py -v

# Document service tests
python -m pytest tests/test_document_service.py -v

# PDF processing tests
python -m pytest tests/test_pdf.py -v

# OCR tests
python -m pytest tests/test_ocr.py -v
```

### Test Coverage

| Test File | Tests | Covers |
|-----------|-------|--------|
| `test_classification.py` | 22 | Preprocessing, metrics, predictor |
| `test_layout_extraction.py` | 13 | Layout blocks, bounding boxes, coordinate scaling |
| `test_document_service.py` | — | Document upload and retrieval |
| `test_pdf.py` | — | PDF text extraction |
| `test_ocr.py` | — | Tesseract OCR integration |
| `test_extractor.py` | — | Document extractor routing |

---

## Project Structure

```
Nexora/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── document_routes.py         — FastAPI route handlers
│   │   ├── core/
│   │   │   ├── config.py                  — Settings from .env
│   │   │   └── logging.py                — Logging configuration
│   │   ├── database/
│   │   │   └── session.py                 — SQLAlchemy engine & session
│   │   ├── ml/
│   │   │   └── classification/
│   │   │       ├── preprocessing.py       — Text preprocessing for TF-IDF
│   │   │       ├── predictor.py           — Model loading & prediction
│   │   │       ├── trainer.py             — Training script (CLI)
│   │   │       └── metrics.py             — Evaluation metrics
│   │   ├── models/
│   │   │   ├── document.py                — Document model
│   │   │   ├── document_content.py        — DocumentContent model
│   │   │   └── document_page.py           — DocumentPage model
│   │   ├── processing/
│   │   │   ├── pipeline.py                — Processing orchestrator
│   │   │   ├── pdf_processor.py           — PDF extraction + layout
│   │   │   ├── ocr_service.py             — Tesseract OCR wrapper
│   │   │   ├── document_extractor.py      — PDF vs image routing
│   │   │   ├── text_cleaner.py            — Text normalization
│   │   │   ├── page_storage.py            — Page data persistence
│   │   │   └── result.py                  — Processing result model
│   │   ├── schemas/
│   │   │   └── document.py                — Pydantic schemas
│   │   ├── services/
│   │   │   ├── document_service.py        — Document CRUD logic
│   │   │   ├── document_processing_service.py — Processing orchestration
│   │   │   ├── classification_service.py  — Classification integration
│   │   │   ├── document_repository.py     — Document DB operations
│   │   │   ├── document_content_repository.py — Content DB operations
│   │   │   └── document_page_repository.py — Page DB operations
│   │   ├── utils/
│   │   │   └── ...                        — Utility helpers
│   │   └── main.py                        — FastAPI application entry
│   ├── alembic/
│   │   ├── versions/                      — Database migration scripts
│   │   └── env.py                         — Alembic configuration
│   ├── scripts/
│   │   └── prepare_classification_data.py — Dataset preparation utility
│   ├── tests/
│   │   ├── test_classification.py         — Classification unit tests
│   │   ├── test_layout_extraction.py      — Layout extraction tests
│   │   ├── test_document_service.py       — Service tests
│   │   ├── test_pdf.py                    — PDF processing tests
│   │   ├── test_ocr.py                    — OCR tests
│   │   └── test_extractor.py              — Extractor tests
│   ├── requirements.txt                   — Python dependencies
│   └── .env                               — Environment variables
├── ml/
│   └── artifacts/
│       └── classification/                — Trained model files
│           ├── vectorizer.joblib
│           ├── classifier.joblib
│           └── metadata.json
├── data/
│   └── classification/                    — Training data
│       ├── invoice/                       — Invoice text files
│       ├── purchase_order/                — PO text files
│       └── other/                         — Other document text files
├── frontend/                              — React dashboard (Phase 9)
├── docker/                                — Docker configuration
├── docker-compose.yml                     — Container orchestration
├── .gitignore
└── README.md
```

---

## Roadmap

| Phase | Description | Status |
|-------|-------------|--------|
| Phase 1 | Document ingestion & safe storage | ✅ |
| Phase 2 | Text extraction (native PDF + OCR) | ✅ |
| Phase 3 | Layout extraction & bounding boxes | ✅ |
| Phase 4 | Document classification (TF-IDF baseline) | ✅ |
| Phase 5 | Structured information extraction (key-value pairs) | 🔜 |
| Phase 6 | LayoutLMv3 document understanding | 🔜 |
| Phase 7 | Business rule validation | 🔜 |
| Phase 8 | Duplicate & anomaly detection | 🔜 |
| Phase 9 | React dashboard | 🔜 |
| Phase 10 | Semantic search & RAG-based Q&A | 🔜 |
| Phase 11 | Human-in-the-loop review | 🔜 |

---

## License

This project is private and proprietary.
