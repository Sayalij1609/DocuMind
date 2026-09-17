"""
CLI Script to train or bootstrap the Document Anomaly Detection Isolation Forest model.

Usage:
    # 1. Train directly on the dataset CSV (extracts features on real invoices):
    python scripts/train_anomaly.py --csv ../data/company-document-text.csv

    # 2. Train on completed documents in database (requires at least 10 documents):
    python scripts/train_anomaly.py

    # 3. Bootstrap with synthetic baseline if you don't have enough DB documents yet:
    python scripts/train_anomaly.py --bootstrap
"""

import argparse
import csv
import logging
import os
import sys

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.anomaly.base import FeatureVector
from app.anomaly.features import DocumentFeatureExtractor, FEATURE_NAMES
from app.anomaly.isolation_forest import IsolationForestDetector
from app.anomaly.service import AnomalyDetectionService
from app.core.config import settings
from app.database.session import SessionLocal
from app.ml.extraction.invoice_extractor import InvoiceExtractor
from app.validation.base import ValidationEngine
from app.validation.rules import create_invoice_validation_rules


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("train_anomaly")


def train_from_csv(
    csv_path: str,
    output_path: str,
    contamination: float = 0.05,
    min_samples: int = 10,
    max_samples: int = 1000,
):
    """Train Isolation Forest directly on invoices from a dataset CSV.

    Processes raw text documents through Nexora's Extraction and
    Validation pipelines to produce authentic feature vectors.
    """
    if not os.path.exists(csv_path):
        logger.error("Dataset CSV file not found at: %s", csv_path)
        sys.exit(1)

    logger.info("Reading dataset from: %s", csv_path)
    extractor = InvoiceExtractor()
    validation_engine = ValidationEngine(create_invoice_validation_rules())
    feature_extractor = DocumentFeatureExtractor()

    feature_vectors: list[FeatureVector] = []
    skipped = 0

    with open(csv_path, mode="r", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            label = (row.get("label") or "").strip().lower()
            text = (row.get("text") or "").strip()

            if not text:
                continue

            # Target invoices (and related billing documents)
            if "invoice" not in label and "order" not in label:
                continue

            try:
                # 1. Structured extraction via Phase 5 InvoiceExtractor
                extraction_res = extractor.extract(text)
                fields_dict = {
                    k: {"value": v.value}
                    for k, v in extraction_res.fields.items()
                }

                # 2. Validation via Phase 7 ValidationEngine
                val_res = validation_engine.validate(
                    document_id=f"csv-{i}",
                    document_type="invoice",
                    extracted_fields=fields_dict,
                )

                # Mock minimal content & extraction record wrappers
                class ContentMock:
                    cleaned_text = text
                    page_count = 1

                class ExtractionMock:
                    extracted_fields = fields_dict

                class ValidationMock:
                    rule_results = [r.to_dict() for r in val_res.results]

                fv = feature_extractor.extract(
                    document_id=f"csv-{i}",
                    content=ContentMock(),
                    extraction_record=ExtractionMock(),
                    validation_record=ValidationMock(),
                )
                feature_vectors.append(fv)

                if len(feature_vectors) % 100 == 0:
                    logger.info(
                        "Extracted %d invoice feature vectors...",
                        len(feature_vectors),
                    )

                if len(feature_vectors) >= max_samples:
                    logger.info(
                        "Reached training sample limit (%d)",
                        max_samples,
                    )
                    break

            except Exception as e:
                skipped += 1
                if skipped <= 3:
                    logger.warning("Error processing row %d: %s", i, e)

    logger.info(
        "Successfully extracted feature vectors from %d dataset documents (skipped: %d)",
        len(feature_vectors),
        skipped,
    )

    if len(feature_vectors) < min_samples:
        logger.error(
            "Extracted only %d samples, but minimum required is %d",
            len(feature_vectors),
            min_samples,
        )
        sys.exit(1)

    # Fit Isolation Forest
    logger.info("Fitting Isolation Forest model on real dataset features...")
    detector = IsolationForestDetector(
        contamination=contamination,
        min_samples=min_samples,
        model_version="isolation_forest_dataset_v1",
    )
    detector.fit(feature_vectors)

    # Save
    detector.save(output_path)
    logger.info("========================================")
    logger.info("DATASET TRAINING SUCCESSFUL!")
    logger.info("Samples Trained: %d", len(feature_vectors))
    logger.info("Contamination:   %.3f", contamination)
    logger.info("Model Saved To:  %s", os.path.abspath(output_path))
    logger.info("========================================")


def main():
    parser = argparse.ArgumentParser(
        description="Train Nexora Document Anomaly Detection (Isolation Forest)"
    )
    parser.add_argument(
        "--csv",
        type=str,
        default="",
        help="Path to dataset CSV (e.g., ../data/company-document-text.csv)",
    )
    parser.add_argument(
        "--contamination",
        type=float,
        default=settings.anomaly_contamination,
        help="Expected proportion of outliers (default: 0.05)",
    )
    parser.add_argument(
        "--min-samples",
        type=int,
        default=settings.anomaly_min_training_samples,
        help="Minimum completed documents required to train (default: 10)",
    )
    parser.add_argument(
        "--output-path",
        type=str,
        default=settings.anomaly_model_path,
        help=f"Target model path (default: {settings.anomaly_model_path})",
    )
    parser.add_argument(
        "--bootstrap",
        action="store_true",
        help="Force generate and save a synthetic baseline model (for cold-start)",
    )

    args = parser.parse_args()

    # 1. Train from CSV dataset
    if args.csv:
        train_from_csv(
            csv_path=args.csv,
            output_path=args.output_path,
            contamination=args.contamination,
            min_samples=args.min_samples,
        )
        return

    # 2. Synthetic baseline bootstrap
    if args.bootstrap:
        logger.info("Generating synthetic baseline model for cold-start...")
        detector = IsolationForestDetector.create_synthetic_baseline(
            n_samples=60,
            contamination=args.contamination,
        )
        detector.save(args.output_path)
        logger.info(
            "Successfully bootstrapped and saved baseline model to: %s",
            os.path.abspath(args.output_path),
        )
        return

    # 3. Train on historical documents from PostgreSQL
    logger.info("Connecting to database...")
    db = SessionLocal()
    try:
        service = AnomalyDetectionService(
            session=db,
            model_path=args.output_path,
        )
        logger.info(
            "Querying completed documents from database (min required: %d)...",
            args.min_samples,
        )
        result = service.train_on_historical_documents(
            min_samples=args.min_samples,
            contamination=args.contamination,
        )

        if result["status"] == "SUCCESS":
            logger.info("========================================")
            logger.info("TRAINING SUCCESSFUL!")
            logger.info("Samples Trained: %d", result["samples_trained"])
            logger.info("Contamination:   %.3f", result["contamination"])
            logger.info("Saved Model:     %s", os.path.abspath(result["model_path"]))
            logger.info("========================================")
        elif result["status"] == "INSUFFICIENT_DATA":
            logger.warning("========================================")
            logger.warning("COULD NOT TRAIN ON DATABASE RECORDS:")
            logger.warning(result["message"])
            logger.warning(
                "TIP: You can train directly on your CSV dataset using:\n"
                "     python scripts/train_anomaly.py --csv ../data/company-document-text.csv\n"
                "Or bootstrap a synthetic baseline model using:\n"
                "     python scripts/train_anomaly.py --bootstrap"
            )
            logger.warning("========================================")
        else:
            logger.error("Training failed: %s", result)

    finally:
        db.close()


if __name__ == "__main__":
    main()
