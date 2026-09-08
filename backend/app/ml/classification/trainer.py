"""
Document classification trainer.

Trains a TF-IDF + LogisticRegression classifier
from labeled text files organized in directories.

Directory structure expected:
    data/classification/
    ├── invoice/
    │   ├── doc_0001.txt
    │   └── ...
    ├── purchase_order/
    │   └── ...
    └── other/
        └── ...

Usage:
    cd backend
    python -m app.ml.classification.trainer \
        --data-dir ../data/classification \
        --output-dir ../ml/artifacts/classification

    Optional arguments:
        --test-size 0.2
        --max-features 10000
        --random-state 42
"""

import argparse
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
from sklearn.feature_extraction.text import (
    TfidfVectorizer,
)
from sklearn.linear_model import (
    LogisticRegression,
)
from sklearn.model_selection import (
    train_test_split,
    StratifiedKFold,
)

from app.ml.classification.metrics import (
    compute_metrics,
)
from app.ml.classification.preprocessing import (
    preprocess_for_classification,
)


logger = logging.getLogger(__name__)


def _pick_solver(penalty: str) -> str:
    """Return the best solver for the given penalty.

    - lbfgs  → supports l2 and None
    - saga   → supports l1, l2, elasticnet, and None
    """
    if penalty in ("l1", "elasticnet"):
        return "saga"
    return "lbfgs"


def load_training_data(
    data_dir: str,
    min_text_length: int = 20
) -> tuple[list[str], list[str]]:
    """
    Load labeled text files from a directory.

    Each subdirectory name is the class label.
    Each .txt file in the subdirectory is one
    training sample.

    Args:
        data_dir: Path to classification data
                  directory.
        min_text_length: Minimum text length
                         to include a document.

    Returns:
        Tuple of (texts, labels).
    """

    data_path = Path(data_dir)

    if not data_path.exists():

        raise FileNotFoundError(
            f"Data directory not found: "
            f"{data_dir}"
        )

    texts: list[str] = []
    labels: list[str] = []
    skipped = 0

    class_dirs = sorted([
        d for d in data_path.iterdir()
        if d.is_dir()
        and not d.name.startswith(".")
    ])

    if not class_dirs:

        raise ValueError(
            f"No class directories found "
            f"in {data_dir}"
        )

    for class_dir in class_dirs:

        class_name = class_dir.name

        txt_files = sorted(
            class_dir.glob("*.txt")
        )

        for txt_file in txt_files:

            try:

                text = txt_file.read_text(
                    encoding="utf-8"
                ).strip()

            except UnicodeDecodeError:

                text = txt_file.read_text(
                    encoding="latin-1"
                ).strip()

            if len(text) < min_text_length:
                skipped += 1
                continue

            texts.append(text)
            labels.append(class_name)

    logger.info(
        "Loaded %d documents from %d classes "
        "(skipped %d short documents)",
        len(texts),
        len(class_dirs),
        skipped
    )

    return texts, labels


