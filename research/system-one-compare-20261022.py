#!/usr/bin/env python3
"""Порівняти вчителя, учня за gold і учня з м'якими цілями на тих самих holdout.

Вхідні teacher JSONL треба підготувати окремим локальним запуском збирача
оцінок. До навчання надходить ТІЛЬКИ teacher-train; validation застосовується
для калібрування/вибору порога, test — лише для фінального вимірювання.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import sys
import unicodedata
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent


def load_module(filename: str, module_name: str):
    path = HERE / filename
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"не вдалося завантажити дослідницький модуль {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


student = load_module(
    "system-one-compact-student-20261022.py",
    "system_one_compact_student_for_comparison",
)
calibrator = load_module(
    "system-one-calibrate-20261022.py",
    "system_one_calibrate_for_comparison",
)
evaluator = load_module(
    "system-one-evaluate-20261022.py",
    "system_one_evaluate_for_comparison",
)

LABELS = tuple(student.LABELS)


class ComparisonError(ValueError):
    """Названа помилка порівняльного експерименту."""


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def read_rows(path: Path) -> tuple[list[dict[str, Any]], bytes]:
    try:
        return student.read_jsonl(path)
    except (OSError, UnicodeDecodeError, student.StudentError) as exc:
        raise ComparisonError(str(exc)) from exc


def teacher_decoding_agreement(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Measure whether constrained decoding agrees with the distribution argmax."""
    matches = [
        str(row["teacher_generated_label"]) == str(row["teacher_prediction"])
        for row in rows
    ]
    disagreements = [
        str(row["id"])
        for row, matches_argmax in zip(rows, matches)
        if not matches_argmax
    ]
    count = len(rows)
    return {
        "count": count,
        "agreements": sum(matches),
        "disagreements": len(disagreements),
        "agreement_rate": (sum(matches) / count) if count else None,
        "disagreement_ids": disagreements,
        "interpretation": "generated constrained label compared with argmax of normalized top-logprob distribution",
    }


def validate_teacher_file(
    path: Path,
    expected_rows: list[dict[str, Any]],
    expected_split: str,
    dataset_sha: str,
) -> tuple[list[dict[str, Any]], str, str]:
    rows, _raw = read_rows(path)
    if len(rows) != len(expected_rows):
        raise ComparisonError(
            f"{path}: {len(rows)} записів, очікувалося {len(expected_rows)} для {expected_split}"
        )
    expected = {str(row["id"]): row for row in expected_rows}
    observed: dict[str, dict[str, Any]] = {}
    for row in rows:
        row_id = str(row.get("id", ""))
        if not row_id or row_id in observed:
            raise ComparisonError(f"{path}: відсутній/повторений id {row_id!r}")
        observed[row_id] = row
        if row.get("split") != expected_split:
            raise ComparisonError(f"{row_id}: очікувався split={expected_split!r}")
        if row.get("dataset_sha256") != dataset_sha:
            raise ComparisonError(f"{row_id}: SHA корпусу не збігається")
        if row_id not in expected:
            raise ComparisonError(f"{row_id}: id відсутній у seed-корпусі")
        original = expected[row_id]
        if row.get("gold") != original.get("gold") or row.get("text") != original.get("text"):
            raise ComparisonError(f"{row_id}: teacher-запис змінює еталонну мітку або текст")
        distribution = evaluator.extract_distribution(row)
        probability_winner = max(
            LABELS,
            key=lambda label: (distribution[label], -LABELS.index(label)),
        )
        generated_label = row.get("teacher_generated_label")
        if generated_label not in LABELS:
            raise ComparisonError(f"{row_id}: немає допустимої фактично згенерованої мітки вчителя")
        if row.get("teacher_prediction") != probability_winner:
            raise ComparisonError(f"{row_id}: teacher_prediction не збігається з argmax розподілу")
        expected_agreement = generated_label == probability_winner
        if row.get("generated_label_matches_top_probability") is not expected_agreement:
            raise ComparisonError(f"{row_id}: ознака збігу з argmax не відповідає фактичним міткам")

    if set(observed) != set(expected):
        raise ComparisonError(
            f"{path}: не збігається склад {expected_split}: "
            f"відсутні={sorted(set(expected)-set(observed))}"
        )
    teacher_names = {str(row.get("teacher", "")) for row in rows}
    prompt_versions = {str(row.get("prompt_version", "")) for row in rows}
    if len(teacher_names) != 1 or not next(iter(teacher_names)).strip():
        raise ComparisonError(f"{path}: очікується одна вказана модель-вчитель")
    if len(prompt_versions) != 1 or not next(iter(prompt_versions)).strip():
        raise ComparisonError(f"{path}: очікується одна версія prompt")
    return rows, next(iter(teacher_names)), next(iter(prompt_versions))


