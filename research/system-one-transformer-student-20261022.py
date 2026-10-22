#!/usr/bin/env python3
"""Необов'язковий багатомовний трансформер-учень System One.

Потрібні PyTorch, Transformers та Accelerate. За замовчуванням використовує
jhu-clsp/mmbert-small. Навчається лише на split=train. Якщо передано --teacher,
використовує м'які оцінки вчителя разом з еталонними мітками; калібрування
температурою навчається тільки на validation. Test ніколи не входить у loss
або добір температури.

Скрипт не звертається до зовнішнього сервісу для прогнозів. Єдина мережа —
завантаження вказаної базової моделі під час train, якщо ваги ще не кешовані.
Локальний сервіс слухає тільки 127.0.0.1.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import shutil
import sys
import tempfile
import unicodedata
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

LABELS = ("оплата", "доставка", "технічне", "обліковий-запис", "невизначено")
LETTERS = "ABCDE"
DENOMINATOR = 1_000_000_000
MODEL_SCHEMA = "sens.system-one.transformer-student/1"
DEFAULT_MODEL = "jhu-clsp/mmBERT-small"
MAX_REQUEST_BYTES = 1 * 1024 * 1024


class TransformerStudentError(ValueError):
    """Названа помилка тренера, моделі або даних."""


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def read_jsonl(path: Path) -> tuple[list[dict[str, Any]], bytes]:
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise TransformerStudentError(f"не вдалося прочитати {path}: {exc}") from exc
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(raw.decode("utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise TransformerStudentError(f"{path}:{line_number}: некоректний JSON: {exc}") from exc
        if not isinstance(row, dict):
            raise TransformerStudentError(f"{path}:{line_number}: запис має бути об'єктом")
        rows.append(row)
    if not rows:
        raise TransformerStudentError(f"{path}: корпус порожній")
    return rows, raw


def load_ml_stack():
    """Важкі залежності завантажуються лише для train/predict/serve."""
    try:
        import torch
        import torch.nn.functional as F
        from transformers import (
            AutoModelForSequenceClassification,
            AutoTokenizer,
            Trainer,
            TrainingArguments,
            set_seed,
        )
    except ImportError as exc:
        raise TransformerStudentError(
            "для трансформера встановіть PyTorch, transformers та accelerate; "
            "для базової лінії без цих залежностей використовуйте "
            "system-one-compact-student-20261022.py"
        ) from exc
    return {
        "torch": torch,
        "F": F,
        "AutoModelForSequenceClassification": AutoModelForSequenceClassification,
        "AutoTokenizer": AutoTokenizer,
        "Trainer": Trainer,
        "TrainingArguments": TrainingArguments,
        "set_seed": set_seed,
    }


def normalized_probabilities(logits: list[float] | tuple[float, ...], temperature: float = 1.0) -> list[float]:
    if isinstance(temperature, bool) or not isinstance(temperature, (int, float)):
        raise TransformerStudentError("температура має бути числом")
    temperature = float(temperature)
    if not math.isfinite(temperature) or temperature <= 0:
        raise TransformerStudentError("температура має бути скінченною та додатною")
    if len(logits) != len(LABELS):
        raise TransformerStudentError("очікується рівно п'ять оцінок класів")
    values = [float(value) / temperature for value in logits]
    if any(not math.isfinite(value) for value in values):
        raise TransformerStudentError("оцінки класів містять NaN або нескінченність")
    maximum = max(values)
    exponentials = [math.exp(value - maximum) for value in values]
    total = sum(exponentials)
    if not math.isfinite(total) or total <= 0:
        raise TransformerStudentError("оцінки не утворюють розподіл")
    return [value / total for value in exponentials]


def quantize_distribution(probabilities: list[float] | tuple[float, ...]) -> dict[str, dict[str, int]]:
    if len(probabilities) != len(LABELS):
        raise TransformerStudentError("очікується рівно п'ять імовірностей")
    values = [float(value) for value in probabilities]
    if any(not math.isfinite(value) or value < 0 for value in values):
        raise TransformerStudentError("розподіл містить недопустимі імовірності")
    total = sum(values)
    if not math.isfinite(total) or total <= 0:
        raise TransformerStudentError("сума імовірностей має бути додатною та скінченною")
    values = [value / total for value in values]
    scaled = [value * DENOMINATOR for value in values]
    counts = [math.floor(value) for value in scaled]
    remaining = DENOMINATOR - sum(counts)
    order = sorted(
        range(len(LABELS)),
        key=lambda index: (-(scaled[index] - counts[index]), index),
    )
    if remaining < 0 or remaining > len(LABELS):
        raise TransformerStudentError("нестійке округлення розподілу")
    for index in order[:remaining]:
        counts[index] += 1
    if sum(counts) != DENOMINATOR:
        raise TransformerStudentError("розподіл не сумується до точної одиниці")
    return {
        label: {"numerator": counts[index], "denominator": DENOMINATOR}
        for index, label in enumerate(LABELS)
    }


def teacher_probabilities(row: dict[str, Any], row_id: str) -> list[float]:
    raw = row.get("teacher_distribution")
    if not isinstance(raw, dict) or set(raw) != set(LABELS):
        raise TransformerStudentError(f"{row_id}: teacher_distribution має містити рівно п'ять класів")
    values: list[float] = []
    for label in LABELS:
        item = raw[label]
        if not isinstance(item, dict):
            raise TransformerStudentError(f"{row_id}: для {label} потрібна точна частка")
        numerator, denominator = item.get("numerator"), item.get("denominator")
        if (
            isinstance(numerator, bool) or not isinstance(numerator, int)
            or isinstance(denominator, bool) or not isinstance(denominator, int)
            or denominator <= 0
        ):
            raise TransformerStudentError(f"{row_id}: некоректна частка для {label}")
        probability = numerator / denominator
        if not math.isfinite(probability) or not 0 <= probability <= 1:
            raise TransformerStudentError(f"{row_id}: імовірність для {label} поза [0,1]")
        values.append(probability)
    if abs(sum(values) - 1.0) > 1e-9:
        raise TransformerStudentError(f"{row_id}: розподіл учителя не сумується до 1")
    total = sum(values)
    return [value / total for value in values]


def validate_rows(
    seed_rows: list[dict[str, Any]],
    seed_sha: str,
    teacher_rows: list[dict[str, Any]] | None = None,
) -> tuple[list[dict[str, Any]], dict[str, list[float]]]:
    seen: set[str] = set()
    train_rows: list[dict[str, Any]] = []
    for row in seed_rows:
        row_id = str(row.get("id", ""))
        if not row_id or row_id in seen:
            raise TransformerStudentError(f"відсутній або повторений seed id {row_id!r}")
        seen.add(row_id)
        if row.get("split") not in {"train", "validation", "test"}:
            raise TransformerStudentError(f"{row_id}: невідомий поділ вибірки")
        if row.get("gold") not in LABELS or not isinstance(row.get("text"), str) or not row["text"].strip():
            raise TransformerStudentError(f"{row_id}: некоректна мітка або текст")
        if row["split"] == "train":
            train_rows.append(row)
    if not train_rows:
        raise TransformerStudentError("корпус не має прикладів split=train")
    if teacher_rows is None:
        return train_rows, {}

    expected = {str(row["id"]): row for row in train_rows}
    by_id: dict[str, dict[str, Any]] = {}
    for row in teacher_rows:
        row_id = str(row.get("id", ""))
        if not row_id or row_id in by_id:
            raise TransformerStudentError(f"відсутній або повторений teacher id {row_id!r}")
        by_id[row_id] = row
        if row.get("split") != "train":
            raise TransformerStudentError(f"{row_id}: навчання дозволяє лише teacher split=train")
        if row.get("dataset_sha256") != seed_sha:
            raise TransformerStudentError(f"{row_id}: SHA корпусу вчителя не збігається")
    if set(by_id) != set(expected):
        raise TransformerStudentError(
            f"розбіжність train/teacher: відсутні={sorted(set(expected)-set(by_id))}, "
            f"зайві={sorted(set(by_id)-set(expected))}"
        )
    targets: dict[str, list[float]] = {}
    for row_id, teacher_row in by_id.items():
        original = expected[row_id]
        if teacher_row.get("gold") != original["gold"] or teacher_row.get("text") != original["text"]:
            raise TransformerStudentError(f"{row_id}: teacher не збігається з еталонним текстом/міткою")
        targets[row_id] = teacher_probabilities(teacher_row, row_id)
    return train_rows, targets


def calibration_nll(logits: list[list[float]], rows: list[dict[str, Any]], temperature: float) -> float:
    if not rows or len(logits) != len(rows):
        raise TransformerStudentError("логіти не відповідають validation набору")
    if any(row.get("split") != "validation" for row in rows):
        raise TransformerStudentError("температура калібрується лише на split=validation")
    total = 0.0
    for row, values in zip(rows, logits):
        probabilities = normalized_probabilities(values, temperature)
        probability = probabilities[LABELS.index(row["gold"])]
        total -= math.log(max(probability, 1e-300))
    return total / len(rows)


def fit_temperature(
    logits: list[list[float]],
    rows: list[dict[str, Any]],
    minimum: float = 0.05,
    maximum: float = 20.0,
    grid_points: int = 501,
) -> dict[str, Any]:
    if not math.isfinite(minimum) or not math.isfinite(maximum) or minimum <= 0 or maximum <= minimum:
        raise TransformerStudentError("потрібно 0 < minimum < maximum для температури")
    if isinstance(grid_points, bool) or not isinstance(grid_points, int) or not 51 <= grid_points <= 5001:
        raise TransformerStudentError("grid_points має бути цілим у межах 51..5001")
    before = calibration_nll(logits, rows, 1.0)
    candidates = [
        math.exp(math.log(minimum) + i * (math.log(maximum) - math.log(minimum)) / (grid_points - 1))
        for i in range(grid_points)
    ]
    candidates.append(1.0)
    scored = [(calibration_nll(logits, rows, value), value) for value in set(candidates)]
    after, temperature = min(scored, key=lambda pair: (pair[0], abs(math.log(pair[1])), pair[1]))
    if after > before + 1e-12:
        raise TransformerStudentError("калібрування несподівано погіршило NLL")
    return {
        "method": "scalar-temperature-grid-min-nll-v1",
        "temperature": temperature,
        "split": "validation",
        "count": len(rows),
        "nll_before": before,
        "nll_after": after,
        "grid_points": grid_points,
        "range": {"minimum": minimum, "maximum": maximum},
        "used_test_split": False,
    }


def _load_stack():
    stack = load_ml_stack()
    return stack["torch"], stack["F"], stack


def _tokenize(tokenizer, rows: list[dict[str, Any]], max_length: int, targets: dict[str, list[float]]):
    result = []
    for row in rows:
        encoded = tokenizer(row["text"], truncation=True, max_length=max_length, padding=False)
        one_hot = [1.0 if label == row["gold"] else 0.0 for label in LABELS]
        result.append({
            **encoded,
            "labels": LABELS.index(row["gold"]),
            "teacher_probs": targets.get(str(row["id"]), one_hot),
        })
    return result


def _collate(tokenizer, torch):
    def collate(features):
        values = [
            {key: item for key, item in row.items() if key not in {"labels", "teacher_probs"}}
            for row in features
        ]
        batch = tokenizer.pad(values, padding=True, return_tensors="pt")
        batch["labels"] = torch.tensor([row["labels"] for row in features], dtype=torch.long)
        batch["teacher_probs"] = torch.tensor(
            [row["teacher_probs"] for row in features], dtype=torch.float32
        )
        return batch
    return collate


def _logits(model, tokenizer, rows, max_length: int, batch_size: int, torch):
    model.eval()
    device = next(model.parameters()).device
    result: list[list[float]] = []
    with torch.no_grad():
        for start in range(0, len(rows), batch_size):
            batch_rows = rows[start:start + batch_size]
            encoded = tokenizer(
                [row["text"] for row in batch_rows],
                truncation=True,
                max_length=max_length,
                padding=True,
                return_tensors="pt",
            )
            encoded = {key: value.to(device) for key, value in encoded.items()}
            raw_logits = model(**encoded).logits.detach().float().cpu().tolist()
            result.extend([[float(value) for value in item] for item in raw_logits])
    if len(result) != len(rows):
        raise TransformerStudentError("кількість прогнозів не збігається з розміром набору")
    return result


def _atomic_text(path: Path, value: str, overwrite: bool = False):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and not overwrite:
        raise TransformerStudentError(f"файл уже існує: {path}; додайте --overwrite свідомо")
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", newline="\n", dir=path.parent,
        prefix=f".{path.name}.", suffix=".tmp", delete=False,
    ) as handle:
        temporary = Path(handle.name)
        handle.write(value)
    try:
        os.replace(temporary, path)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise


def train(args: argparse.Namespace) -> int:
    torch, F, stack = _load_stack()
    input_path, output_dir = args.input.resolve(), args.output_dir.resolve()
    teacher_path = args.teacher.resolve() if args.teacher else None
    if output_dir == input_path or output_dir in input_path.parents:
        raise TransformerStudentError("каталог моделі не може містити seed-корпус")
    if teacher_path and (output_dir == teacher_path or output_dir in teacher_path.parents):
        raise TransformerStudentError("каталог моделі не може містити teacher-файл")
    if output_dir.exists() and not args.overwrite:
        raise TransformerStudentError(f"каталог уже існує: {output_dir}; додайте --overwrite свідомо")
    output_dir.parent.mkdir(parents=True, exist_ok=True)

    seed_rows, seed_raw = read_jsonl(input_path)
    dataset_sha = sha256(seed_raw)
    teacher_rows = read_jsonl(teacher_path)[0] if teacher_path else None
    train_rows, soft_targets = validate_rows(seed_rows, dataset_sha, teacher_rows)
    validation = [row for row in seed_rows if row["split"] == "validation"]
    if not validation:
        raise TransformerStudentError("потрібен непорожній split=validation для калібрування")
    gold_weight = args.gold_weight if args.gold_weight is not None else (0.25 if teacher_path else 1.0)
    if not math.isfinite(gold_weight) or not 0 <= gold_weight <= 1:
        raise TransformerStudentError("--gold-weight має бути в [0,1]")
    if not teacher_path and gold_weight != 1.0:
        raise TransformerStudentError("без --teacher допустимий лише gold_weight=1")
    if args.epochs <= 0 or args.batch_size <= 0 or args.max_length <= 0 or args.learning_rate <= 0:
        raise TransformerStudentError("epochs, batch-size, max-length і learning-rate мають бути додатними")
    if not math.isfinite(args.distillation_temperature) or args.distillation_temperature <= 0:
        raise TransformerStudentError("distillation-temperature має бути скінченною та додатною")

    label_to_id = {label: index for index, label in enumerate(LABELS)}
    id_to_label = {str(index): label for index, label in enumerate(LABELS)}
    revision = args.revision or None
    tokenizer = stack["AutoTokenizer"].from_pretrained(args.model_name, revision=revision)
    model = stack["AutoModelForSequenceClassification"].from_pretrained(
        args.model_name,
        revision=revision,
        num_labels=len(LABELS),
        label2id=label_to_id,
        id2label={int(key): value for key, value in id_to_label.items()},
    )
    model.config.problem_type = "single_label_classification"
    tokenized_train = _tokenize(tokenizer, train_rows, args.max_length, soft_targets)
    collator = _collate(tokenizer, torch)

    class SoftTargetTrainer(stack["Trainer"]):
        def __init__(self, *trainer_args, system_one_gold_weight: float, distillation_temperature: float, **kwargs):
            self.system_one_gold_weight = system_one_gold_weight
            self.distillation_temperature = distillation_temperature
            super().__init__(*trainer_args, **kwargs)

        def compute_loss(self, model, inputs, return_outputs=False, num_items_in_batch=None):
            labels = inputs.pop("labels")
            target_probs = inputs.pop("teacher_probs").float().clamp(min=1e-12)
            target_probs = target_probs / target_probs.sum(dim=-1, keepdim=True)
            outputs = model(**inputs)
            logits = outputs.logits.float()
            temperature = self.distillation_temperature
            teacher_soft = torch.softmax(torch.log(target_probs) / temperature, dim=-1)
            student_log = torch.log_softmax(logits / temperature, dim=-1)
            soft_loss = F.kl_div(student_log, teacher_soft, reduction="batchmean") * (temperature ** 2)
            hard_loss = F.cross_entropy(logits, labels)
            loss = (1.0 - self.system_one_gold_weight) * soft_loss + self.system_one_gold_weight * hard_loss
            return (loss, outputs) if return_outputs else loss

    import inspect
    ta_parameters = inspect.signature(stack["TrainingArguments"].__init__).parameters
    trainer_parameters = inspect.signature(stack["Trainer"].__init__).parameters
    with tempfile.TemporaryDirectory(prefix=".sens-system-one-checkpoints-", dir=output_dir.parent) as checkpoint_dir:
        training_options = {
            "output_dir": checkpoint_dir,
            "learning_rate": args.learning_rate,
            "per_device_train_batch_size": args.batch_size,
            "num_train_epochs": args.epochs,
            "weight_decay": args.weight_decay,
            "logging_steps": 1,
            "save_strategy": "no",
            "report_to": [],
            "remove_unused_columns": False,
            "seed": args.seed,
            "dataloader_num_workers": 0,
        }
        if "eval_strategy" in ta_parameters:
            training_options["eval_strategy"] = "no"
        elif "evaluation_strategy" in ta_parameters:
            training_options["evaluation_strategy"] = "no"
        if "use_cpu" in ta_parameters and args.force_cpu:
            training_options["use_cpu"] = True
        stack["set_seed"](args.seed)
        trainer_kwargs = {
            "model": model,
            "args": stack["TrainingArguments"](**training_options),
            "train_dataset": tokenized_train,
            "data_collator": collator,
            "system_one_gold_weight": gold_weight,
            "distillation_temperature": args.distillation_temperature,
        }
        trainer_kwargs.update(
            {"processing_class": tokenizer} if "processing_class" in trainer_parameters
            else {"tokenizer": tokenizer}
        )
        trainer = SoftTargetTrainer(**trainer_kwargs)
        trainer.train()
        model = trainer.model
        validation_logits = _logits(model, tokenizer, validation, args.max_length, args.batch_size, torch)
        calibration = fit_temperature(
            validation_logits, validation, args.min_temperature, args.max_temperature, args.grid_points
        )

        staging = Path(tempfile.mkdtemp(prefix=f".{output_dir.name}.staging-", dir=output_dir.parent))
        backup = output_dir.with_name(f".{output_dir.name}.backup")
        try:
            trainer.save_model(str(staging))
            tokenizer.save_pretrained(staging)
            metadata = {
                "schema": MODEL_SCHEMA,
                "model_kind": "multilingual-transformer-sequence-classifier",
                "base_model": args.model_name,
                "base_revision": args.revision,
                "classes": list(LABELS),
                "label2id": label_to_id,
                "id2label": id_to_label,
                "max_length": args.max_length,
                "training_count": len(train_rows),
                "training_split": "train",
                "training_dataset_sha256": dataset_sha,
                "teacher_observations_sha256": sha256(teacher_path.read_bytes()) if teacher_path else None,
                "teacher_used": teacher_path is not None,
                "gold_weight": gold_weight,
                "distillation_temperature": args.distillation_temperature,
                "seed": args.seed,
                "calibration_temperature": calibration["temperature"],
                "calibration": calibration,
                "test_used_for_training_or_calibration": False,
            }
            _atomic_text(staging / "sens-system-one-transformer.json", json.dumps(metadata, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
            if output_dir.exists():
                if not args.overwrite:
                    raise TransformerStudentError(f"каталог з'явився під час роботи: {output_dir}")
                if backup.exists():
                    shutil.rmtree(backup)
                os.replace(output_dir, backup)
            try:
                os.replace(staging, output_dir)
            except Exception:
                if backup.exists() and not output_dir.exists():
                    os.replace(backup, output_dir)
                raise
            if backup.exists():
                shutil.rmtree(backup)
        finally:
            if staging.exists():
                shutil.rmtree(staging, ignore_errors=True)

    print(json.dumps({
        "result": "transformer-student-trained-and-calibrated",
        "model_path": str(output_dir),
        "base_model": args.model_name,
        "teacher_used": teacher_path is not None,
        "training_count": len(train_rows),
        "validation_count": len(validation),
        "calibration_temperature": calibration["temperature"],
        "nll_before": calibration["nll_before"],
        "nll_after": calibration["nll_after"],
        "training_dataset_sha256": dataset_sha,
        "test_used_for_training_or_calibration": False,
    }, ensure_ascii=False, sort_keys=True))
    return 0


def _load_bundle(model_dir: Path):
    stack = load_ml_stack()
    try:
        metadata = json.loads((model_dir / "sens-system-one-transformer.json").read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise TransformerStudentError(f"не вдалося прочитати метадані моделі: {exc}") from exc
    if metadata.get("schema") != MODEL_SCHEMA or metadata.get("classes") != list(LABELS):
        raise TransformerStudentError("несумісна схема трансформерної моделі")
    temperature = metadata.get("calibration_temperature", 1.0)
    if isinstance(temperature, bool) or not isinstance(temperature, (int, float)) or not math.isfinite(float(temperature)) or temperature <= 0:
        raise TransformerStudentError("температура калібрування моделі некоректна")
    tokenizer = stack["AutoTokenizer"].from_pretrained(model_dir)
    model = stack["AutoModelForSequenceClassification"].from_pretrained(model_dir)
    model.eval()
    return stack, tokenizer, model, metadata


def _prediction_rows(model, tokenizer, rows, metadata, batch_size: int, torch):
    raw_logits = _logits(model, tokenizer, rows, metadata["max_length"], batch_size, torch)
    temperature = float(metadata.get("calibration_temperature", 1.0))
    output = []
    for row, logits in zip(rows, raw_logits):
        values = normalized_probabilities(logits, temperature)
        distribution = quantize_distribution(values)
        winner_index = max(range(len(LABELS)), key=lambda i: (values[i], -i))
        output.append({
            "id": str(row["id"]),
            "split": row["split"],
            "text": row["text"],
            "gold": row["gold"],
            "source": "compact-transformer-student",
            "model_schema": MODEL_SCHEMA,
            "base_model": metadata["base_model"],
            "training_dataset_sha256": metadata["training_dataset_sha256"],
            "calibration_temperature": temperature,
            "prediction": LABELS[winner_index],
            "confidence": distribution[LABELS[winner_index]],
            "distribution": distribution,
        })
    return output


def predict(args: argparse.Namespace) -> int:
    stack, tokenizer, model, metadata = _load_bundle(args.model_dir)
    rows, raw = read_jsonl(args.input)
    if sha256(raw) != metadata.get("training_dataset_sha256"):
        raise TransformerStudentError("SHA seed-корпусу не збігається з навчальним SHA моделі")
    selected, seen = [], set()
    for row in rows:
        row_id = str(row.get("id", ""))
        if not row_id or row_id in seen:
            raise TransformerStudentError(f"відсутній або повторений id {row_id!r}")
        seen.add(row_id)
        if row.get("split") not in {"train", "validation", "test"}:
            raise TransformerStudentError(f"{row_id}: невідомий split")
        if row.get("gold") not in LABELS or not isinstance(row.get("text"), str):
            raise TransformerStudentError(f"{row_id}: некоректний запис")
        if row["split"] == args.split:
            selected.append(row)
    if not selected:
        raise TransformerStudentError(f"немає прикладів split={args.split}")
    predictions = _prediction_rows(model, tokenizer, selected, metadata, args.batch_size, stack["torch"])
    output = args.output.resolve()
    if output == args.input.resolve() or output == args.model_dir.resolve() or args.model_dir.resolve() in output.parents:
        raise TransformerStudentError("вихід прогнозів не може перезаписати вхід або файли моделі")
    _atomic_text(output, "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in predictions), args.overwrite)
    print(json.dumps({"result": "transformer-student-predictions-written", "count": len(predictions), "split": args.split, "output": str(output)}, ensure_ascii=False, sort_keys=True))
    return 0


def create_local_server(model_dir: Path, port: int = 8101, api_key: str | None = None):
    stack, tokenizer, model, metadata = _load_bundle(model_dir)
    torch = stack["torch"]
    if isinstance(port, bool) or not isinstance(port, int) or not 0 <= port <= 65535:
        raise TransformerStudentError("порт має бути цілим у межах 0..65535")
    if api_key is not None and ("\r" in api_key or "\n" in api_key):
        raise TransformerStudentError("ключ HTTP-вузла містить заборонені символи")

    class Handler(BaseHTTPRequestHandler):
        server_version = "SENS-System-One-Transformer/1"
        sys_version = ""

        def _reply(self, status: int, payload: dict[str, Any]):
            body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            if self.path == "/health":
                self._reply(200, {"status": "ok", "model": MODEL_SCHEMA})
            else:
                self._reply(404, {"error": {"message": "route not found", "type": "not_found"}})

        def do_POST(self):
            if self.path != "/v1/chat/completions":
                self._reply(404, {"error": {"message": "route not found", "type": "not_found"}})
                return
            if api_key is not None:
                import hmac
                if not hmac.compare_digest(self.headers.get("Authorization", ""), f"Bearer {api_key}"):
                    self._reply(401, {"error": {"message": "unauthorized", "type": "authentication_error"}})
                    return
            try:
                raw_length = self.headers.get("Content-Length", "")
                if not raw_length.isdigit():
                    self._reply(411, {"error": {"message": "Content-Length required", "type": "invalid_request_error"}})
                    return
                length = int(raw_length)
                if length <= 0 or length > MAX_REQUEST_BYTES:
                    self._reply(413, {"error": {"message": "request body too large or empty", "type": "invalid_request_error"}})
                    return
                request = json.loads(self.rfile.read(length).decode("utf-8"))
                if not isinstance(request, dict):
                    raise TransformerStudentError("корінь запиту має бути об'єктом")
                structured = request.get("structured_outputs")
                if not isinstance(structured, dict) or structured.get("choice") != list(LETTERS):
                    raise TransformerStudentError("structured_outputs.choice має бути рівно A,B,C,D,E")
                messages = request.get("messages")
                if not isinstance(messages, list):
                    raise TransformerStudentError("messages має бути списком")
                system_prompts = [m.get("content") for m in messages if isinstance(m, dict) and m.get("role") == "system"]
                user_texts = [m.get("content") for m in messages if isinstance(m, dict) and m.get("role") == "user"]
                if not system_prompts or not isinstance(system_prompts[-1], str):
                    raise TransformerStudentError("потрібна system-інструкція")
                if not user_texts or not isinstance(user_texts[-1], str) or not user_texts[-1].strip():
                    raise TransformerStudentError("потрібен непорожній текст звернення")
                criterion_pairs = []
                for line in system_prompts[-1].splitlines():
                    match = re.match(r"^([A-E]):\s*(.*?)\s+—\s+.+$", line.strip())
                    if match:
                        criterion_pairs.append((match.group(1), match.group(2)))
                expected = list(zip(LETTERS, LABELS))
                if criterion_pairs != expected:
                    raise TransformerStudentError("порядок критеріїв не збігається з класами моделі")
                encoded = tokenizer(user_texts[-1], truncation=True, max_length=metadata["max_length"], return_tensors="pt")
                encoded = {key: value.to(next(model.parameters()).device) for key, value in encoded.items()}
                with torch.no_grad():
                    logits = model(**encoded).logits[0].detach().float().cpu().tolist()
                probs = normalized_probabilities(logits, float(metadata["calibration_temperature"]))
                winning = max(range(len(LABELS)), key=lambda index: (probs[index], -index))
                generated = LETTERS[winning]
                top_logprobs = [
                    {"token": LETTERS[index], "logprob": math.log(max(probs[index], 1e-300))}
                    for index in range(len(LABELS))
                ]
                self._reply(200, {
                    "id": "sens-transformer-student-local",
                    "object": "chat.completion",
                    "created": 0,
                    "model": request.get("model") or metadata["base_model"],
                    "choices": [{
                        "index": 0,
                        "message": {"role": "assistant", "content": generated},
                        "finish_reason": "stop",
                        "logprobs": {"content": [{"token": generated, "top_logprobs": top_logprobs}]},
                    }],
                })
            except (UnicodeDecodeError, json.JSONDecodeError, TransformerStudentError, KeyError, TypeError, ValueError) as exc:
                self._reply(400, {"error": {"message": str(exc), "type": "invalid_request_error"}})

        def log_message(self, _format: str, *_args: Any) -> None:
            return

    try:
        return ThreadingHTTPServer(("127.0.0.1", port), Handler)
    except OSError as exc:
        raise TransformerStudentError(f"не вдалося запустити локальний HTTP-вузол: {exc}") from exc


def serve(args: argparse.Namespace) -> int:
    api_key = args.api_key or os.environ.get("SENS_SYSTEM_ONE_STUDENT_API_KEY")
    server = create_local_server(args.model_dir, args.port, api_key)
    print(f"System One transformer ready at http://127.0.0.1:{server.server_port}/v1/chat/completions", file=sys.stderr)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    train_parser = commands.add_parser("train", help="навчити трансформер-учня")
    train_parser.add_argument("--input", type=Path, default=Path("research/system-one-support-seed-20261022.jsonl"))
    train_parser.add_argument("--teacher", type=Path, help="teacher JSONL; лише split=train")
    train_parser.add_argument("--model-name", default=DEFAULT_MODEL)
    train_parser.add_argument("--revision", help="зафіксована ревізія/commit базової моделі")
    train_parser.add_argument("--output-dir", type=Path, required=True)
    train_parser.add_argument("--epochs", type=float, default=3.0)
    train_parser.add_argument("--batch-size", type=int, default=8)
    train_parser.add_argument("--learning-rate", type=float, default=3e-5)
    train_parser.add_argument("--weight-decay", type=float, default=0.01)
    train_parser.add_argument("--max-length", type=int, default=512)
    train_parser.add_argument("--gold-weight", type=float)
    train_parser.add_argument("--distillation-temperature", type=float, default=1.0)
    train_parser.add_argument("--min-temperature", type=float, default=0.05)
    train_parser.add_argument("--max-temperature", type=float, default=20.0)
    train_parser.add_argument("--grid-points", type=int, default=501)
    train_parser.add_argument("--seed", type=int, default=42)
    train_parser.add_argument("--force-cpu", action="store_true")
    train_parser.add_argument("--overwrite", action="store_true")
    train_parser.set_defaults(handler=train)

    predict_parser = commands.add_parser("predict", help="оцінити validation або test")
    predict_parser.add_argument("--model-dir", type=Path, required=True)
    predict_parser.add_argument("--input", type=Path, default=Path("research/system-one-support-seed-20261022.jsonl"))
    predict_parser.add_argument("--split", choices=("validation", "test"), default="test")
    predict_parser.add_argument("--output", type=Path, required=True)
    predict_parser.add_argument("--batch-size", type=int, default=16)
    predict_parser.add_argument("--overwrite", action="store_true")
    predict_parser.set_defaults(handler=predict)

    serve_parser = commands.add_parser("serve", help="локальний HTTP API для адаптера SENS")
    serve_parser.add_argument("--model-dir", type=Path, required=True)
    serve_parser.add_argument("--port", type=int, default=8101)
    serve_parser.add_argument("--api-key")
    serve_parser.set_defaults(handler=serve)

    args = parser.parse_args()
    try:
        return args.handler(args)
    except (OSError, UnicodeDecodeError, TransformerStudentError, KeyError, TypeError, ValueError) as exc:
        print(f"помилка трансформерного учня System One: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
