#!/usr/bin/env python3
"""Малий базовий учень System One: навчання за мітками або м'якими оцінками вчителя.

Модель — компактний багатокласовий наївний баєсів класифікатор на словах.
Це відтворювана CPU-базова лінія, а не мала мовна модель-трансформер.
Скрипт не потребує сторонніх пакетів і не визначає семантику SENS.
"""
from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import math
import os
import re
import sys
import tempfile
import unicodedata
from collections import Counter
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from fractions import Fraction
from pathlib import Path
from typing import Any

LABELS = ("оплата", "доставка", "технічне", "обліковий-запис", "невизначено")
DENOMINATOR = 1_000_000_000
MODEL_SCHEMA = "sens.system-one.naive-bayes/1"


class StudentError(ValueError):
    """Названа помилка навчальних даних чи компактної моделі."""


def read_jsonl(path: Path) -> tuple[list[dict[str, Any]], bytes]:
    raw = path.read_bytes()
    rows: list[dict[str, Any]] = []
    for number, line in enumerate(raw.decode("utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise StudentError(f"{path}:{number}: некоректний JSON: {exc}") from exc
        if not isinstance(value, dict):
            raise StudentError(f"{path}:{number}: запис має бути об'єктом")
        rows.append(value)
    if not rows:
        raise StudentError(f"{path}: набір порожній")
    return rows, raw


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def tokenize(text: str) -> list[str]:
    normalized = unicodedata.normalize("NFKC", text).casefold()
    return re.findall(r"[^\W_]+", normalized, flags=re.UNICODE)


def atomic_write(path: Path, text: str, overwrite: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and not overwrite:
        raise StudentError(f"файл вже існує: {path}; додайте --overwrite свідомо")
    handle = tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", newline="\n", dir=path.parent,
        prefix=f".{path.name}.", suffix=".tmp", delete=False,
    )
    temp = Path(handle.name)
    try:
        with handle:
            handle.write(text)
        os.replace(temp, path)
    except Exception:
        temp.unlink(missing_ok=True)
        raise


def exact_probability(value: Any, row_id: str, label: str) -> Fraction:
    if not isinstance(value, dict):
        raise StudentError(f"{row_id}: для {label} потрібна точна частка")
    num, den = value.get("numerator"), value.get("denominator")
    if (
        isinstance(num, bool) or not isinstance(num, int)
        or isinstance(den, bool) or not isinstance(den, int) or den <= 0
    ):
        raise StudentError(f"{row_id}: некоректна частка для {label}")
    probability = Fraction(num, den)
    if probability < 0 or probability > 1:
        raise StudentError(f"{row_id}: ймовірність поза [0,1] для {label}")
    return probability


def teacher_targets(rows: list[dict[str, Any]], teacher_path: Path, seed_sha: str) -> dict[str, dict[str, Fraction]]:
    teacher_rows, teacher_raw = read_jsonl(teacher_path)
    del teacher_raw
    by_id: dict[str, dict[str, Any]] = {}
    for row in teacher_rows:
        row_id = row.get("id")
        if not row_id or row_id in by_id:
            raise StudentError(f"учительський файл має відсутній/повторений id: {row_id!r}")
        if row.get("split") != "train":
            raise StudentError(f"{row_id}: до навчання допускаються лише вчительські записи train")
        if row.get("dataset_sha256") != seed_sha:
            raise StudentError(f"{row_id}: SHA корпусу учителя не збігається з корпусом навчання")
        by_id[str(row_id)] = row
    expected_ids = {str(row["id"]) for row in rows}
    observed_ids = set(by_id)
    if expected_ids != observed_ids:
        raise StudentError(
            f"розбіжність train/teacher: відсутні={sorted(expected_ids-observed_ids)}, "
            f"зайві={sorted(observed_ids-expected_ids)}"
        )

    targets: dict[str, dict[str, Fraction]] = {}
    for row in rows:
        row_id = str(row["id"])
        raw = by_id[row_id].get("teacher_distribution")
        if not isinstance(raw, dict) or set(raw) != set(LABELS):
            raise StudentError(f"{row_id}: розподіл учителя має містити рівно п'ять класів")
        target = {label: exact_probability(raw[label], row_id, label) for label in LABELS}
        if sum(target.values(), Fraction(0, 1)) != 1:
            raise StudentError(f"{row_id}: розподіл учителя не сумується точно до 1")
        targets[row_id] = target
    return targets


def train(args: argparse.Namespace) -> int:
    all_rows, raw = read_jsonl(args.input)
    seed_sha = digest(raw)
    if args.output.resolve() == args.input.resolve():
        raise StudentError("вихід моделі не може перезаписати навчальний корпус")
    if args.teacher is not None and args.output.resolve() == args.teacher.resolve():
        raise StudentError("вихід моделі не може перезаписати вчительські спостереження")

    # Хеш прив'язує вчительські спостереження до повного зафіксованого корпусу,
    # але статистики моделі обчислюються винятково на train.
    seen: set[str] = set()
    for row in all_rows:
        row_id = str(row.get("id", ""))
        if not row_id or row_id in seen:
            raise StudentError(f"відсутній або повторений id: {row_id!r}")
        seen.add(row_id)
        if row.get("split") not in ("train", "validation", "test"):
            raise StudentError(f"{row_id}: невідомий поділ вибірки")
        if row.get("gold") not in LABELS:
            raise StudentError(f"{row_id}: невідома еталонна мітка")
        if not isinstance(row.get("text"), str) or not row["text"].strip():
            raise StudentError(f"{row_id}: відсутній текст")
    rows = [row for row in all_rows if row.get("split") == "train"]
    if not rows:
        raise StudentError("у корпусі немає жодного прикладу split=train")

    has_teacher = args.teacher is not None
    gold_weight = args.gold_weight if args.gold_weight is not None else (0.25 if has_teacher else 1.0)
    if not 0 <= gold_weight <= 1 or not math.isfinite(gold_weight):
        raise StudentError("--gold-weight має бути числом у [0,1]")
    if not has_teacher and gold_weight != 1:
        raise StudentError("без --teacher допустимий лише gold_weight=1")
    if args.smoothing <= 0 or not math.isfinite(args.smoothing):
        raise StudentError("--smoothing має бути скінченним додатним числом")
    if args.min_count < 1:
        raise StudentError("--min-count має бути не меншим за 1")

    teachers: dict[str, dict[str, Fraction]] = {}
    teacher_sha = None
    if has_teacher:
        teacher_sha = digest(args.teacher.read_bytes())
        teachers = teacher_targets(rows, args.teacher, seed_sha)

    tokenized = {str(row["id"]): tokenize(row["text"]) for row in rows}
    global_terms = Counter(token for sequence in tokenized.values() for token in sequence)
    vocabulary = sorted(token for token, count in global_terms.items() if count >= args.min_count)
    if not vocabulary:
        raise StudentError("словник порожній після фільтрування")
    vocabulary_set = set(vocabulary)

    class_mass = {label: 0.0 for label in LABELS}
    word_mass = {label: Counter() for label in LABELS}
    word_totals = {label: 0.0 for label in LABELS}
    for row in rows:
        row_id = str(row["id"])
        gold = str(row["gold"])
        if has_teacher:
            soft = {label: float(teachers[row_id][label]) for label in LABELS}
            weights = {
                label: (1.0 - gold_weight) * soft[label] + (gold_weight if label == gold else 0.0)
                for label in LABELS
            }
        else:
            weights = {label: (1.0 if label == gold else 0.0) for label in LABELS}
        terms = [term for term in tokenized[row_id] if term in vocabulary_set]
        for label in LABELS:
            weight = weights[label]
            if weight <= 0:
                continue
            class_mass[label] += weight
            for term in terms:
                word_mass[label][term] += weight
                word_totals[label] += weight

    alpha = args.smoothing
    total_class_mass = sum(class_mass.values())
    class_log_prior = {
        label: math.log(
            (class_mass[label] + alpha)
            / (total_class_mass + alpha * len(LABELS))
        )
        for label in LABELS
    }
    token_log_probability: dict[str, dict[str, float]] = {}
    for label in LABELS:
        denominator = word_totals[label] + alpha * len(vocabulary)
        token_log_probability[label] = {
            token: math.log((word_mass[label][token] + alpha) / denominator)
            for token in vocabulary
        }

    model: dict[str, Any] = {
        "schema": MODEL_SCHEMA,
        "model_kind": "multinomial-naive-bayes-soft-target-student",
        "tokenizer": "unicode-NFKC-casefold-word-tokens-v1",
        "classes": list(LABELS),
        "vocabulary": vocabulary,
        "smoothing": alpha,
        "minimum_token_count": args.min_count,
        "gold_weight": gold_weight,
        "teacher_used": has_teacher,
        "training_count": len(rows),
        "training_split": "train",
        "calibration_temperature": 1.0,
        "calibration": {
            "method": "none",
            "split": None,
            "count": 0,
            "dataset_sha256": None,
        },
        "training_dataset_sha256": seed_sha,
        "teacher_observations_sha256": teacher_sha,
        "class_log_prior": class_log_prior,
        "token_log_probability": token_log_probability,
        "note": "compact baseline only; SENS owns validation, thresholds, and final decisions",
    }
    rendered = json.dumps(model, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
    atomic_write(args.output, rendered, args.overwrite)
    print(
        json.dumps(
            {
                "result": "student-trained",
                "model_kind": model["model_kind"],
                "training_count": len(rows),
                "vocabulary_size": len(vocabulary),
                "teacher_used": has_teacher,
                "gold_weight": gold_weight,
                "training_dataset_sha256": seed_sha,
                "model_path": str(args.output),
                "model_sha256": digest(rendered.encode("utf-8")),
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


def class_scores(model: dict[str, Any], text: str) -> dict[str, float]:
    """Ненормовані оцінки класів; не округлюємо їх до транспортних дробів."""
    classes = model.get("classes")
    vocabulary = model.get("vocabulary")
    if classes != list(LABELS) or not isinstance(vocabulary, list):
        raise StudentError("схема компактної моделі не відповідає System One")
    vocab = set(vocabulary)
    scores = {label: float(model["class_log_prior"][label]) for label in LABELS}
    for token in tokenize(text):
        if token not in vocab:
            continue
        for label in LABELS:
            scores[label] += float(model["token_log_probability"][label][token])
    if any(not math.isfinite(value) for value in scores.values()):
        raise StudentError("компактна модель повернула нескінченну оцінку")
    return scores


def normalized_log_probabilities(model: dict[str, Any], text: str) -> dict[str, float]:
    raw_temperature = model.get("calibration_temperature", 1.0)
    if isinstance(raw_temperature, bool) or not isinstance(raw_temperature, (int, float)):
        raise StudentError("температура калібрування має бути числом")
    temperature = float(raw_temperature)
    if not math.isfinite(temperature) or temperature <= 0:
        raise StudentError("температура калібрування має бути скінченною та додатною")
    scores = class_scores(model, text)
    scaled = {label: scores[label] / temperature for label in LABELS}
    maximum = max(scaled.values())
    log_total = maximum + math.log(sum(math.exp(value - maximum) for value in scaled.values()))
    return {label: scaled[label] - log_total for label in LABELS}


def probabilities(model: dict[str, Any], text: str) -> dict[str, Fraction]:
    log_probabilities = normalized_log_probabilities(model, text)
    exps = {label: math.exp(log_probabilities[label]) for label in LABELS}
    total = sum(exps.values())
    if not math.isfinite(total) or total <= 0:
        raise StudentError("оцінки компактної моделі не утворюють розподіл")
    scaled = {label: exps[label] / total * DENOMINATOR for label in LABELS}
    counts = {label: math.floor(scaled[label]) for label in LABELS}
    remainder = DENOMINATOR - sum(counts.values())
    ranked = sorted(
        LABELS,
        key=lambda label: (
            -(scaled[label] - math.floor(scaled[label])),
            LABELS.index(label),
        ),
    )
    for label in ranked[:remainder]:
        counts[label] += 1
    if sum(counts.values()) != DENOMINATOR:
        raise StudentError("внутрішня помилка: нормування учня")
    return {label: Fraction(counts[label], DENOMINATOR) for label in LABELS}


def create_local_server(
    model: dict[str, Any],
    port: int = 0,
    api_key: str | None = None,
) -> ThreadingHTTPServer:
    """Підняти вузький OpenAI-сумісний HTTP інтерфейс лише на loopback."""
    if not isinstance(model, dict) or model.get("schema") != MODEL_SCHEMA or model.get("classes") != list(LABELS):
        raise StudentError("несумісна схема компактної моделі для HTTP")
    if not isinstance(port, int) or not 0 <= port <= 65535:
        raise StudentError("порт має бути цілим числом у межах 0..65535")
    if api_key is not None and ("\r" in api_key or "\n" in api_key):
        raise StudentError("ключ сервера містить заборонені символи")

    letter_to_label = dict(zip("ABCDE", LABELS))
    expected_labels = list(LABELS)
    maximum_body = 1 * 1024 * 1024

    class Handler(BaseHTTPRequestHandler):
        server_version = "SENS-System-One-Student/1"
        sys_version = ""

        def _reply(self, status: int, value: dict[str, Any]) -> None:
            data = json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self) -> None:
            if self.path == "/health":
                self._reply(200, {"status": "ok", "model": MODEL_SCHEMA})
            else:
                self._reply(404, {"error": {"message": "route not found", "type": "not_found"}})

        def do_POST(self) -> None:
            if self.path != "/v1/chat/completions":
                self._reply(404, {"error": {"message": "route not found", "type": "not_found"}})
                return
            if api_key is not None:
                received = self.headers.get("Authorization", "")
                expected = f"Bearer {api_key}"
                if not hmac.compare_digest(received, expected):
                    self._reply(401, {"error": {"message": "unauthorized", "type": "authentication_error"}})
                    return
            try:
                length_text = self.headers.get("Content-Length", "")
                if not length_text.isdigit():
                    self._reply(411, {"error": {"message": "Content-Length required", "type": "invalid_request_error"}})
                    return
                length = int(length_text)
                if length <= 0 or length > maximum_body:
                    self._reply(413, {"error": {"message": "request body too large or empty", "type": "invalid_request_error"}})
                    return
                request = json.loads(self.rfile.read(length).decode("utf-8"))
                if not isinstance(request, dict):
                    raise StudentError("request root must be an object")
                messages = request.get("messages")
                structured_outputs = request.get("structured_outputs")
                if not isinstance(structured_outputs, dict):
                    raise StudentError("structured_outputs must be an object")
                choices = structured_outputs.get("choice")
                if choices != list("ABCDE"):
                    raise StudentError("structured_outputs.choice must be exactly A,B,C,D,E")
                if not isinstance(messages, list) or len(messages) < 2:
                    raise StudentError("messages must contain system instructions and user text")
                system_prompts = [
                    message.get("content")
                    for message in messages
                    if isinstance(message, dict) and message.get("role") == "system"
                ]
                user_texts = [
                    message.get("content")
                    for message in messages
                    if isinstance(message, dict) and message.get("role") == "user"
                ]
                if not system_prompts or not isinstance(system_prompts[-1], str):
                    raise StudentError("system prompt is required")
                if not user_texts or not isinstance(user_texts[-1], str) or not user_texts[-1].strip():
                    raise StudentError("user text is required")
                prompt_labels = []
                for line in system_prompts[-1].splitlines():
                    match = re.match(r"^([A-E]):\s*(.*?)\s+—\s+.+$", line.strip())
                    if match:
                        prompt_labels.append((match.group(1), match.group(2)))
                expected_pairs = list(zip("ABCDE", expected_labels))
                if prompt_labels != expected_pairs:
                    raise StudentError(
                        "criterion labels/order do not match the compact student's fixed class map"
                    )
                model_name = request.get("model")
                if not isinstance(model_name, str) or not model_name.strip():
                    raise StudentError("model name is required")
                scores = class_scores(model, user_texts[-1])
                log_probabilities = normalized_log_probabilities(model, user_texts[-1])
                predicted_index = max(
                    range(len(LABELS)),
                    key=lambda index: (scores[LABELS[index]], -index),
                )
                generated_letter = "ABCDE"[predicted_index]
                top_logprobs = [
                    {"token": letter, "logprob": log_probabilities[label]}
                    for letter, label in zip("ABCDE", LABELS)
                ]
                self._reply(
                    200,
                    {
                        "id": "sens-student-local",
                        "object": "chat.completion",
                        "created": 0,
                        "model": model_name,
                        "choices": [
                            {
                                "index": 0,
                                "message": {"role": "assistant", "content": generated_letter},
                                "finish_reason": "stop",
                                "logprobs": {
                                    "content": [{"token": generated_letter, "top_logprobs": top_logprobs}]
                                },
                            }
                        ],
                    },
                )
            except (UnicodeDecodeError, json.JSONDecodeError, StudentError, TypeError, ValueError) as exc:
                self._reply(400, {"error": {"message": str(exc), "type": "invalid_request_error"}})

        def log_message(self, _format: str, *_args: Any) -> None:
            return

    try:
        return ThreadingHTTPServer(("127.0.0.1", port), Handler)
    except OSError as exc:
        raise StudentError(f"не вдалося запустити локальний HTTP сервер: {exc}") from exc


def serve(args: argparse.Namespace) -> int:
    try:
        raw = args.model_path.read_bytes()
        model = json.loads(raw.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise StudentError(f"не вдалося прочитати модель: {exc}") from exc
    if not isinstance(model, dict) or model.get("schema") != MODEL_SCHEMA:
        raise StudentError("несумісна схема моделі")
    if args.port < 1 or args.port > 65535:
        raise StudentError("--port має бути в межах 1..65535")
    api_key = args.api_key or os.environ.get("SENS_SYSTEM_ONE_STUDENT_API_KEY")
    server = create_local_server(model, args.port, api_key)
    print(
        f"System One student ready at http://127.0.0.1:{server.server_port}/v1/chat/completions",
        file=sys.stderr,
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


def predict(args: argparse.Namespace) -> int:
    model_bytes = args.model.read_bytes()
    try:
        model = json.loads(model_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise StudentError(f"файл моделі некоректний: {exc}") from exc
    if model.get("schema") != MODEL_SCHEMA:
        raise StudentError("несумісна схема моделі")
    all_rows, input_raw = read_jsonl(args.input)
    if args.output.resolve() in {args.input.resolve(), args.model.resolve()}:
        raise StudentError("вихід прогнозів не може перезаписати вхідні дані або файл моделі")
    seen: set[str] = set()
    for row in all_rows:
        row_id = str(row.get("id", ""))
        if not row_id or row_id in seen:
            raise StudentError(f"відсутній або повторений id: {row_id!r}")
        seen.add(row_id)
        if row.get("split") not in ("train", "validation", "test"):
            raise StudentError(f"{row_id}: невідомий поділ вибірки")
        if row.get("gold") not in LABELS or not isinstance(row.get("text"), str):
            raise StudentError(f"{row_id}: некоректний приклад для оцінювання")
    rows = [row for row in all_rows if row.get("split") == args.split]
    if not rows:
        raise StudentError(f"у корпусі немає прикладів для split={args.split!r}")
    seen.clear()
    model_sha = digest(model_bytes)
    output: list[dict[str, Any]] = []
    for row in rows:
        row_id = str(row.get("id", ""))
        if not row_id or row_id in seen:
            raise StudentError(f"відсутній або повторений id: {row_id!r}")
        seen.add(row_id)
        if row.get("split") != args.split:
            raise StudentError(f"{row_id}: очікувався split={args.split!r}, отримано {row.get('split')!r}")
        if row.get("gold") not in LABELS or not isinstance(row.get("text"), str):
            raise StudentError(f"{row_id}: некоректний приклад для оцінювання")
        distribution = probabilities(model, row["text"])
        prediction = max(LABELS, key=lambda label: (distribution[label], -LABELS.index(label)))
        output.append(
            {
                "id": row_id,
                "split": args.split,
                "text": row["text"],
                "gold": row["gold"],
                "source": "compact-student-naive-bayes",
                "student_model_sha256": model_sha,
                "dataset_sha256": digest(input_raw),
                "prediction": prediction,
                "confidence": {
                    "numerator": distribution[prediction].numerator * (
                        DENOMINATOR // distribution[prediction].denominator
                    ) if DENOMINATOR % distribution[prediction].denominator == 0
                    else round(float(distribution[prediction]) * DENOMINATOR),
                    "denominator": DENOMINATOR,
                },
                "distribution": {
                    label: {
                        "numerator": round(float(distribution[label]) * DENOMINATOR),
                        "denominator": DENOMINATOR,
                    }
                    for label in LABELS
                },
            }
        )
    atomic_write(
        args.output,
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in output),
        args.overwrite,
    )
    print(
        json.dumps(
            {
                "result": "student-predictions-written",
                "count": len(output),
                "split": args.split,
                "student_model_sha256": model_sha,
                "output": str(args.output),
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    train_parser = commands.add_parser("train", help="навчити компактну CPU-базову лінію")
    train_parser.add_argument("--input", type=Path, default=Path("research/system-one-support-seed-20261022.jsonl"))
    train_parser.add_argument("--teacher", type=Path, help="вихід system-one-teacher-observe; лише train")
    train_parser.add_argument("--output", type=Path, required=True)
    train_parser.add_argument("--smoothing", type=float, default=1.0)
    train_parser.add_argument("--min-count", type=int, default=1)
    train_parser.add_argument("--gold-weight", type=float, help="вага еталонної мітки у суміші з оцінками учителя")
    train_parser.add_argument("--overwrite", action="store_true")
    train_parser.set_defaults(handler=train)

    predict_parser = commands.add_parser("predict", help="оцінити validation або test компактною моделлю")
    predict_parser.add_argument("--model", type=Path, required=True)
    predict_parser.add_argument("--input", type=Path, required=True)
    predict_parser.add_argument("--split", choices=("validation", "test"), default="test")
    predict_parser.add_argument("--output", type=Path, required=True)
    predict_parser.add_argument("--overwrite", action="store_true")
    predict_parser.set_defaults(handler=predict)

    serve_parser = commands.add_parser("serve", help="запустити локальний HTTP-вузол компактного учня")
    serve_parser.add_argument("--model-path", type=Path, required=True)
    serve_parser.add_argument("--port", type=int, default=8100)
    serve_parser.add_argument("--api-key", help="необов'язковий локальний Bearer-ключ; за замовчуванням змінна SENS_SYSTEM_ONE_STUDENT_API_KEY")
    serve_parser.set_defaults(handler=serve)

    args = parser.parse_args()
    try:
        return args.handler(args)
    except (OSError, UnicodeDecodeError, StudentError, KeyError, TypeError, ValueError) as exc:
        print(f"помилка компактного учня System One: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