def validate_transformer_predictions(
    path: Path,
    expected_rows: list[dict[str, Any]],
    expected_split: str,
    dataset_sha: str,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows, raw = read_rows(path)
    if len(rows) != len(expected_rows):
        raise ComparisonError(
            f"{path}: {len(rows)} трансформерних прогнозів, очікувалося {len(expected_rows)} для {expected_split}"
        )
    expected = {str(row["id"]): row for row in expected_rows}
    observed: dict[str, dict[str, Any]] = {}
    for row in rows:
        row_id = str(row.get("id", ""))
        if not row_id or row_id in observed:
            raise ComparisonError(f"{path}: відсутній або повторений id {row_id!r}")
        observed[row_id] = row
        if row.get("split") != expected_split:
            raise ComparisonError(f"{row_id}: очікувався transformer split={expected_split!r}")
        if row.get("model_schema") != "sens.system-one.transformer-student/1":
            raise ComparisonError(f"{row_id}: невідома схема трансформерного учня")
        if row.get("training_dataset_sha256") != dataset_sha:
            raise ComparisonError(f"{row_id}: transformer train SHA не збігається з seed")
        if row_id not in expected:
            raise ComparisonError(f"{row_id}: transformer ID відсутній у seed")
        source = expected[row_id]
        if row.get("gold") != source.get("gold") or row.get("text") != source.get("text"):
            raise ComparisonError(f"{row_id}: transformer змінив еталонний текст або мітку")
        try:
            evaluator.extract_distribution(row)
        except evaluator.EvaluationError as exc:
            raise ComparisonError(f"{row_id}: недопустимий transformer distribution: {exc}") from exc
        temperature = row.get("calibration_temperature")
        if (
            isinstance(temperature, bool)
            or not isinstance(temperature, (int, float))
            or not math.isfinite(float(temperature))
            or float(temperature) <= 0
        ):
            raise ComparisonError(f"{row_id}: некоректна температура трансформера")

    if set(observed) != set(expected):
        raise ComparisonError(
            f"{path}: не збігається склад transformer {expected_split}: "
            f"відсутні={sorted(set(expected)-set(observed))}"
        )
    model_names = {str(row.get("base_model", "")) for row in rows}
    temperatures = {float(row["calibration_temperature"]) for row in rows}
    if len(model_names) != 1 or not next(iter(model_names)).strip():
        raise ComparisonError(f"{path}: очікується одна модель трансформера")
    if len(temperatures) != 1:
        raise ComparisonError(f"{path}: температура змінюється між прогнозами одного набору")
    return rows, {
        "base_model": next(iter(model_names)),
        "temperature": next(iter(temperatures)),
        "predictions_sha256": sha256(raw),
        "count": len(rows),
    }



def _normalized_text(value: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", value).casefold().split())


def validate_challenge_corpus(
    path: Path, seed_rows: list[dict[str, Any]]
) -> tuple[list[dict[str, Any]], str]:
    """Accept only a clearly marked, disjoint, evaluation-only challenge set."""
    rows, raw = read_rows(path)
    if not rows:
        raise ComparisonError("challenge corpus порожній")
    seed_ids = {str(row["id"]) for row in seed_rows}
    seed_texts = {_normalized_text(str(row["text"])) for row in seed_rows}
    seen_ids: set[str] = set()
    seen_texts: set[str] = set()
    observed_labels: set[str] = set()
    for row in rows:
        row_id = str(row.get("id", ""))
        text = row.get("text")
        gold = row.get("gold")
        if not row_id or row_id in seen_ids or row_id in seed_ids:
            raise ComparisonError(f"challenge має відсутній/повторений або seed ID: {row_id!r}")
        if row.get("split") != "test" or row.get("evaluation_only") is not True:
            raise ComparisonError(f"{row_id}: challenge має бути тільки test з evaluation_only=true")
        if row.get("source") != "synthetic-adversarial-challenge":
            raise ComparisonError(f"{row_id}: невідоме походження challenge-запису")
        if not isinstance(text, str) or not text.strip() or gold not in LABELS:
            raise ComparisonError(f"{row_id}: некоректний текст або еталонна мітка challenge")
        normalized = _normalized_text(text)
        if normalized in seen_texts or normalized in seed_texts:
            raise ComparisonError(f"{row_id}: нормалізований текст повторюється в challenge або seed")
        seen_ids.add(row_id)
        seen_texts.add(normalized)
        observed_labels.add(gold)
    if observed_labels != set(LABELS):
        raise ComparisonError(
            f"challenge має охоплювати всі класи: отримано {sorted(observed_labels)}"
        )
    return rows, sha256(raw)

def write_model(path: Path, model: dict[str, Any], overwrite: bool) -> str:
    rendered = json.dumps(model, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
    student.atomic_write(path, rendered, overwrite=overwrite)
    return sha256(rendered.encode("utf-8"))


def train_model(
    input_path: Path,
    teacher_path: Path | None,
    output_path: Path,
    args: argparse.Namespace,
) -> dict[str, Any]:
    result = student.train(
        argparse.Namespace(
            input=input_path,
            teacher=teacher_path,
            output=output_path,
            smoothing=args.smoothing,
            min_count=args.min_count,
            gold_weight=args.gold_weight if teacher_path is not None else None,
            overwrite=args.overwrite,
        )
    )
    if result != 0:
        raise ComparisonError(f"навчання не вдалося: {output_path}")
    try:
        model = json.loads(output_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ComparisonError(f"немає коректної моделі {output_path}: {exc}") from exc
    return model


def predict_split(
    model_path: Path,
    seed_path: Path,
    split: str,
    output_path: Path,
    overwrite: bool,
) -> list[dict[str, Any]]:
    result = student.predict(
        argparse.Namespace(
            model=model_path,
            input=seed_path,
            split=split,
            output=output_path,
            overwrite=overwrite,
        )
    )
    if result != 0:
        raise ComparisonError(f"прогнозування не вдалося: {model_path} / {split}")
    rows, _ = read_rows(output_path)
    return rows


def evaluate_rows(
    rows: list[dict[str, Any]],
    split: str,
    threshold: float,
    bins: int,
) -> dict[str, Any]:
    return evaluator.score(rows, threshold=threshold, bins=bins, expected_split=split)


def run(args: argparse.Namespace) -> dict[str, Any]:
    seed_path = args.input.resolve()
    teacher_paths = {
        "train": args.teacher_train.resolve(),
        "validation": args.teacher_validation.resolve(),
        "test": args.teacher_test.resolve(),
    }
    output_dir = args.output_dir.resolve()
    policy_max_selective_risk = float(getattr(args, "policy_max_selective_risk", 0.10))
    policy_min_accepted = getattr(args, "policy_min_accepted", 5)
    policy_confidence_level = float(getattr(args, "policy_confidence_level", 0.95))
    if not math.isfinite(policy_max_selective_risk) or not 0.0 <= policy_max_selective_risk <= 1.0:
        raise ComparisonError("policy-max-selective-risk має бути скінченним числом у [0,1]")
    if isinstance(policy_min_accepted, bool) or not isinstance(policy_min_accepted, int) or policy_min_accepted < 1:
        raise ComparisonError("policy-min-accepted має бути додатним цілим числом")
    if not math.isfinite(policy_confidence_level) or not 0.0 < policy_confidence_level < 1.0:
        raise ComparisonError("policy-confidence-level має бути строго між 0 та 1")
    transformer_validation_path = getattr(args, "transformer_validation_predictions", None)
    transformer_test_path = getattr(args, "transformer_test_predictions", None)
    if (transformer_validation_path is None) != (transformer_test_path is None):
        raise ComparisonError("для трансформера потрібно передати обидва файли: validation і test")
    transformer_paths = (
        [transformer_validation_path.resolve(), transformer_test_path.resolve()]
        if transformer_validation_path is not None and transformer_test_path is not None
        else []
    )
    challenge_input_value = getattr(args, "challenge_input", None)
    challenge_teacher_value = getattr(args, "challenge_teacher", None)
    challenge_transformer_value = getattr(args, "challenge_transformer_predictions", None)
    if challenge_input_value is None:
        if challenge_teacher_value is not None or challenge_transformer_value is not None:
            raise ComparisonError("challenge-teacher/transformer не можна передати без challenge-input")
    elif challenge_teacher_value is None:
        raise ComparisonError("для challenge-input обов'язковий окремий challenge-teacher")
    if challenge_input_value is not None and bool(transformer_paths) != (challenge_transformer_value is not None):
        raise ComparisonError("challenge-трансформер має бути поданий тоді й лише тоді, коли трансформер є в базовому порівнянні")
    challenge_paths = []
    if challenge_input_value is not None:
        challenge_paths = [Path(challenge_input_value).resolve(), Path(challenge_teacher_value).resolve()]
        if challenge_transformer_value is not None:
            challenge_paths.append(Path(challenge_transformer_value).resolve())
    input_paths = [seed_path, *teacher_paths.values(), *transformer_paths, *challenge_paths]
    if len(set(input_paths)) != len(input_paths):
        raise ComparisonError("seed, teacher і transformer-файли мають бути різними файлами")
    if any(path == output_dir or output_dir in path.parents for path in input_paths):
        raise ComparisonError("вихідний каталог не може містити seed або вхідні teacher-файли")
    if output_dir.exists() and not output_dir.is_dir():
        raise ComparisonError("output-dir уже існує як файл")
    if output_dir.exists() and any(output_dir.iterdir()) and not args.overwrite:
        raise ComparisonError(f"output-dir не порожній: {output_dir}; додайте --overwrite свідомо")
    output_dir.mkdir(parents=True, exist_ok=True)

    seed_rows, seed_raw = read_rows(seed_path)
    dataset_sha = sha256(seed_raw)
    unique_ids: set[str] = set()
    for row in seed_rows:
        row_id = str(row.get("id", ""))
        if not row_id or row_id in unique_ids:
            raise ComparisonError(f"seed має відсутній або повторений id: {row_id!r}")
        unique_ids.add(row_id)
        if row.get("gold") not in LABELS or not isinstance(row.get("text"), str):
            raise ComparisonError(f"{row_id}: некоректний seed-запис")
        if row.get("split") not in {"train", "validation", "test"}:
            raise ComparisonError(f"{row_id}: невідомий split")

    split_rows = {
        split: [row for row in seed_rows if row["split"] == split]
        for split in ("train", "validation", "test")
    }
    if any(not split_rows[split] for split in split_rows):
        raise ComparisonError("seed має містити непорожні train, validation і test")

    challenge_rows = None
    challenge_sha = None
    challenge_transformer_records = None
    challenge_transformer_report = None
    if challenge_input_value is not None:
        challenge_rows, challenge_sha = validate_challenge_corpus(Path(challenge_input_value), seed_rows)

    # Перевірити готові трансформерні holdout-прогнози ДО будь-якого навчання/запису моделей.
    transformer_records: dict[str, list[dict[str, Any]]] = {}
    transformer_report: dict[str, Any] | None = None
    if transformer_paths:
        transformer_report = {}
        for split, prediction_path in (
            ("validation", transformer_paths[0]),
            ("test", transformer_paths[1]),
        ):
            records, details = validate_transformer_predictions(
                prediction_path, split_rows[split], split, dataset_sha
            )
            transformer_records[split] = records
            transformer_report[split] = details
        if transformer_report["validation"]["base_model"] != transformer_report["test"]["base_model"]:
            raise ComparisonError("validation/test трансформера походять від різних базових моделей")
        if transformer_report["validation"]["temperature"] != transformer_report["test"]["temperature"]:
            raise ComparisonError("validation/test трансформера мають різну температуру")
        if challenge_input_value is not None:
            challenge_transformer_records, challenge_transformer_report = validate_transformer_predictions(
                Path(challenge_transformer_value), challenge_rows, "test", dataset_sha
            )
            if challenge_transformer_report["base_model"] != transformer_report["test"]["base_model"]:
                raise ComparisonError("challenge-трансформер походить від іншої базової моделі")
            if challenge_transformer_report["temperature"] != transformer_report["test"]["temperature"]:
                raise ComparisonError("challenge-трансформер має іншу температуру")

    teacher_records: dict[str, list[dict[str, Any]]] = {}
    teachers: set[str] = set()
    prompt_versions: set[str] = set()
    teacher_file_hashes: dict[str, str] = {}
    for split in ("train", "validation", "test"):
        records, teacher_name, prompt_version = validate_teacher_file(
            teacher_paths[split], split_rows[split], split, dataset_sha
        )
        teacher_records[split] = records
        teachers.add(teacher_name)
        prompt_versions.add(prompt_version)
        teacher_file_hashes[split] = sha256(teacher_paths[split].read_bytes())
    if len(teachers) != 1 or len(prompt_versions) != 1:
        raise ComparisonError("teacher-файли мають походити від однієї моделі та версії prompt")
    teacher_name = next(iter(teachers))
    prompt_version = next(iter(prompt_versions))
    challenge_teacher_records = None
    challenge_teacher_sha = None
    if challenge_input_value is not None:
        challenge_teacher_records, challenge_teacher_name, challenge_prompt_version = validate_teacher_file(
            Path(challenge_teacher_value), challenge_rows, "test", challenge_sha
        )
        if challenge_teacher_name != teacher_name or challenge_prompt_version != prompt_version:
            raise ComparisonError("challenge-teacher має походити від тієї самої моделі та версії prompt")
        challenge_teacher_sha = sha256(Path(challenge_teacher_value).read_bytes())

    # Model training can see only seed train and teacher train. Holdout observations
    # are used only for measuring the teacher and are never supplied to the trainer.
    gold_model_path = output_dir / "student-gold-uncalibrated.json"
    soft_model_path = output_dir / "student-soft-uncalibrated.json"
    gold_model = train_model(seed_path, None, gold_model_path, args)
    soft_model = train_model(seed_path, teacher_paths["train"], soft_model_path, args)

    model_paths: dict[str, Path] = {}
    calibration_reports: dict[str, Any] = {}
    for kind, raw_model in (("gold", gold_model), ("soft", soft_model)):
        calibrated, calibration_report = calibrator.fit_temperature(
            raw_model,
            seed_rows,
            dataset_sha,
            min_temperature=args.min_temperature,
            max_temperature=args.max_temperature,
            grid_points=args.grid_points,
        )
        calibrated_path = output_dir / f"student-{kind}-calibrated.json"
        write_model(calibrated_path, calibrated, overwrite=args.overwrite)
        model_paths[kind] = calibrated_path
        calibration_reports[kind] = calibration_report

    evaluations: dict[str, dict[str, Any]] = {
        "teacher": {},
        "student_gold": {},
        "student_soft": {},
    }
    policy_validation_records: dict[str, list[dict[str, Any]]] = {"teacher": teacher_records["validation"]}
    policy_test_records: dict[str, list[dict[str, Any]]] = {"teacher": teacher_records["test"]}
    for split in ("validation", "test"):
        evaluations["teacher"][split] = evaluate_rows(
            teacher_records[split], split, args.threshold, args.bins
        )
        for kind, model_path in model_paths.items():
            predictions = predict_split(
                model_path,
                seed_path,
                split,
                output_dir / f"student-{kind}-{split}.jsonl",
                overwrite=args.overwrite,
            )
            target = "student_gold" if kind == "gold" else "student_soft"
            if split == "validation":
                policy_validation_records[target] = predictions
            else:
                policy_test_records[target] = predictions
            evaluations[target][split] = evaluate_rows(
                predictions, split, args.threshold, args.bins
            )

    if transformer_report is not None:
        policy_validation_records["student_transformer"] = transformer_records["validation"]
        policy_test_records["student_transformer"] = transformer_records["test"]
        evaluations["student_transformer"] = {
            split: evaluate_rows(records, split, args.threshold, args.bins)
            for split, records in transformer_records.items()
        }

    comparisons: dict[str, Any] = {}
    metric_keys = (
        "accuracy",
        "macro_f1",
        "multiclass_brier_sum_over_examples",
        "top_class_ece",
        "coverage_at_threshold",
        "selective_risk_at_threshold",
    )
    for split in ("validation", "test"):
        comparisons[split] = {
            model_name: {
                key: result[split]["metrics"][key]
                for key in metric_keys
            }
            for model_name, result in evaluations.items()
        }

    validation_policy_models: dict[str, Any] = {}
    for model_name, validation_records in policy_validation_records.items():
        selection = evaluator.select_threshold(
            validation_records,
            max_selective_risk=policy_max_selective_risk,
            min_accepted=policy_min_accepted,
            expected_split="validation",
            confidence_level=policy_confidence_level,
        )
        selected_threshold = selection["threshold"]
        test_evaluation = None
        if selected_threshold is not None:
            numeric_threshold = selected_threshold["numerator"] / selected_threshold["denominator"]
            test_evaluation = evaluate_rows(
                policy_test_records[model_name], "test", numeric_threshold, args.bins
            )
        validation_policy_models[model_name] = {
            "selection": selection,
            "selected_threshold": selected_threshold,
            "test_evaluation": test_evaluation,
            "test_used_for_selection": False,
        }

    validation_selected_policy = {
        "selection_split": "validation",
        "max_selective_risk": policy_max_selective_risk,
        "minimum_accepted": policy_min_accepted,
        "familywise_confidence_level": policy_confidence_level,
        "test_used_for_threshold_selection": False,
        "challenge_used_for_threshold_selection": False,
        "models": validation_policy_models,
    }

    challenge_report = None
    if challenge_input_value is not None:
        challenge_evaluations: dict[str, dict[str, Any]] = {}
        challenge_policy_records: dict[str, list[dict[str, Any]]] = {"teacher": challenge_teacher_records}
        challenge_evaluations["teacher"] = evaluate_rows(
            challenge_teacher_records, "test", args.threshold, args.bins
        )
        for kind, model_path in model_paths.items():
            records = predict_split(
                model_path,
                Path(challenge_input_value),
                "test",
                output_dir / f"challenge-student-{kind}.jsonl",
                overwrite=args.overwrite,
            )
            challenge_model_name = "student_gold" if kind == "gold" else "student_soft"
            challenge_policy_records[challenge_model_name] = records
            challenge_evaluations[challenge_model_name] = evaluate_rows(
                records, "test", args.threshold, args.bins
            )
        if challenge_transformer_records is not None:
            challenge_policy_records["student_transformer"] = challenge_transformer_records
            challenge_evaluations["student_transformer"] = evaluate_rows(
                challenge_transformer_records, "test", args.threshold, args.bins
            )
        challenge_metric_keys = (
            "accuracy",
            "macro_f1",
            "multiclass_brier_sum_over_examples",
            "top_class_ece",
            "coverage_at_threshold",
            "selective_risk_at_threshold",
        )
        challenge_validation_policy_models: dict[str, Any] = {}
        for model_name, policy_model in validation_policy_models.items():
            selected_threshold = policy_model["selected_threshold"]
            challenge_evaluation = None
            if selected_threshold is not None:
                numeric_threshold = selected_threshold["numerator"] / selected_threshold["denominator"]
                challenge_evaluation = evaluate_rows(
                    challenge_policy_records[model_name], "test", numeric_threshold, args.bins
                )
            challenge_validation_policy_models[model_name] = {
                "selection_status": policy_model["selection"]["status"],
                "selected_threshold": selected_threshold,
                "evaluation": challenge_evaluation,
            }
        challenge_validation_policy = {
            "selected_on": "validation",
            "threshold_selected_on_challenge": False,
            "models": challenge_validation_policy_models,
        }

        challenge_report = {
            "result": "measured",
            "evaluation_only": True,
            "dataset_sha256": challenge_sha,
            "record_count": len(challenge_rows),
            "class_counts": {label: sum(row["gold"] == label for row in challenge_rows) for label in LABELS},
            "teacher_observation_sha256": challenge_teacher_sha,
            "teacher_decoding_agreement": teacher_decoding_agreement(challenge_teacher_records),
            "transformer_predictions_sha256": challenge_transformer_report["predictions_sha256"] if challenge_transformer_report else None,
            "threshold": args.threshold,
            "threshold_selected_on_challenge": False,
            "validation_selected_policy": challenge_validation_policy,
            "test_used_for_training_or_calibration": False,
            "evaluations": challenge_evaluations,
            "comparison": {
                model_name: {key: value["metrics"][key] for key in challenge_metric_keys}
                for model_name, value in challenge_evaluations.items()
            },
            "limitations": [
                "Набір синтетичний і використовується лише як challenge-test.",
                "Поріг має бути зафіксований до перегляду challenge-результатів.",
                "Цей набір не доводить якість на реальних зверненнях.",
            ],
        }

    report = {
        "schema": "sens.system-one.teacher-student-comparison/1",
        "result": "measured",
        "dataset_sha256": dataset_sha,
        "dataset_count_by_split": {split: len(values) for split, values in split_rows.items()},
        "teacher": teacher_name,
        "prompt_version": prompt_version,
        "teacher_observation_sha256": teacher_file_hashes,
        "teacher_decoding_agreement": {
            split: teacher_decoding_agreement(records)
            for split, records in teacher_records.items()
        },
        "teacher_observations_used_for_training": ["train"],
        "validation_used_for_calibration": True,
        "test_used_for_training_or_calibration": False,
        "threshold": args.threshold,
        "validation_selected_policy": validation_selected_policy,
        "calibration": calibration_reports,
        "transformer_student": transformer_report,
        "challenge": challenge_report,
        "evaluations": evaluations,
        "comparison": comparisons,
        "models": {
            "student_gold_sha256": sha256(gold_model_path.read_bytes()),
            "student_soft_sha256": sha256(soft_model_path.read_bytes()),
            "student_gold_calibrated_sha256": sha256(model_paths["gold"].read_bytes()),
            "student_soft_calibrated_sha256": sha256(model_paths["soft"].read_bytes()),
        },
        "limitations": [
            "Початковий seed є синтетичним і малим.",
            "CPU-наївний баєсів учень не є трансформером.",
            "Teacher scores are observations, not gold truth.",
            "Узагальнення на реальні звернення цим seed не доведене.",
        ],
    }
    rendered = json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    student.atomic_write(output_dir / "comparison.json", rendered, overwrite=args.overwrite)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path("research/system-one-support-seed-20261022.jsonl"))
    parser.add_argument("--teacher-train", type=Path, required=True)
    parser.add_argument("--teacher-validation", type=Path, required=True)
    parser.add_argument("--teacher-test", type=Path, required=True)
    parser.add_argument("--transformer-validation-predictions", type=Path)
    parser.add_argument("--transformer-test-predictions", type=Path)
    parser.add_argument("--challenge-input", type=Path, help="необов'язковий незалежний evaluation-only challenge-test")
    parser.add_argument("--challenge-teacher", type=Path, help="окремі вчительські оцінки для challenge-input")
    parser.add_argument("--challenge-transformer-predictions", type=Path, help="прогнози того самого трансформера на challenge-test")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--threshold", type=float, default=0.80, help="фіксований діагностичний поріг")
    parser.add_argument("--policy-max-selective-risk", type=float, default=0.10)
    parser.add_argument("--policy-min-accepted", type=int, default=5)
    parser.add_argument("--policy-confidence-level", type=float, default=0.95, help="сімейний рівень довіри з поправкою Бонферроні")
    parser.add_argument("--bins", type=int, default=10)
    parser.add_argument("--smoothing", type=float, default=1.0)
    parser.add_argument("--min-count", type=int, default=1)
    parser.add_argument("--gold-weight", type=float, default=0.25)
    parser.add_argument("--min-temperature", type=float, default=0.05)
    parser.add_argument("--max-temperature", type=float, default=20.0)
    parser.add_argument("--grid-points", type=int, default=501)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    try:
        if not math.isfinite(args.threshold) or not 0 <= args.threshold <= 1:
            raise ComparisonError("threshold має бути скінченним числом у [0,1]")
        if not isinstance(args.bins, int) or not 1 <= args.bins <= 100:
            raise ComparisonError("bins має бути в межах 1..100")
        report = run(args)
        print(
            json.dumps(
                {
                    "result": report["result"],
                    "dataset_sha256": report["dataset_sha256"],
                    "dataset_count_by_split": report["dataset_count_by_split"],
                    "comparison": report["comparison"],
                    "teacher_decoding_agreement": report["teacher_decoding_agreement"],
                    "validation_selected_policy": {
                        "selection_split": report["validation_selected_policy"]["selection_split"],
                        "test_used_for_threshold_selection": report["validation_selected_policy"]["test_used_for_threshold_selection"],
                        "models": {
                            name: {
                                "selection_status": policy["selection"]["status"],
                                "selected_threshold": policy["selected_threshold"],
                                "test_metrics": (
                                    policy["test_evaluation"]["metrics"]
                                    if policy["test_evaluation"] is not None
                                    else None
                                ),
                            }
                            for name, policy in report["validation_selected_policy"]["models"].items()
                        },
                    },
                    "challenge": (
                        {
                            "dataset_sha256": report["challenge"]["dataset_sha256"],
                            "record_count": report["challenge"]["record_count"],
                            "comparison": report["challenge"]["comparison"],
                        }
                        if report.get("challenge") is not None
                        else None
                    ),
                    "output": str(args.output_dir.resolve() / "comparison.json"),
                },
                ensure_ascii=False,
                sort_keys=True,
            )
        )
        return 0
    except (
        OSError,
        UnicodeDecodeError,
        ComparisonError,
        student.StudentError,
        calibrator.CalibrationError,
        KeyError,
        TypeError,
        ValueError,
    ) as exc:
        print(f"помилка порівняння System One: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
