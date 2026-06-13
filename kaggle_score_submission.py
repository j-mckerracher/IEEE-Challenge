from __future__ import annotations

import argparse
import csv
import json
import math
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path


SUBMISSION_COLUMNS = ("row_id", "failure_probability")
SOLUTION_COLUMNS = ("row_id", "cluster", "label")


@dataclass(frozen=True)
class PredictionRow:
    row_id: str
    cluster: str
    label: int
    probability: float


def read_csv_rows(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ValueError(f"{path} is empty or missing a header row.")
        return list(reader.fieldnames), list(reader)


def require_columns(actual: list[str], required: tuple[str, ...], file_label: str) -> None:
    missing = [column for column in required if column not in actual]
    if missing:
        raise ValueError(f"{file_label} is missing required columns: {missing}")


def parse_label(value: str, row_id: str) -> int:
    normalized = value.strip()
    if normalized not in {"0", "1"}:
        raise ValueError(f"Invalid label for row_id={row_id!r}: expected 0 or 1, got {value!r}")
    return int(normalized)


def parse_probability(value: str, row_id: str) -> float:
    try:
        probability = float(value)
    except ValueError as exc:
        raise ValueError(
            f"Invalid failure_probability for row_id={row_id!r}: {value!r}"
        ) from exc

    if not math.isfinite(probability):
        raise ValueError(f"failure_probability must be finite for row_id={row_id!r}")
    if probability < 0.0 or probability > 1.0:
        raise ValueError(
            f"failure_probability must be between 0 and 1 for row_id={row_id!r}"
        )
    return probability


def load_solution(path: Path) -> dict[str, tuple[str, int]]:
    columns, rows = read_csv_rows(path)
    require_columns(columns, SOLUTION_COLUMNS, "Solution file")

    solution: dict[str, tuple[str, int]] = {}
    for line_number, row in enumerate(rows, start=2):
        row_id = row["row_id"].strip()
        cluster = row["cluster"].strip()
        if not row_id:
            raise ValueError(f"Solution file has blank row_id at line {line_number}.")
        if not cluster:
            raise ValueError(f"Solution file has blank cluster at row_id={row_id!r}.")
        if row_id in solution:
            raise ValueError(f"Solution file contains duplicate row_id={row_id!r}.")
        solution[row_id] = (cluster, parse_label(row["label"], row_id))

    if not solution:
        raise ValueError("Solution file contains no rows.")
    return solution


def load_submission(path: Path) -> dict[str, float]:
    columns, rows = read_csv_rows(path)
    require_columns(columns, SUBMISSION_COLUMNS, "Submission file")

    submission: dict[str, float] = {}
    for line_number, row in enumerate(rows, start=2):
        row_id = row["row_id"].strip()
        if not row_id:
            raise ValueError(f"Submission file has blank row_id at line {line_number}.")
        if row_id in submission:
            raise ValueError(f"Submission file contains duplicate row_id={row_id!r}.")
        submission[row_id] = parse_probability(row["failure_probability"], row_id)

    if not submission:
        raise ValueError("Submission file contains no rows.")
    return submission


def join_rows(
    solution: dict[str, tuple[str, int]], submission: dict[str, float]
) -> list[PredictionRow]:
    expected_ids = set(solution)
    submitted_ids = set(submission)
    missing_ids = sorted(expected_ids - submitted_ids)
    extra_ids = sorted(submitted_ids - expected_ids)

    if missing_ids or extra_ids:
        examples = {
            "missing_examples": missing_ids[:5],
            "extra_examples": extra_ids[:5],
        }
        raise ValueError(
            "Submission row_id values do not match the hidden solution. "
            f"missing={len(missing_ids)}, extra={len(extra_ids)}, examples={examples}"
        )

    joined = []
    for row_id, (cluster, label) in solution.items():
        joined.append(
            PredictionRow(
                row_id=row_id,
                cluster=cluster,
                label=label,
                probability=submission[row_id],
            )
        )
    return joined


def average_precision(labels: list[int], scores: list[float]) -> float:
    """Compute non-interpolated average precision, matching sklearn's AP definition."""
    if len(labels) != len(scores):
        raise ValueError("labels and scores must have the same length.")
    if not labels:
        raise ValueError("Cannot compute average precision on an empty cluster.")

    positives = sum(labels)
    negatives = len(labels) - positives
    if positives == 0 or negatives == 0:
        raise ValueError("Each scored cluster must contain at least one positive and one negative.")

    pairs = sorted(zip(scores, labels), key=lambda item: item[0], reverse=True)
    true_positives = 0
    false_positives = 0
    previous_recall = 0.0
    ap = 0.0
    index = 0

    while index < len(pairs):
        score = pairs[index][0]

        while index < len(pairs) and pairs[index][0] == score:
            if pairs[index][1] == 1:
                true_positives += 1
            else:
                false_positives += 1
            index += 1

        recall = true_positives / positives
        precision = true_positives / (true_positives + false_positives)
        ap += (recall - previous_recall) * precision
        previous_recall = recall

    return ap


def compute_macro_cluster_auprc(rows: list[PredictionRow]) -> dict:
    by_cluster: dict[str, list[PredictionRow]] = defaultdict(list)
    for row in rows:
        by_cluster[row.cluster].append(row)

    if not by_cluster:
        raise ValueError("No clusters found in joined prediction rows.")

    per_cluster = {}
    for cluster in sorted(by_cluster):
        cluster_rows = by_cluster[cluster]
        labels = [row.label for row in cluster_rows]
        probabilities = [row.probability for row in cluster_rows]
        auprc = average_precision(labels, probabilities)
        per_cluster[cluster] = {
            "auprc": auprc,
            "n_rows": len(cluster_rows),
            "n_positive": sum(labels),
            "positive_rate": sum(labels) / len(labels),
        }

    score = sum(metrics["auprc"] for metrics in per_cluster.values()) / len(per_cluster)
    return {
        "score": score,
        "primary_metric": "macro_cluster_auprc",
        "n_clusters": len(per_cluster),
        "per_cluster": per_cluster,
    }


def score(solution_path: Path, submission_path: Path) -> dict:
    solution = load_solution(solution_path)
    submission = load_submission(submission_path)
    rows = join_rows(solution, submission)
    return compute_macro_cluster_auprc(rows)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Score IEEE GSC FRESCO failure-prediction submissions."
    )
    parser.add_argument(
        "--solution",
        required=True,
        type=Path,
        help="Private Kaggle/organizer CSV with row_id, cluster, label.",
    )
    parser.add_argument(
        "--submission",
        required=True,
        type=Path,
        help="Participant CSV with row_id, failure_probability.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print full JSON diagnostics instead of only the numeric score.",
    )
    args = parser.parse_args()

    result = score(args.solution, args.submission)
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"{result['score']:.12f}")


if __name__ == "__main__":
    main()
