from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, average_precision_score, confusion_matrix, f1_score, precision_score, recall_score, roc_auc_score, brier_score_loss
from sklearn.model_selection import GroupShuffleSplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from app.services.ranking_features import pair_matrix

DATA_PATH = ROOT / "training" / "data" / "labeled_match_pairs.csv"
ARTIFACT_DIR = ROOT / "backend" / "app" / "models" / "artifacts"
REPORT_DIR = ROOT / "training" / "reports"


def parse_list(value: str) -> list[str]:
    if not value.strip():
        return []
    try:
        parsed = json.loads(value)
        return [str(item) for item in parsed] if isinstance(parsed, list) else []
    except json.JSONDecodeError:
        return [item.strip() for item in value.split("|") if item.strip()]


def load_pairs(path: Path) -> list[dict]:
    rows = []
    with path.open("r", encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        required_columns = {"candidate_id", "job_id", "candidate_text", "job_text", "candidate_skills", "required_skills", "label"}
        missing = required_columns - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"Dataset is missing required columns: {', '.join(sorted(missing))}")
        for line_number, row in enumerate(reader, start=2):
            if not row.get("candidate_text", "").strip() or not row.get("job_text", "").strip():
                raise ValueError(f"Row {line_number} has an empty candidate_text or job_text.")
            label = int(row["label"])
            if label not in {0, 1}:
                raise ValueError(f"Row {line_number}: label must be 0 or 1.")
            rows.append({
                "candidate_id": row["candidate_id"].strip(), "job_id": row["job_id"].strip(),
                "candidate_text": row["candidate_text"], "job_text": row["job_text"],
                "candidate_skills": parse_list(row.get("candidate_skills", "")),
                "required_skills": parse_list(row.get("required_skills", "")),
                "preferred_skills": parse_list(row.get("preferred_skills", "")),
                "candidate_experience": float(row["candidate_experience"]) if row.get("candidate_experience", "").strip() else None,
                "minimum_experience": float(row["minimum_experience"]) if row.get("minimum_experience", "").strip() else 0.0,
                "maximum_experience": float(row["maximum_experience"]) if row.get("maximum_experience", "").strip() else None,
                "education_match": float(row.get("education_match", "0.5") or 0.5),
                "label": label,
            })
    return rows


def ndcg_at_k(groups: list[str], labels: np.ndarray, scores: np.ndarray, k: int = 5) -> float | None:
    values = []
    for group in sorted(set(groups)):
        indices = [index for index, value in enumerate(groups) if value == group]
        if len(indices) < 2:
            continue
        ranked = sorted(indices, key=lambda index: scores[index], reverse=True)[:k]
        ideal = sorted((labels[index] for index in indices), reverse=True)[:k]
        dcg = sum((2 ** labels[index] - 1) / np.log2(position + 2) for position, index in enumerate(ranked))
        idcg = sum((2 ** value - 1) / np.log2(position + 2) for position, value in enumerate(ideal))
        if idcg:
            values.append(dcg / idcg)
    return round(float(np.mean(values)), 4) if values else None


def main() -> int:
    parser = argparse.ArgumentParser(description="Train and evaluate a ResumeIQ role-relevance ranker from human-labelled candidate/job pairs.")
    parser.add_argument("--data", type=Path, default=DATA_PATH)
    parser.add_argument("--test-size", type=float, default=0.2)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--min-samples", type=int, default=50)
    args = parser.parse_args()

    if not args.data.is_file():
        raise SystemExit(f"Dataset not found: {args.data}\nCopy the template to training/data/labeled_match_pairs.csv and add reviewed labels.")
    rows = load_pairs(args.data)
    labels = np.asarray([row["label"] for row in rows], dtype=np.int32)
    groups = np.asarray([row["candidate_id"] for row in rows])
    job_groups = np.asarray([row["job_id"] for row in rows])
    if len(rows) < args.min_samples:
        raise SystemExit(f"Only {len(rows)} labelled pairs found. At least {args.min_samples} are required for this training workflow.")
    if len(set(labels.tolist())) != 2:
        raise SystemExit("The dataset must contain both positive (1) and negative (0) labels.")
    if len(set(groups.tolist())) < 10:
        raise SystemExit("At least 10 distinct candidate_id groups are required for a grouped hold-out split.")

    splitter = GroupShuffleSplit(n_splits=1, test_size=args.test_size, random_state=args.seed)
    train_indices, test_indices = next(splitter.split(np.zeros(len(rows)), labels, groups))
    y_train, y_test = labels[train_indices], labels[test_indices]
    if len(set(y_train.tolist())) != 2 or len(set(y_test.tolist())) != 2:
        raise SystemExit("The grouped split did not preserve both labels in train and test. Add more balanced labelled examples.")

    train_pairs = [rows[index] for index in train_indices]
    test_pairs = [rows[index] for index in test_indices]
    vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=1, max_features=30000, sublinear_tf=True, strip_accents="unicode")
    X_train = pair_matrix(train_pairs, vectorizer, fit=True)
    X_test = pair_matrix(test_pairs, vectorizer, fit=False)
    classifier = LogisticRegression(max_iter=1500, class_weight="balanced", C=0.7, random_state=args.seed)
    classifier.fit(X_train, y_train)
    scores = classifier.predict_proba(X_test)[:, list(classifier.classes_).index(1)]
    predictions = (scores >= 0.5).astype(np.int32)
    metrics = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "dataset": str(args.data), "sample_count": len(rows), "train_count": len(train_indices), "test_count": len(test_indices),
        "candidate_groups": len(set(groups.tolist())), "job_groups_test": len(set(job_groups[test_indices].tolist())),
        "positive_rate": round(float(labels.mean()), 4), "accuracy": round(float(accuracy_score(y_test, predictions)), 4),
        "precision": round(float(precision_score(y_test, predictions, zero_division=0)), 4),
        "recall": round(float(recall_score(y_test, predictions, zero_division=0)), 4),
        "f1": round(float(f1_score(y_test, predictions, zero_division=0)), 4),
        "roc_auc": round(float(roc_auc_score(y_test, scores)), 4),
        "average_precision": round(float(average_precision_score(y_test, scores)), 4),
        "brier_score": round(float(brier_score_loss(y_test, scores)), 4),
        "ndcg_at_5_by_job": ndcg_at_k(job_groups[test_indices].tolist(), y_test, scores, 5),
        "confusion_matrix": confusion_matrix(y_test, predictions).tolist(),
        "split_strategy": "GroupShuffleSplit by candidate_id; candidate identities do not cross train/test.",
        "status": "holdout-evaluated; not automatically promoted",
    }
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    bundle_path = ARTIFACT_DIR / "match_ranker.joblib"
    report_path = REPORT_DIR / "latest_metrics.json"
    joblib.dump({"vectorizer": vectorizer, "classifier": classifier, "metadata": metrics}, bundle_path)
    report_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    print(json.dumps(metrics, indent=2))
    print(f"\nSaved model candidate: {bundle_path}")
    print(f"Saved evaluation report: {report_path}")
    print("Do not enable USE_TRAINED_MODEL until the held-out report has been reviewed and the training data is representative.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