def train_classifier(
    data_dir: str,
    output_dir: str,
    test_size: float = 0.2,
    max_features: int = 10000,
    random_state: int = 42,
    C: float = 1.0,
    penalty: str = "l2",
    shuffle_baseline: bool = False,
    external_data_dir: str = ""
) -> dict:
    """
    Train a TF-IDF + LogisticRegression classifier.

    Args:
        data_dir: Path to labeled training data.
        output_dir: Path to save model artifacts.
        test_size: Fraction for test split.
        max_features: Max vocabulary size for TF-IDF.
        random_state: Random seed for reproducibility.

    Returns:
        Dictionary with training results and metrics.
    """

    # -------------------------------------------------
    # Load data
    # -------------------------------------------------

    texts, labels = load_training_data(
        data_dir
    )

    if len(texts) == 0:

        raise ValueError(
            "No training data found."
        )

    class_names = sorted(set(labels))

    print(f"Classes: {class_names}")
    print(f"Total documents: {len(texts)}")

    for class_name in class_names:

        count = labels.count(class_name)
        print(f"  {class_name}: {count}")

    # -------------------------------------------------
    # Preprocess
    # -------------------------------------------------

    print("\nPreprocessing texts...")

    preprocessed = [
        preprocess_for_classification(text)
        for text in texts
    ]

    # -------------------------------------------------
    # Train/test split
    # -------------------------------------------------

    X_train, X_test, y_train, y_test = (
        train_test_split(
            preprocessed,
            labels,
            test_size=test_size,
            random_state=random_state,
            stratify=labels
        )
    )

    print(
        f"\nTrain: {len(X_train)} documents"
    )

    print(
        f"Test: {len(X_test)} documents"
    )

    # -------------------------------------------------
    # TF-IDF vectorization
    # -------------------------------------------------

    print("\nFitting TF-IDF vectorizer...")

    vectorizer = TfidfVectorizer(
        max_features=max_features,
        ngram_range=(1, 2),
        min_df=2,
        max_df=0.95,
        sublinear_tf=True
    )

    X_train_tfidf = vectorizer.fit_transform(
        X_train
    )

    X_test_tfidf = vectorizer.transform(
        X_test
    )

    print(
        f"Vocabulary size: "
        f"{len(vectorizer.vocabulary_)}"
    )

    # -------------------------------------------------
    # Train classifier
    # -------------------------------------------------

    print("\nTraining Logistic Regression...")

    classifier = LogisticRegression(
        C=C,
        penalty=penalty if penalty != "none" else None,
        max_iter=1000,
        class_weight="balanced",
        random_state=random_state,
        solver=_pick_solver(penalty),
        l1_ratio=0.5 if penalty == "elasticnet" else None
    )

    classifier.fit(
        X_train_tfidf,
        y_train
    )

    # -------------------------------------------------
    # Evaluate
    # -------------------------------------------------

    print("\nEvaluating...")

    y_pred = classifier.predict(
        X_test_tfidf
    )

    metrics = compute_metrics(
        y_true=y_test,
        y_pred=y_pred,
        labels=class_names
    )

    print(f"\nAccuracy: {metrics['accuracy']}")
    print(f"Precision (macro): "
          f"{metrics['precision_macro']}")
    print(f"Recall (macro): "
          f"{metrics['recall_macro']}")
    print(f"F1 (macro): {metrics['f1_macro']}")

    print(f"\nConfusion Matrix:")
    print(f"Labels: {class_names}")

    for row in metrics["confusion_matrix"]:
        print(f"  {row}")

    # -------------------------------------------------
    # Save artifacts
    # -------------------------------------------------

    output_path = Path(output_dir)

    output_path.mkdir(
        parents=True,
        exist_ok=True
    )

    vectorizer_path = (
        output_path / "vectorizer.joblib"
    )

    classifier_path = (
        output_path / "classifier.joblib"
    )

    metadata_path = (
        output_path / "metadata.json"
    )

    joblib.dump(
        vectorizer,
        vectorizer_path
    )

    joblib.dump(
        classifier,
        classifier_path
    )

    metadata = {
        "model_type": "tfidf_logistic_regression",
        "classes": class_names,
        "training_date": (
            datetime.now(timezone.utc).isoformat()
        ),
        "total_samples": len(texts),
        "train_samples": len(X_train),
        "test_samples": len(X_test),
        "test_size": test_size,
        "max_features": max_features,
        "vocabulary_size": len(
            vectorizer.vocabulary_
        ),
        "random_state": random_state,
        "metrics": {
            "accuracy": metrics["accuracy"],
            "precision_macro": (
                metrics["precision_macro"]
            ),
            "recall_macro": (
                metrics["recall_macro"]
            ),
            "f1_macro": metrics["f1_macro"],
            "confusion_matrix": (
                metrics["confusion_matrix"]
            ),
            "labels": metrics["labels"]
        }
    }

    with open(metadata_path, "w") as f:

        json.dump(
            metadata,
            f,
            indent=2
        )

    print(f"\nModel saved to: {output_path}")
    print(f"  vectorizer: {vectorizer_path}")
    print(f"  classifier: {classifier_path}")
    print(f"  metadata: {metadata_path}")

    return metadata


