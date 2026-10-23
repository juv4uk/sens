#!/usr/bin/env python3
"""Оцінити розподіли System One на окремому validation або test наборі.

Скрипт лише вимірює прогнози, він не навчає модель і не змінює поріг.
За замовчуванням приймає тільки split=test; validation треба вказати явно.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import sys
import tempfile
from fractions import Fraction
from pathlib import Path
from typing import Any

LABELS = ("оплата", "доставка", "технічне", "обліковий-запис", "невизначено")


class EvaluationError(ValueError):
    """Named validation failure."""


def read_rows(path: Path) -> list[dict[str, Any]]:
    raw = path.read_bytes()
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(raw.decode("utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError as exc:
            raise EvaluationError(f"{path}:{line_number}: некоректний JSON: {exc}") from exc
        if not isinstance(item, dict):
            raise EvaluationError(f"{path}:{line_number}: запис має бути об'єктом")
        rows.append(item)
    if not rows:
        raise EvaluationError(f"{path}: набір порожній")
    return rows


def as_fraction(value: Any, row_id: str, label: str) -> Fraction:
    if isinstance(value, dict):
        numerator = value.get("numerator")
        denominator = value.get("denominator")
        if (
            isinstance(numerator, bool)
            or not isinstance(numerator, int)
            or isinstance(denominator, bool)
            or not isinstance(denominator, int)
            or denominator <= 0
        ):
            raise EvaluationError(f"{row_id}: некоректна точна частка для {label}")
        result = Fraction(numerator, denominator)
    elif isinstance(value, bool) or not isinstance(value, (int, float)):
        raise EvaluationError(f"{row_id}: відсутня числова ймовірність для {label}")
    else:
        if not math.isfinite(float(value)):
            raise EvaluationError(f"{row_id}: нескінченна/нечислова ймовірність для {label}")
        result = Fraction(str(value))
    if result < 0 or result > 1:
        raise EvaluationError(f"{row_id}: ймовірність поза [0,1] для {label}")
    return result


def extract_distribution(row: dict[str, Any]) -> dict[str, Fraction]:
    row_id = str(row.get("id", "<без id>"))
    raw = row.get("teacher_distribution", row.get("distribution"))
    if not isinstance(raw, dict):
        raise EvaluationError(f"{row_id}: немає teacher_distribution або distribution")
    missing = [label for label in LABELS if label not in raw]
    extra = [label for label in raw if label not in LABELS]
    if missing or extra:
        raise EvaluationError(
            f"{row_id}: неповний/зайвий набір класів; відсутні={missing}, зайві={extra}"
        )
    distribution = {label: as_fraction(raw[label], row_id, label) for label in LABELS}
    if sum(distribution.values(), Fraction(0, 1)) != 1:
        raise EvaluationError(f"{row_id}: сума ймовірностей не дорівнює точно 1")
    return distribution


def score(rows: list[dict[str, Any]], threshold: float, bins: int, expected_split: str) -> dict[str, Any]:
    if not 0 <= threshold <= 1 or not math.isfinite(threshold):
        raise EvaluationError("поріг має бути скінченним числом у [0,1]")
    if bins < 1 or bins > 100:
        raise EvaluationError("кількість кошиків калібрування має бути в межах 1..100")

    confusion = {gold: {pred: 0 for pred in LABELS} for gold in LABELS}
    correct = 0
    brier_sum = 0.0
    ece_bins = [{"count": 0, "confidence_sum": 0.0, "correct": 0} for _ in range(bins)]
    accepted = 0
    accepted_errors = 0
    top_confidences: list[float] = []
    seen_ids: set[str] = set()
    splits: set[str] = set()
    teachers: set[str] = set()
    datasets: set[str] = set()

    for row in rows:
        row_id = str(row.get("id", ""))
        if not row_id or row_id in seen_ids:
            raise EvaluationError(f"відсутній або повторений id: {row_id!r}")
        seen_ids.add(row_id)
        split = row.get("split")
        splits.add(str(split))
        if split != expected_split:
            raise EvaluationError(
                f"{row_id}: очікувався split={expected_split!r}, отримано {split!r}"
            )
        gold = row.get("gold")
        if gold not in LABELS:
            raise EvaluationError(f"{row_id}: невідома еталонна мітка {gold!r}")
        distribution = extract_distribution(row)
        predicted = max(LABELS, key=lambda label: (distribution[label], -LABELS.index(label)))
        confidence = float(distribution[predicted])
        is_correct = predicted == gold
        confusion[gold][predicted] += 1
        correct += int(is_correct)
        top_confidences.append(confidence)
        brier_sum += sum(
            (float(distribution[label]) - (1.0 if label == gold else 0.0)) ** 2
            for label in LABELS
        )

        bin_index = min(int(confidence * bins), bins - 1)
        ece_bins[bin_index]["count"] += 1
        ece_bins[bin_index]["confidence_sum"] += confidence
        ece_bins[bin_index]["correct"] += int(is_correct)

        if confidence >= threshold:
            accepted += 1
            accepted_errors += int(not is_correct)

        if row.get("teacher"):
            teachers.add(str(row["teacher"]))
        if row.get("dataset_sha256"):
            datasets.add(str(row["dataset_sha256"]))

    count = len(rows)
    per_class: dict[str, dict[str, float | int]] = {}
    f1_values: list[float] = []
    for label in LABELS:
        tp = confusion[label][label]
        fp = sum(confusion[other][label] for other in LABELS if other != label)
        fn = sum(confusion[label][other] for other in LABELS if other != label)
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        f1 = (2 * precision * recall / (precision + recall)) if precision + recall else 0.0
        f1_values.append(f1)
        per_class[label] = {
            "support": sum(confusion[label].values()),
            "precision": precision,
            "recall": recall,
            "f1": f1,
        }

    ece = 0.0
    bin_report = []
    for index, bucket in enumerate(ece_bins):
        n = bucket["count"]
        avg_confidence = bucket["confidence_sum"] / n if n else None
        accuracy = bucket["correct"] / n if n else None
        if n:
            ece += n / count * abs(accuracy - avg_confidence)
        bin_report.append(
            {
                "lower_inclusive": index / bins,
                "upper_exclusive": (index + 1) / bins if index < bins - 1 else 1.0,
                "count": n,
                "accuracy": accuracy,
                "mean_top_confidence": avg_confidence,
            }
        )

    return {
        "status": "measured",
        "count": count,
        "split": expected_split,
        "classes": list(LABELS),
        "threshold": threshold,
        "metrics": {
            "accuracy": correct / count,
            "macro_f1": sum(f1_values) / len(f1_values),
            "multiclass_brier_sum_over_examples": brier_sum / count,
            "top_class_ece": ece,
            "coverage_at_threshold": accepted / count,
            "selective_risk_at_threshold": (accepted_errors / accepted) if accepted else None,
            "accepted": accepted,
            "accepted_errors": accepted_errors,
        },
        "per_class": per_class,
        "confusion_matrix_gold_rows_predicted_columns": confusion,
        "calibration_bins": bin_report,
        "teacher_models": sorted(teachers),
        "dataset_sha256_values": sorted(datasets),
        "interpretation": {
            "probability_is_not_truth": True,
            "threshold_must_be_selected_on_validation": True,
            "brier_definition": "mean over examples of the sum of squared errors over all five classes",
            "ece_definition": "equal-width bins over maximum class probability; weighted absolute gap between bin accuracy and mean confidence",
        },
    }


def select_threshold(
    rows: list[dict[str, Any]],
    max_selective_risk: float = 0.10,
    min_accepted: int = 5,
    expected_split: str = "validation",
) -> dict[str, Any]:
    """Вибрати поріг лише на validation; якщо безпечного немає — не вигадувати."""
    if expected_split != "validation":
        raise EvaluationError("поріг дозволено добирати лише на split=validation")
    if not math.isfinite(max_selective_risk) or not 0 <= max_selective_risk <= 1:
        raise EvaluationError("max selective risk має бути скінченним у [0,1]")
    if isinstance(min_accepted, bool) or not isinstance(min_accepted, int) or min_accepted < 1:
        raise EvaluationError("min accepted має бути додатним цілим числом")
    if not rows:
        raise EvaluationError("validation набір порожній")
    if min_accepted > len(rows):
        raise EvaluationError("min accepted більший за кількість validation-прикладів")

    risk_limit = Fraction(str(max_selective_risk))
    observed: list[tuple[Fraction, bool, str]] = []
    seen_ids: set[str] = set()
    dataset_hashes: set[str] = set()
    model_hashes: set[str] = set()
    for row in rows:
        row_id = str(row.get("id", ""))
        if not row_id or row_id in seen_ids:
            raise EvaluationError(f"відсутній або повторений id: {row_id!r}")
        seen_ids.add(row_id)
        if row.get("split") != "validation":
            raise EvaluationError(f"{row_id}: поріг добирається лише з validation, отримано {row.get('split')!r}")
        gold = row.get("gold")
        if gold not in LABELS:
            raise EvaluationError(f"{row_id}: невідома еталонна мітка {gold!r}")
        distribution = extract_distribution(row)
        predicted = max(LABELS, key=lambda label: (distribution[label], -LABELS.index(label)))
        confidence = distribution[predicted]
        observed.append((confidence, predicted == gold, row_id))
        if row.get("dataset_sha256"):
            dataset_hashes.add(str(row["dataset_sha256"]))
        elif row.get("input_dataset_sha256"):
            dataset_hashes.add(str(row["input_dataset_sha256"]))
        if row.get("student_model_sha256"):
            model_hashes.add(str(row["student_model_sha256"]))
        elif row.get("model_sha256"):
            model_hashes.add(str(row["model_sha256"]))

    if len(dataset_hashes) > 1:
        raise EvaluationError("validation змішує кілька хешів корпусу")
    if len(model_hashes) > 1:
        raise EvaluationError("validation змішує прогнози кількох моделей")

    candidates: list[dict[str, Any]] = []
    thresholds = sorted({confidence for confidence, _correct, _row_id in observed})
    for threshold in thresholds:
        accepted = [(confidence, correct, row_id) for confidence, correct, row_id in observed if confidence >= threshold]
        accepted_count = len(accepted)
        if accepted_count < min_accepted:
            continue
        errors = sum(not correct for _confidence, correct, _row_id in accepted)
        risk = Fraction(errors, accepted_count)
        if risk <= risk_limit:
            candidates.append(
                {
                    "threshold_fraction": threshold,
                    "accepted": accepted_count,
                    "errors": errors,
                    "risk_fraction": risk,
                }
            )

    common = {
        "selected_for": "validation",
        "validation_count": len(rows),
        "maximum_allowed_selective_risk": {
            "numerator": risk_limit.numerator,
            "denominator": risk_limit.denominator,
        },
        "minimum_accepted": min_accepted,
        "dataset_sha256_values": sorted(dataset_hashes),
        "model_sha256_values": sorted(model_hashes),
        "small_validation_warning": len(rows) < 30,
        "threshold_rule": "maximize accepted validation rows subject to the risk bound; ties choose the higher threshold",
        "challenge_used": False,
        "test_used": False,
    }
    if not candidates:
        return {
            **common,
            "status": "no-safe-threshold",
            "threshold": None,
            "accepted": 0,
            "errors": 0,
            "achieved_selective_risk": None,
            "coverage": {"numerator": 0, "denominator": len(rows)},
            "reason": "no candidate meets both max risk and minimum accepted count",
        }

    best = max(
        candidates,
        key=lambda candidate: (
            candidate["accepted"],
            candidate["threshold_fraction"],
        ),
    )
    threshold = best["threshold_fraction"]
    risk = best["risk_fraction"]
    return {
        **common,
        "status": "selected",
        "threshold": {"numerator": threshold.numerator, "denominator": threshold.denominator},
        "accepted": best["accepted"],
        "errors": best["errors"],
        "achieved_selective_risk": {"numerator": risk.numerator, "denominator": risk.denominator},
        "coverage": {
            "numerator": best["accepted"],
            "denominator": len(rows),
        },
        "reason": None,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True, help="JSONL з teacher_distribution або distribution")
    parser.add_argument("--expected-split", choices=("validation", "test"), default="test")
    parser.add_argument("--mode", choices=("score", "select-threshold"), default="score")
    parser.add_argument("--threshold", type=float, default=0.80, help="тільки для coverage/selective risk")
    parser.add_argument("--max-selective-risk", type=float, default=0.10, help="максимальна частка помилок для mode=select-threshold")
    parser.add_argument("--min-accepted", type=int, default=5, help="мінімум прийнятих validation-прикладів для mode=select-threshold")
    parser.add_argument("--bins", type=int, default=10)
    parser.add_argument("--output", type=Path, help="необов'язковий JSON-звіт; за замовчуванням stdout")
    args = parser.parse_args()
    try:
        raw_bytes = args.input.read_bytes()
        if args.output and args.output.resolve() == args.input.resolve():
            raise EvaluationError("звіт не може перезаписати файл прогнозів")
        rows = read_rows(args.input)
        if args.mode == "select-threshold":
            report = select_threshold(
                rows,
                max_selective_risk=args.max_selective_risk,
                min_accepted=args.min_accepted,
                expected_split=args.expected_split,
            )
        else:
            report = score(rows, args.threshold, args.bins, args.expected_split)
        report["input_path"] = str(args.input)
        report["input_sha256"] = hashlib.sha256(raw_bytes).hexdigest()
        rendered = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            handle = tempfile.NamedTemporaryFile(
                mode="w", encoding="utf-8", newline="\n",
                dir=args.output.parent, prefix=f".{args.output.name}.", suffix=".tmp",
                delete=False,
            )
            temp_path = Path(handle.name)
            try:
                with handle:
                    handle.write(rendered)
                os.replace(temp_path, args.output)
            except Exception:
                temp_path.unlink(missing_ok=True)
                raise
        else:
            sys.stdout.write(rendered)
        return 0
    except (OSError, UnicodeDecodeError, EvaluationError) as exc:
        print(f"помилка оцінювання System One: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
