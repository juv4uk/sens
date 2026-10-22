#!/usr/bin/env python3
"""Зібрати локальні вчительські оцінки для System One.

Скрипт працює лише з HTTP-сервером на 127.0.0.1. Він не змінює еталонні
мітки та не перетворює прогноз моделі на істину. Результат — окремий JSONL
із точним нормованим розподілом у вигляді чисельник/1_000_000_000.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

LABELS = (
    ("оплата", "Платіж, рахунок, подвійне списання або повернення коштів."),
    ("доставка", "Доставка, кур'єр, відстеження, адреса або відсутня посилка."),
    ("технічне", "Помилка програми, сайту, сервера або функції інтерфейсу."),
    ("обліковий-запис", "Вхід, пароль, профіль, доступ або захист облікового запису."),
    ("невизначено", "Недостатньо даних, змішані теми або запит поза цими класами."),
)
LETTERS = tuple("ABCDE")
DENOMINATOR = 1_000_000_000
MAX_RESPONSE_BYTES = 8 * 1024 * 1024
PROMPT_VERSION = "system-one-routing-v1"


class TeacherError(RuntimeError):
    """Named failure of the local teacher collection step."""


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise TeacherError(f"{path}:{line_number}: некоректний JSON: {exc}") from exc
        if not isinstance(row, dict):
            raise TeacherError(f"{path}:{line_number}: запис має бути об'єктом")
        rows.append(row)
    if not rows:
        raise TeacherError(f"{path}: набір порожній")
    return rows


def validate_endpoint(endpoint: str) -> tuple[str, int, str]:
    parsed = urllib.parse.urlsplit(endpoint)
    try:
        port = parsed.port
    except ValueError as exc:
        raise TeacherError("порт локального endpoint некоректний") from exc
    if (
        parsed.scheme != "http"
        or parsed.hostname != "127.0.0.1"
        or parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
        or parsed.path != "/v1/chat/completions"
        or port is None
        or not 1 <= port <= 65535
    ):
        raise TeacherError(
            "адреса має бути http://127.0.0.1:ПОРТ/v1/chat/completions; "
            "зовнішні адреси заборонені"
        )
    return "127.0.0.1", port, parsed.path


def log_add(left: float, right: float) -> float:
    maximum = max(left, right)
    return maximum + math.log(math.exp(left - maximum) + math.exp(right - maximum))


def teacher_distribution(response: dict[str, Any]) -> tuple[str, str, dict[str, float], dict[str, dict[str, int]]]:
    try:
        choice = response["choices"][0]
        answer = choice["message"]["content"].strip()
        rows = choice["logprobs"]["content"][0]["top_logprobs"]
    except (KeyError, IndexError, TypeError, AttributeError) as exc:
        raise TeacherError(
            "відповідь не містить message.content і першої позиції top_logprobs"
        ) from exc

    if answer not in LETTERS:
        raise TeacherError(f"учитель повернув недозволену мітку {answer!r}")
    by_letter: dict[str, float] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        token = row.get("token")
        score = row.get("logprob")
        if not isinstance(token, str) or not isinstance(score, (int, float)):
            continue
        score = float(score)
        letter = token.strip()
        if letter in LETTERS and math.isfinite(score):
            by_letter[letter] = (
                log_add(by_letter[letter], score) if letter in by_letter else score
            )

    missing = [letter for letter in LETTERS if letter not in by_letter]
    if missing:
        raise TeacherError(
            "модель не надала оцінки всім п'ятьом дозволеним міткам; "
            f"відсутні: {','.join(missing)}. Відсутню ймовірність не вгадуємо"
        )

    maximum = max(by_letter.values())
    exponentials = {letter: math.exp(score - maximum) for letter, score in by_letter.items()}
    total = sum(exponentials.values())
    if not math.isfinite(total) or total <= 0:
        raise TeacherError("логарифми оцінок не утворюють скінченний розподіл")
    scaled = {letter: exponentials[letter] / total * DENOMINATOR for letter in LETTERS}
    counts = {letter: math.floor(scaled[letter]) for letter in LETTERS}
    remaining = DENOMINATOR - sum(counts.values())
    if remaining < 0 or remaining > len(LETTERS):
        raise TeacherError("нестійке округлення нормованого розподілу")
    ranked = sorted(
        LETTERS,
        key=lambda letter: (-(scaled[letter] - math.floor(scaled[letter])), LETTERS.index(letter)),
    )
    for letter in ranked[:remaining]:
        counts[letter] += 1
    if sum(counts.values()) != DENOMINATOR:
        raise TeacherError("внутрішня помилка: сума часток не дорівнює одиниці")

    answer_label = LABELS[LETTERS.index(answer)][0]
    raw_scores = {LABELS[LETTERS.index(letter)][0]: by_letter[letter] for letter in LETTERS}
    distribution = {
        LABELS[LETTERS.index(letter)][0]: {
            "numerator": counts[letter],
            "denominator": DENOMINATOR,
        }
        for letter in LETTERS
    }
    probability_label = max(
        (label for label, _description in LABELS),
        key=lambda label: (distribution[label]["numerator"], -[item[0] for item in LABELS].index(label)),
    )
    return answer_label, probability_label, raw_scores, distribution


def call_teacher(
    endpoint: str,
    model: str,
    api_key: str | None,
    prompt: str,
    text: str,
    timeout: float,
) -> dict[str, Any]:
    validate_endpoint(endpoint)
    payload = {
        "model": model,
        "max_tokens": 1,
        "temperature": 0,
        "logprobs": True,
        "top_logprobs": 20,
        "messages": [
            {"role": "system", "content": prompt},
            {"role": "user", "content": text},
        ],
        "structured_outputs": {"choice": list(LETTERS)},
        "chat_template_kwargs": {"enable_thinking": False},
    }
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    if api_key:
        if "\r" in api_key or "\n" in api_key:
            raise TeacherError("ключ локального сервера містить заборонені символи")
        headers["Authorization"] = f"Bearer {api_key}"
    request = urllib.request.Request(
        endpoint,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read(MAX_RESPONSE_BYTES + 1)
    except urllib.error.HTTPError as exc:
        body = exc.read(2000).decode("utf-8", errors="replace")
        raise TeacherError(f"локальний сервер повернув HTTP {exc.code}: {body}") from exc
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise TeacherError(f"не вдалося звернутися до локального вчителя: {exc}") from exc
    if len(raw) > MAX_RESPONSE_BYTES:
        raise TeacherError("відповідь локального вчителя перевищила 8 MiB")
    try:
        result = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise TeacherError(f"локальний учитель повернув некоректний JSON: {exc}") from exc
    if not isinstance(result, dict):
        raise TeacherError("корінь відповіді моделі має бути JSON-об'єктом")
    return result


def atomic_write(path: Path, rows: list[dict[str, Any]], overwrite: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and not overwrite:
        raise TeacherError(f"вихідний файл вже існує: {path}; додайте --overwrite свідомо")
    handle = tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        newline="\n",
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
        delete=False,
    )
    temp_path = Path(handle.name)
    try:
        with handle:
            for row in rows:
                handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
        os.replace(temp_path, path)
    except Exception:
        temp_path.unlink(missing_ok=True)
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path("research/system-one-support-seed-20261022.jsonl"))
    parser.add_argument("--output", type=Path, required=True, help="новий JSONL; не перезаписується без --overwrite")
    parser.add_argument("--model", required=True, help="точне ім'я/ревізія, яку знає локальний сервер")
    parser.add_argument(
        "--endpoint",
        default=os.environ.get("SENS_SYSTEM_ONE_ENDPOINT", "http://127.0.0.1:8000/v1/chat/completions"),
    )
    parser.add_argument("--split", choices=("train", "validation", "test"), default="train")
    parser.add_argument("--allow-holdout", action="store_true", help="обов'язково для validation/test")
    parser.add_argument("--limit", type=int, default=0, help="необов'язкове обмеження для пробного запуску")
    parser.add_argument("--timeout", type=float, default=90.0)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    try:
        validate_endpoint(args.endpoint)
        if not args.model.strip():
            raise TeacherError("--model не може бути порожнім")
        if args.timeout <= 0:
            raise TeacherError("--timeout має бути додатним")
        if args.output.exists() and not args.overwrite:
            raise TeacherError(f"вихідний файл вже існує: {args.output}; додайте --overwrite свідомо")
        if args.limit < 0:
            raise TeacherError("--limit не може бути від'ємним")
        if args.split != "train" and not args.allow_holdout:
            raise TeacherError("для validation/test потрібен явний --allow-holdout")
        input_path = args.input.resolve()
        output_path = args.output.resolve()
        if input_path == output_path:
            raise TeacherError("вхідний seed-корпус не можна замінити виходом учителя")

        input_bytes = args.input.read_bytes()
        dataset_sha256 = hashlib.sha256(input_bytes).hexdigest()
        source_rows = read_jsonl(args.input)
        rows = [row for row in source_rows if row.get("split") == args.split]
        if args.limit:
            rows = rows[: args.limit]
        if not rows:
            raise TeacherError(f"у наборі немає рядків для розділу {args.split!r}")
        allowed_labels = {label for label, _ in LABELS}
        for row in rows:
            if not isinstance(row.get("text"), str) or not row["text"].strip():
                raise TeacherError(f"{row.get('id', '<без id>')}: відсутній текст")
            if row.get("gold") not in allowed_labels:
                raise TeacherError(f"{row.get('id', '<без id>')}: невідома еталонна мітка")
            if not row.get("id"):
                raise TeacherError("кожен приклад мусить мати сталий id")

        criteria = "\n".join(
            f"{letter}: {label} — {description}"
            for letter, (label, description) in zip(LETTERS, LABELS)
        )
        prompt = (
            "Ти класифікуєш українські звернення підтримки. Оціни тільки наведені класи.\n"
            f"Дозволені класи:\n{criteria}\n\n"
            "Поверни рівно одну велику латинську літеру A, B, C, D або E, "
            "яка відповідає найкращому класу. Не додавай пояснень. "
            "Якщо даних замало, обери E."
        )
        prompt_sha256 = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
        api_key = os.environ.get("SENS_SYSTEM_ONE_API_KEY")
        observations: list[dict[str, Any]] = []
        for index, row in enumerate(rows, 1):
            response = call_teacher(
                args.endpoint, args.model, api_key, prompt, row["text"], args.timeout
            )
            generated_label, prediction, scores, distribution = teacher_distribution(response)
            top_confidence_numerator = max(
                value["numerator"] for value in distribution.values()
            )
            observations.append(
                {
                    "id": row["id"],
                    "split": row["split"],
                    "text": row["text"],
                    "gold": row["gold"],
                    "source": row.get("source", "unspecified"),
                    "dataset_sha256": dataset_sha256,
                    "prompt_version": PROMPT_VERSION,
                    "prompt_sha256": prompt_sha256,
                    "teacher": args.model,
                    "endpoint": args.endpoint,
                    "method": "vllm-top-logprobs-softmax-largest-remainder-1e9",
                    "teacher_scores": scores,
                    "teacher_prediction": prediction,
                    "teacher_generated_label": generated_label,
                    "generated_label_matches_top_probability": generated_label == prediction,
                    "teacher_confidence": {
                        "numerator": top_confidence_numerator,
                        "denominator": DENOMINATOR,
                    },
                    "teacher_distribution": distribution,
                }
            )
            print(f"[{index}/{len(rows)}] {row['id']} -> {prediction}", file=sys.stderr)

        atomic_write(args.output, observations, args.overwrite)
        print(
            json.dumps(
                {
                    "result": "observations-written",
                    "count": len(observations),
                    "split": args.split,
                    "dataset_sha256": dataset_sha256,
                    "output": str(args.output),
                    "teacher": args.model,
                    "predictions_are_not_gold": True,
                },
                ensure_ascii=False,
                sort_keys=True,
            )
        )
        return 0
    except (OSError, TeacherError) as exc:
        print(f"помилка збору оцінок учителя: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