def main():

    logging.basicConfig(
        level=logging.INFO,
        format=(
            "%(asctime)s | "
            "%(levelname)s | "
            "%(message)s"
        )
    )

    parser = argparse.ArgumentParser(
        description=(
            "Train document classification model"
        )
    )

    parser.add_argument(
        "--data-dir",
        required=True,
        help="Path to labeled training data"
    )

    parser.add_argument(
        "--output-dir",
        required=True,
        help="Path to save model artifacts"
    )

    parser.add_argument(
        "--test-size",
        type=float,
        default=0.2,
        help="Test split fraction (default: 0.2)"
    )

    parser.add_argument(
        "--max-features",
        type=int,
        default=10000,
        help="Max TF-IDF features (default: 10000)"
    )

    parser.add_argument(
        "--random-state",
        type=int,
        default=42,
        help="Random seed (default: 42)"
    )
    parser.add_argument(
        "--k-fold",
        type=int,
        default=0,
        help="If >1, perform stratified K-Fold cross-validation with given number of folds"
    )
    parser.add_argument(
        "--C",
        type=float,
        default=1.0,
        help="Inverse regularization strength for LogisticRegression (default: 1.0)"
    )
    parser.add_argument(
        "--penalty",
        type=str,
        default="l2",
        choices=["l1", "l2", "elasticnet", "none"],
        help="Penalty term for LogisticRegression (default: l2)"
    )
    parser.add_argument(
        "--shuffle-baseline",
        action="store_true",
        help="Train a baseline model with shuffled labels to estimate chance performance"
    )
    parser.add_argument(
        "--external-data-dir",
        type=str,
        default="",
        help="Path to external validation data (same structure as training data)"
    )

    args = parser.parse_args()

    try:
        if args.k_fold and args.k_fold > 1:
            # Stratified K-Fold cross-validation
            texts, labels = load_training_data(args.data_dir)
            texts = np.array(texts)
            labels = np.array(labels)
            skf = StratifiedKFold(n_splits=args.k_fold, shuffle=True, random_state=args.random_state)
            all_metrics = []
            fold_idx = 1
            for train_index, test_index in skf.split(texts, labels):
                print(f"\n=== Fold {fold_idx}/{args.k_fold} ===")
                X_train_raw, X_test_raw = texts[train_index], texts[test_index]
                y_train, y_test = labels[train_index], labels[test_index]
                preprocessed_train = [preprocess_for_classification(t) for t in X_train_raw]
                preprocessed_test = [preprocess_for_classification(t) for t in X_test_raw]
                vectorizer = TfidfVectorizer(
                    max_features=args.max_features,
                    ngram_range=(1, 2),
                    min_df=2,
                    max_df=0.95,
                    sublinear_tf=True,
                )
                X_train_tfidf = vectorizer.fit_transform(preprocessed_train)
                X_test_tfidf = vectorizer.transform(preprocessed_test)
                classifier = LogisticRegression(
                    C=args.C,
                    penalty=args.penalty if args.penalty != "none" else None,
                    max_iter=1000,
                    class_weight="balanced",
                    random_state=args.random_state,
                    solver=_pick_solver(args.penalty),
                    l1_ratio=0.5 if args.penalty == "elasticnet" else None,
                )
                classifier.fit(X_train_tfidf, y_train)
                y_pred = classifier.predict(X_test_tfidf)
                fold_metrics = compute_metrics(y_test, y_pred, labels=sorted(set(labels)))
                print(f"Fold {fold_idx} metrics: {fold_metrics}")
                all_metrics.append(fold_metrics)
                fold_idx += 1
            # Aggregate metrics (simple mean)
            avg_metrics = {
                k: round(np.mean([m[k] for m in all_metrics if isinstance(m[k], (int, float))]), 4)
                for k in all_metrics[0].keys()
                if k not in ["confusion_matrix", "classification_report", "labels"]
            }
            print("\n=== Average CV Metrics ===")
            print(avg_metrics)
            # Save a dummy metadata with avg metrics
            metadata = {
                "model_type": "tfidf_logistic_regression_cv",
                "classes": sorted(set(labels)),
                "cv_folds": args.k_fold,
                "average_metrics": avg_metrics,
                "training_date": datetime.now(timezone.utc).isoformat(),
            }
            output_path = Path(args.output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            metadata_path = output_path / "metadata.json"
            with open(metadata_path, "w") as f:
                json.dump(metadata, f, indent=2)
            print(f"\nCV metadata saved to: {metadata_path}")
        else:
            # Standard train-test split training
            train_classifier(
                data_dir=args.data_dir,
                output_dir=args.output_dir,
                test_size=args.test_size,
                max_features=args.max_features,
                random_state=args.random_state,
                C=args.C,
                penalty=args.penalty,
                shuffle_baseline=args.shuffle_baseline,
                external_data_dir=args.external_data_dir
            )

        # Optional shuffled baseline evaluation
        if args.shuffle_baseline:
            print("\n=== Shuffled Baseline Evaluation ===")
            # Load data again
            texts, labels = load_training_data(args.data_dir)
            shuffled_labels = labels.copy()
            np.random.seed(args.random_state)
            np.random.shuffle(shuffled_labels)
            # Use same split as before for fairness
            X_train, X_test, y_train, y_test = train_test_split(
                [preprocess_for_classification(t) for t in texts],
                shuffled_labels,
                test_size=args.test_size,
                random_state=args.random_state,
                stratify=shuffled_labels,
            )
            vectorizer = TfidfVectorizer(
                max_features=args.max_features,
                ngram_range=(1, 2),
                min_df=2,
                max_df=0.95,
                sublinear_tf=True,
            )
            X_train_tfidf = vectorizer.fit_transform(X_train)
            X_test_tfidf = vectorizer.transform(X_test)
            baseline_clf = LogisticRegression(
                C=args.C,
                penalty=args.penalty if args.penalty != "none" else None,
                max_iter=1000,
                class_weight="balanced",
                random_state=args.random_state,
                solver=_pick_solver(args.penalty),
                l1_ratio=0.5 if args.penalty == "elasticnet" else None,
            )
            baseline_clf.fit(X_train_tfidf, y_train)
            y_pred_baseline = baseline_clf.predict(X_test_tfidf)
            baseline_metrics = compute_metrics(y_test, y_pred_baseline, labels=sorted(set(labels)))
            print(f"Baseline (shuffled) metrics: {baseline_metrics}")

        # External validation if provided
        if args.external_data_dir:
            print("\n=== External Validation ===")
            ext_texts, ext_labels = load_training_data(args.external_data_dir)
            ext_preprocessed = [preprocess_for_classification(t) for t in ext_texts]
            # Load the previously trained model artifacts
            vectorizer_path = Path(args.output_dir) / "vectorizer.joblib"
            classifier_path = Path(args.output_dir) / "classifier.joblib"
            if not vectorizer_path.exists() or not classifier_path.exists():
                raise FileNotFoundError("Model artifacts not found for external validation.")
            vectorizer = joblib.load(vectorizer_path)
            classifier = joblib.load(classifier_path)
            X_ext = vectorizer.transform(ext_preprocessed)
            y_ext_pred = classifier.predict(X_ext)
            ext_metrics = compute_metrics(ext_labels, y_ext_pred, labels=sorted(set(ext_labels)))
            print(f"External validation metrics: {ext_metrics}")

    except Exception as exc:
        print(f"\nTraining failed: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
