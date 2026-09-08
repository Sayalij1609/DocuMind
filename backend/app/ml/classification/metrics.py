"""
Classification evaluation metrics.

Computes accuracy, precision, recall, F1-score,
and confusion matrix for document classification.
"""

from typing import Any

from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)


def compute_metrics(
    y_true: list[str],
    y_pred: list[str],
    labels: list[str] | None = None
) -> dict[str, Any]:
    """
    Compute classification evaluation metrics.

    Args:
        y_true: Ground truth labels.
        y_pred: Predicted labels.
        labels: Ordered list of class labels.

    Returns:
        Dictionary containing:
        - accuracy
        - precision_macro
        - recall_macro
        - f1_macro
        - classification_report (per-class)
        - confusion_matrix
    """

    accuracy = accuracy_score(
        y_true, y_pred
    )

    precision = precision_score(
        y_true, y_pred,
        average="macro",
        zero_division=0
    )

    recall = recall_score(
        y_true, y_pred,
        average="macro",
        zero_division=0
    )

    f1 = f1_score(
        y_true, y_pred,
        average="macro",
        zero_division=0
    )

    report = classification_report(
        y_true, y_pred,
        labels=labels,
        output_dict=True,
        zero_division=0
    )

    matrix = confusion_matrix(
        y_true, y_pred,
        labels=labels
    )

    return {
        "accuracy": round(accuracy, 4),
        "precision_macro": round(precision, 4),
        "recall_macro": round(recall, 4),
        "f1_macro": round(f1, 4),
        "classification_report": report,
        "confusion_matrix": matrix.tolist(),
        "labels": labels or sorted(
            set(y_true) | set(y_pred)
        )
    }
