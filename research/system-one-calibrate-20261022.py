#!/usr/bin/env python3
"""Підібрати скалярну температуру компактного учня лише за validation.

Вхідний seed-корпус мусить мати той самий SHA, що й навчальний корпус моделі.
Test не бере участі у підборі. Вихід — окремий файл моделі з provenance,
температурою, кількістю прикладів та NLL до/після.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
STUDENT_PATH = HERE / "system-one-compact-student-20261022.py"
_spec = importlib.util.spec_from_file_location("system_one_compact_student_for_calibration", STUDENT_PATH)
if _spec is None or _spec.loader is None:
    raise RuntimeError(f"не вдалося завантажити учня: {STUDENT_PATH}")
student = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(student)


class CalibrationError(ValueError):
    """Названа помилка калібрування."""


def dataset_sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def validation_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    result: list[dict[str, Any]] = []
    for row in rows:
        row_id = str(row.get("id", ""))
        if not row_id or row_id in seen:
            raise CalibrationError(f"відсутній або повторений id: {row_id!r}")
        seen.add(row_id)
        split = row.get("split")
        if split not in {"train", "validation", "test"}:
            raise CalibrationError(f"{row_id}: невідомий поділ вибірки {split!r}")
        if row.get("gold") not in student.LABELS:
            raise CalibrationError(f"{row_id}: невідома еталонна мітка")
        if not isinstance(row.get("text"), str) or not row["text"].strip():
            raise CalibrationError(f"{row_id}: відсутній текст")
        if split == "validation":
            result.append(row)
    if not result:
        raise CalibrationError("корпус не містить прикладів validation; test використовувати не можна")
    return result


def negative_log_likelihood(
    model: dict[str, Any],
    rows: list[dict[str, Any]],
    temperature: float,
) -> float:
    if not math.isfinite(temperature) or temperature <= 0:
        raise CalibrationError("температура має бути скінченною та додатною")
    total = 0.0
    for row in rows:
        scores = student.class_scores(model, row["text"])
        scaled = {label: scores[label] / temperature for label in student.LABELS}
        maximum = max(scaled.values())
        log_partition = maximum + math.log(
            sum(math.exp(value - maximum) for value in scaled.values())
        )
        total -= scaled[row["gold"]] - log_partition
    return total / len(rows)


def fit_temperature(
    model: dict[str, Any],
    rows: list[dict[str, Any]],
    source_sha256: str,
    min_temperature: float = 0.05,
    max_temperature: float = 20.0,
    grid_points: int = 501,
) -> tuple[dict[str, Any], dict[str, Any]]:
    if model.get("schema") != student.MODEL_SCHEMA or model.get("classes") != list(student.LABELS):
        raise CalibrationError("несумісна схема моделі")
    trained_sha = model.get("training_dataset_sha256")
    if not isinstance(trained_sha, str) or trained_sha != source_sha256:
        raise CalibrationError(
            "SHA вхідного корпусу не збігається з навчальним SHA моделі; "
            "калібрування іншої вибірки не дозволене цим маршрутом"
        )
    if not math.isfinite(min_temperature) or not math.isfinite(max_temperature):
        raise CalibrationError("межі температури мають бути скінченними")
    if min_temperature <= 0 or max_temperature <= min_temperature:
        raise CalibrationError("потрібно 0 < min-temperature < max-temperature")
    if isinstance(grid_points, bool) or not isinstance(grid_points, int) or not 51 <= grid_points <= 5001:
        raise CalibrationError("grid-points має бути цілим у межах 51..5001")

    holdout = validation_rows(rows)
    log_min = math.log(min_temperature)
    log_max = math.log(max_temperature)
    candidates = [
        math.exp(log_min + index * (log_max - log_min) / (grid_points - 1))
        for index in range(grid_points)
    ]
    candidates.append(1.0)
    # Deduplicate the exact baseline candidate and choose deterministically.
    candidates = sorted(set(candidates))
    scored = [
        (negative_log_likelihood(model, holdout, temperature), temperature)
        for temperature in candidates
    ]
    nll_before = negative_log_likelihood(model, holdout, 1.0)
    nll_after, temperature = min(
        scored,
        key=lambda pair: (pair[0], abs(math.log(pair[1])), pair[1]),
    )
    if nll_after > nll_before + 1e-12:
        # The exact 1.0 candidate must keep calibration from worsening NLL.
        raise CalibrationError("внутрішня помилка: калібрування погіршило NLL")
    fitted = dict(model)
    fitted["calibration_temperature"] = temperature
    fitted["calibration"] = {
        "method": "scalar-temperature-grid-min-nll-v1",
        "temperature": temperature,
        "split": "validation",
        "count": len(holdout),
        "dataset_sha256": source_sha256,
        "nll_before": nll_before,
        "nll_after": nll_after,
        "grid_points": grid_points,
        "range": {
            "minimum": min_temperature,
            "maximum": max_temperature,
        },
        "used_test_split": False,
    }
    report = {
        "result": "temperature-calibrated",
        "model_kind": model.get("model_kind"),
        "temperature": temperature,
        "validation_count": len(holdout),
        "validation_dataset_sha256": source_sha256,
        "nll_before": nll_before,
        "nll_after": nll_after,
        "nll_not_worsened": nll_after <= nll_before + 1e-12,
        "used_test_split": False,
        "calibration_method": fitted["calibration"]["method"],
    }
    return fitted, report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", type=Path, required=True, help="модель після train")
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("research/system-one-support-seed-20261022.jsonl"),
        help="повний seed-корпус із train/validation/test",
    )
    parser.add_argument("--output", type=Path, required=True, help="новий файл каліброваної моделі")
    parser.add_argument("--min-temperature", type=float, default=0.05)
    parser.add_argument("--max-temperature", type=float, default=20.0)
    parser.add_argument("--grid-points", type=int, default=501)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    try:
        model_path = args.model.resolve()
        input_path = args.input.resolve()
        output_path = args.output.resolve()
        if output_path in {model_path, input_path}:
            raise CalibrationError("калібрована модель не може перезаписати модель-джерело або корпус")
        if output_path.exists() and not args.overwrite:
            raise CalibrationError(f"вихід уже існує: {output_path}; додайте --overwrite свідомо")
        model_raw = args.model.read_bytes()
        input_raw = args.input.read_bytes()
        try:
            model = json.loads(model_raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise CalibrationError(f"файл моделі некоректний: {exc}") from exc
        if not isinstance(model, dict):
            raise CalibrationError("корінь файла моделі має бути об'єктом")
        raw_rows, _ = student.read_jsonl(args.input)
        rows = validation_rows(raw_rows)
        source_sha = dataset_sha256(input_raw)
        fitted, report = fit_temperature(
            model,
            raw_rows,
            source_sha,
            min_temperature=args.min_temperature,
            max_temperature=args.max_temperature,
            grid_points=args.grid_points,
        )
        rendered = json.dumps(
            fitted, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ) + "\n"
        student.atomic_write(output_path, rendered, args.overwrite)
        report["model_input_sha256"] = dataset_sha256(model_raw)
        report["calibrated_model_sha256"] = dataset_sha256(rendered.encode("utf-8"))
        report["output"] = str(output_path)
        print(json.dumps(report, ensure_ascii=False, sort_keys=True))
        return 0
    except (OSError, UnicodeDecodeError, CalibrationError, student.StudentError, KeyError, TypeError, ValueError) as exc:
        print(f"помилка калібрування System One: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
