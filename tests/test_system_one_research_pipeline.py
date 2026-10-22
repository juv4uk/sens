"""Точкова перевірка локального вчителя, компактного учня та оцінювання."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import tempfile
import threading
import unicodedata
import unittest
from argparse import Namespace
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_research_module(filename: str, module_name: str):
    path = ROOT / "research" / filename
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise AssertionError(f"не вдалося завантажити модуль {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


teacher = load_research_module(
    "system-one-teacher-observe-20261022.py", "system_one_teacher_observe"
)
student = load_research_module(
    "system-one-compact-student-20261022.py", "system_one_compact_student"
)
evaluator = load_research_module(
    "system-one-evaluate-20261022.py", "system_one_evaluate"
)
calibrator = load_research_module(
    "system-one-calibrate-20261022.py", "system_one_calibrate"
)
comparison = load_research_module(
    "system-one-compare-20261022.py", "system_one_compare"
)
transformer_student = load_research_module(
    "system-one-transformer-student-20261022.py", "system_one_transformer_student"
)


def write_jsonl(path: Path, rows: list[dict]) -> bytes:
    content = "".join(
        json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows
    ).encode("utf-8")
    path.write_bytes(content)
    return content


def exact_distribution(gold: str, numerator: int = 800_000_000) -> dict:
    remainder = 1_000_000_000 - numerator
    other = remainder // (len(student.LABELS) - 1)
    counts = {label: other for label in student.LABELS}
    counts[gold] = numerator
    # У тестовій частці знаменник незмінний, а сума чисельників рівно 1e9.
    assert sum(counts.values()) == 1_000_000_000
    return {
        label: {"numerator": value, "denominator": 1_000_000_000}
        for label, value in counts.items()
    }


class SystemOneResearchPipelineTests(unittest.TestCase):
    def test_teacher_endpoint_is_loopback_only_and_distribution_is_exact(self):
        with self.assertRaises(teacher.TeacherError):
            teacher.validate_endpoint("http://example.com:8000/v1/chat/completions")
        with self.assertRaises(teacher.TeacherError):
            teacher.validate_endpoint("http://127.0.0.1:bad/v1/chat/completions")

        scores = [0.0, -0.1, -1.0, -2.0, -3.0]
        response = {
            "choices": [
                {
                    "message": {"content": "A"},
                    "logprobs": {
                        "content": [
                            {
                                "top_logprobs": [
                                    {"token": letter, "logprob": score}
                                    for letter, score in zip("ABCDE", scores)
                                ]
                            }
                        ]
                    },
                }
            ]
        }
        generated, probability_winner, raw_scores, distribution = (
            teacher.teacher_distribution(response)
        )
        self.assertEqual(generated, "оплата")
        self.assertEqual(probability_winner, "оплата")
        self.assertEqual(set(raw_scores), set(student.LABELS))
        self.assertEqual(
            sum(value["numerator"] for value in distribution.values()),
            1_000_000_000,
        )
        self.assertTrue(
            all(value["denominator"] == 1_000_000_000 for value in distribution.values())
        )

        missing = {
            "choices": [
                {
                    "message": {"content": "A"},
                    "logprobs": {
                        "content": [
                            {"top_logprobs": [{"token": "A", "logprob": 0.0}]}
                        ]
                    },
                }
            ]
        }
        with self.assertRaises(teacher.TeacherError):
            teacher.teacher_distribution(missing)

    def test_teacher_http_request_uses_local_constrained_endpoint(self):
        captured = {}

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                length = int(self.headers.get("Content-Length", "0"))
                captured["payload"] = json.loads(self.rfile.read(length).decode("utf-8"))
                captured["authorization"] = self.headers.get("Authorization")
                body = json.dumps(
                    {
                        "choices": [
                            {
                                "message": {"content": "A"},
                                "logprobs": {
                                    "content": [
                                        {
                                            "top_logprobs": [
                                                {"token": letter, "logprob": score}
                                                for letter, score in zip(
                                                    "ABCDE", [0.0, -0.5, -1.0, -1.5, -2.0]
                                                )
                                            ]
                                        }
                                    ]
                                },
                            }
                        ]
                    }
                ).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, _format, *_args):
                return

        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            endpoint = f"http://127.0.0.1:{server.server_port}/v1/chat/completions"
            response = teacher.call_teacher(
                endpoint=endpoint,
                model="fixture-model",
                api_key="fixture-secret",
                prompt="Вибери тільки один дозволений маршрут.",
                text="Мене двічі оштрафували за одну операцію.",
                timeout=3.0,
            )
            self.assertEqual(captured["authorization"], "Bearer fixture-secret")
            self.assertEqual(captured["payload"]["model"], "fixture-model")
            self.assertEqual(captured["payload"]["max_tokens"], 1)
            self.assertTrue(captured["payload"]["logprobs"])
            self.assertEqual(captured["payload"]["top_logprobs"], 20)
            self.assertEqual(
                captured["payload"]["structured_outputs"]["choice"],
                ["A", "B", "C", "D", "E"],
            )
            self.assertEqual(
                captured["payload"]["messages"][1]["content"],
                "Мене двічі оштрафували за одну операцію.",
            )
            generated, winner, _scores, distribution = teacher.teacher_distribution(response)
            self.assertEqual(generated, "оплата")
            self.assertEqual(winner, "оплата")
            self.assertEqual(
                sum(value["numerator"] for value in distribution.values()),
                1_000_000_000,
            )
        finally:
            server.shutdown()
            thread.join(timeout=2.0)
            server.server_close()

    def test_teacher_refuses_loopback_redirects(self):
        captured = {"redirected": False}

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                self.send_response(302)
                self.send_header(
                    "Location",
                    f"http://127.0.0.1:{self.server.server_port}/redirect-target",
                )
                self.end_headers()

            def do_GET(self):
                if self.path == "/redirect-target":
                    captured["redirected"] = True
                    body = json.dumps({"choices": []}).encode("utf-8")
                    self.send_response(200)
                    self.send_header("Content-Length", str(len(body)))
                    self.end_headers()
                    self.wfile.write(body)
                else:
                    self.send_error(404)

            def log_message(self, _format, *_args):
                return

        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            endpoint = f"http://127.0.0.1:{server.server_port}/v1/chat/completions"
            with self.assertRaises(teacher.TeacherError):
                teacher.call_teacher(
                    endpoint=endpoint,
                    model="fixture-model",
                    api_key="do-not-forward",
                    prompt="Тест перенаправлення.",
                    text="Текст не має залишати локальну адресу.",
                    timeout=3.0,
                )
            self.assertFalse(captured["redirected"])
        finally:
            server.shutdown()
            thread.join(timeout=2.0)
            server.server_close()

    def test_compact_student_trains_from_gold_or_soft_targets_and_evaluates_holdout(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            train_rows = []
            for index, label in enumerate(student.LABELS):
                train_rows.append(
                    {
                        "id": f"train-{index}-a",
                        "split": "train",
                        "text": f"характерніслова{index} приклад {label}",
                        "gold": label,
                    }
                )
                train_rows.append(
                    {
                        "id": f"train-{index}-b",
                        "split": "train",
                        "text": f"додатковіслова{index} звернення {label}",
                        "gold": label,
                    }
                )
            seed_path = root / "seed.jsonl"
            seed_raw = write_jsonl(seed_path, train_rows)
            seed_sha = hashlib.sha256(seed_raw).hexdigest()

            teacher_rows = []
            for row in train_rows:
                teacher_rows.append(
                    {
                        "id": row["id"],
                        "split": "train",
                        "text": row["text"],
                        "gold": row["gold"],
                        "dataset_sha256": seed_sha,
                        "teacher_distribution": exact_distribution(row["gold"]),
                    }
                )
            teacher_path = root / "teacher.jsonl"
            teacher_raw = write_jsonl(teacher_path, teacher_rows)
            teacher_sha = hashlib.sha256(teacher_raw).hexdigest()

            gold_model_path = root / "student-gold.json"
            self.assertEqual(
                student.train(
                    Namespace(
                        input=seed_path,
                        teacher=None,
                        output=gold_model_path,
                        smoothing=1.0,
                        min_count=1,
                        gold_weight=None,
                        overwrite=False,
                    )
                ),
                0,
            )
            gold_model = json.loads(gold_model_path.read_text(encoding="utf-8"))
            self.assertFalse(gold_model["teacher_used"])
            self.assertEqual(gold_model["gold_weight"], 1.0)

            model_path = root / "student-soft.json"

            self.assertEqual(
                student.train(
                    Namespace(
                        input=seed_path,
                        teacher=teacher_path,
                        output=model_path,
                        smoothing=1.0,
                        min_count=1,
                        gold_weight=0.25,
                        overwrite=False,
                    )
                ),
                0,
            )
            model = json.loads(model_path.read_text(encoding="utf-8"))
            self.assertEqual(model["schema"], student.MODEL_SCHEMA)
            self.assertEqual(model["training_count"], len(train_rows))
            self.assertEqual(model["training_dataset_sha256"], seed_sha)
            self.assertEqual(model["teacher_observations_sha256"], teacher_sha)
            self.assertTrue(model["teacher_used"])
            self.assertGreater(len(model["vocabulary"]), 0)

            holdout_rows = [
                {
                    "id": f"test-{index}",
                    "split": "test",
                    "text": f"характерніслова{index} нове повідомлення {label}",
                    "gold": label,
                }
                for index, label in enumerate(student.LABELS)
            ]
            test_path = root / "test.jsonl"
            write_jsonl(test_path, holdout_rows)
            predictions_path = root / "predictions.jsonl"
            self.assertEqual(
                student.predict(
                    Namespace(
                        model=model_path,
                        input=test_path,
                        split="test",
                        output=predictions_path,
                        overwrite=False,
                    )
                ),
                0,
            )
            predictions = [
                json.loads(line)
                for line in predictions_path.read_text(encoding="utf-8").splitlines()
            ]
            self.assertEqual(len(predictions), len(holdout_rows))
            self.assertTrue(
                all(
                    sum(value["numerator"] for value in row["distribution"].values())
                    == 1_000_000_000
                    for row in predictions
                )
            )
            report = evaluator.score(
                predictions, threshold=0.5, bins=5, expected_split="test"
            )
            self.assertEqual(report["status"], "measured")
            self.assertEqual(report["count"], len(holdout_rows))
            self.assertIn("macro_f1", report["metrics"])
            self.assertIn("multiclass_brier_sum_over_examples", report["metrics"])
            self.assertIn("top_class_ece", report["metrics"])
            self.assertIn("selective_risk_at_threshold", report["metrics"])

    def test_compact_student_serves_same_local_distribution_contract_as_teacher(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            seed_path = ROOT / "research" / "system-one-support-seed-20261022.jsonl"
            model_path = root / "student.json"
            self.assertEqual(
                student.train(
                    Namespace(
                        input=seed_path,
                        teacher=None,
                        output=model_path,
                        smoothing=1.0,
                        min_count=1,
                        gold_weight=None,
                        overwrite=False,
                    )
                ),
                0,
            )
            model = json.loads(model_path.read_text(encoding="utf-8"))
            # Перевіряємо, що HTTP-вузол справді застосовує задану температуру.
            model["calibration_temperature"] = 2.0
            server = student.create_local_server(model, port=0, api_key="student-secret")
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                endpoint = f"http://127.0.0.1:{server.server_port}/v1/chat/completions"
                prompt = "\n".join(
                    f"{letter}: {label} — {description}"
                    for letter, (label, description) in zip(
                        "ABCDE",
                        [
                            ("оплата", "Платіж або повернення коштів."),
                            ("доставка", "Посилка або кур'єр."),
                            ("технічне", "Помилка програми або сайту."),
                            ("обліковий-запис", "Вхід, пароль або профіль."),
                            ("невизначено", "Недостатньо даних або змішана тема."),
                        ],
                    )
                )
                response = teacher.call_teacher(
                    endpoint=endpoint,
                    model="compact-student-fixture",
                    api_key="student-secret",
                    prompt=prompt,
                    text="З мене двічі списали гроші за одне замовлення.",
                    timeout=3.0,
                )
                generated, winner, _scores, distribution = teacher.teacher_distribution(response)
                self.assertIn(generated, student.LABELS)
                self.assertIn(winner, student.LABELS)
                self.assertEqual(
                    sum(value["numerator"] for value in distribution.values()),
                    1_000_000_000,
                )
                self.assertEqual(
                    len(distribution),
                    5,
                )
                expected_distribution = student.probabilities(
                    model, "З мене двічі списали гроші за одне замовлення."
                )
                for label, expected_probability in expected_distribution.items():
                    actual_probability = (
                        distribution[label]["numerator"]
                        / distribution[label]["denominator"]
                    )
                    self.assertAlmostEqual(
                        actual_probability, float(expected_probability), places=8
                    )
                with self.assertRaises(teacher.TeacherError):
                    teacher.call_teacher(
                        endpoint=endpoint,
                        model="compact-student-fixture",
                        api_key="wrong-key",
                        prompt=prompt,
                        text="Перевірка авторизації.",
                        timeout=3.0,
                    )
                bad_prompt = prompt.replace("A: оплата", "A: невизначено", 1)
                with self.assertRaises(teacher.TeacherError):
                    teacher.call_teacher(
                        endpoint=endpoint,
                        model="compact-student-fixture",
                        api_key="student-secret",
                        prompt=bad_prompt,
                        text="Не повинно бути класифіковано з іншою мапою.",
                        timeout=3.0,
                    )
            finally:
                server.shutdown()
                thread.join(timeout=2.0)
                server.server_close()

    def test_adversarial_challenge_is_holdout_only_and_disjoint_from_seed(self):
        seed_path = ROOT / "research" / "system-one-support-seed-20261022.jsonl"
        challenge_path = ROOT / "research" / "system-one-support-challenge-20261022.jsonl"
        seed_rows, _ = student.read_jsonl(seed_path)
        challenge_rows, challenge_raw = student.read_jsonl(challenge_path)
        self.assertEqual(len(challenge_rows), 60)
        self.assertTrue(all(row.get("evaluation_only") is True for row in challenge_rows))
        self.assertTrue(all(row.get("split") == "test" for row in challenge_rows))
        self.assertTrue(
            all(row.get("source") == "synthetic-adversarial-challenge" for row in challenge_rows)
        )
        self.assertEqual(
            {label: sum(row.get("gold") == label for row in challenge_rows) for label in student.LABELS},
            {label: 12 for label in student.LABELS},
        )
        normalize = lambda value: unicodedata.normalize("NFKC", value).casefold().strip()
        seed_texts = {normalize(row["text"]) for row in seed_rows}
        challenge_texts = [normalize(row["text"]) for row in challenge_rows]
        self.assertEqual(len(set(challenge_texts)), len(challenge_texts))
        self.assertTrue(seed_texts.isdisjoint(challenge_texts))
        self.assertEqual(len({row["id"] for row in challenge_rows}), len(challenge_rows))
        self.assertEqual(
            hashlib.sha256(challenge_raw).hexdigest(),
            hashlib.sha256(challenge_path.read_bytes()).hexdigest(),
        )

        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "must-not-be-trained.json"
            with self.assertRaises(student.StudentError):
                student.train(
                    Namespace(
                        input=challenge_path,
                        teacher=None,
                        output=output,
                        smoothing=1.0,
                        min_count=1,
                        gold_weight=None,
                        overwrite=False,
                    )
                )
            self.assertFalse(output.exists())

    def test_committed_seed_trains_and_predicts_only_selected_splits(self):
        seed_path = ROOT / "research" / "system-one-support-seed-20261022.jsonl"
        rows, raw = student.read_jsonl(seed_path)
        self.assertEqual(len(rows), 60)
        self.assertEqual(
            {split: sum(row["split"] == split for row in rows) for split in ("train", "validation", "test")},
            {"train": 40, "validation": 10, "test": 10},
        )
        self.assertEqual(
            {label: sum(row["gold"] == label for row in rows) for label in student.LABELS},
            {label: 12 for label in student.LABELS},
        )
        self.assertEqual(len({row["text"] for row in rows}), 60)
        self.assertTrue(all(row["source"] == "synthetic-curated-seed" for row in rows))

        self.assertEqual(len({row["id"] for row in rows}), len(rows))
        normalized_texts = {
            unicodedata.normalize("NFKC", row["text"]).casefold().strip()
            for row in rows
        }
        self.assertEqual(len(normalized_texts), len(rows))
        for split, expected_count in (("train", 8), ("validation", 2), ("test", 2)):
            rows_in_split = [row for row in rows if row["split"] == split]
            self.assertEqual(len(rows_in_split), expected_count * len(student.LABELS))
            self.assertEqual(
                {label: sum(row["gold"] == label for row in rows_in_split) for label in student.LABELS},
                {label: expected_count for label in student.LABELS},
            )

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            model_path = root / "seed-student.json"
            self.assertEqual(
                student.train(
                    Namespace(
                        input=seed_path,
                        teacher=None,
                        output=model_path,
                        smoothing=1.0,
                        min_count=1,
                        gold_weight=None,
                        overwrite=False,
                    )
                ),
                0,
            )
            model = json.loads(model_path.read_text(encoding="utf-8"))
            self.assertEqual(model["training_count"], 40)
            self.assertEqual(model["training_dataset_sha256"], hashlib.sha256(raw).hexdigest())

            prediction_path = root / "seed-test-predictions.jsonl"
            self.assertEqual(
                student.predict(
                    Namespace(
                        model=model_path,
                        input=seed_path,
                        split="test",
                        output=prediction_path,
                        overwrite=False,
                    )
                ),
                0,
            )
            predictions = [
                json.loads(line)
                for line in prediction_path.read_text(encoding="utf-8").splitlines()
            ]
            self.assertEqual(len(predictions), 10)
            self.assertTrue(all(row["split"] == "test" for row in predictions))
            report = evaluator.score(
                predictions, threshold=0.8, bins=10, expected_split="test"
            )
            self.assertEqual(report["count"], 10)
            self.assertEqual(report["split"], "test")

    def test_challenge_comparison_rejects_seed_overlap_and_non_holdout_rows(self):
        seed_path = ROOT / "research" / "system-one-support-seed-20261022.jsonl"
        challenge_path = ROOT / "research" / "system-one-support-challenge-20261022.jsonl"
        seed_rows, _ = student.read_jsonl(seed_path)
        challenge_rows, _ = student.read_jsonl(challenge_path)

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            overlap_rows = [dict(row) for row in challenge_rows]
            overlap_rows[0]["text"] = seed_rows[0]["text"]
            overlap_path = root / "overlap.jsonl"
            write_jsonl(overlap_path, overlap_rows)
            with self.assertRaises(comparison.ComparisonError):
                comparison.validate_challenge_corpus(overlap_path, seed_rows)

            train_leak_rows = [dict(row) for row in challenge_rows]
            train_leak_rows[0]["evaluation_only"] = False
            train_leak_path = root / "not-holdout.jsonl"
            write_jsonl(train_leak_path, train_leak_rows)
            with self.assertRaises(comparison.ComparisonError):
                comparison.validate_challenge_corpus(train_leak_path, seed_rows)

            duplicate_rows = [dict(row) for row in challenge_rows]
            duplicate_rows[1]["text"] = duplicate_rows[0]["text"].upper()
            duplicate_path = root / "duplicate-normalized.jsonl"
            write_jsonl(duplicate_path, duplicate_rows)
            with self.assertRaises(comparison.ComparisonError):
                comparison.validate_challenge_corpus(duplicate_path, seed_rows)

    def test_comparison_runner_keeps_holdout_out_of_training(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            seed_rows = []
            for label_index, label in enumerate(student.LABELS):
                for split, repeat in (("train", 2), ("validation", 1), ("test", 1)):
                    for index in range(repeat):
                        seed_rows.append(
                            {
                                "id": f"{split}-{label_index}-{index}",
                                "split": split,
                                "text": f"слово{label_index} приклад{index} тема {label}",
                                "gold": label,
                                "source": "synthetic-curated-seed",
                                "version": 1,
                            }
                        )
            seed_path = root / "seed.jsonl"
            seed_raw = write_jsonl(seed_path, seed_rows)
            seed_sha = hashlib.sha256(seed_raw).hexdigest()
            teacher_paths = {}
            for split in ("train", "validation", "test"):
                observations = []
                for row in seed_rows:
                    if row["split"] != split:
                        continue
                    observations.append(
                        {
                            **row,
                            "dataset_sha256": seed_sha,
                            "prompt_version": "fixture-prompt-v1",
                            "teacher": "fixture-teacher-v1",
                            "teacher_distribution": exact_distribution(row["gold"]),
                            "teacher_prediction": row["gold"],
                            "teacher_generated_label": row["gold"],
                            "generated_label_matches_top_probability": True,
                        }
                    )
                output = root / f"teacher-{split}.jsonl"
                write_jsonl(output, observations)
                teacher_paths[split] = output

            # Узгодженість фактично згенерованої літери з argmax має бути перевірюваною.
            test_teacher_rows, _ = student.read_jsonl(teacher_paths["test"])
            inconsistent = [dict(row) for row in test_teacher_rows]
            inconsistent[0]["generated_label_matches_top_probability"] = False
            inconsistent_path = root / "teacher-test-inconsistent.jsonl"
            write_jsonl(inconsistent_path, inconsistent)
            with self.assertRaises(comparison.ComparisonError):
                comparison.validate_teacher_file(
                    inconsistent_path,
                    [row for row in seed_rows if row["split"] == "test"],
                    "test",
                    seed_sha,
                )

            output_dir = root / "comparison"
            report = comparison.run(
                Namespace(
                    input=seed_path,
                    teacher_train=teacher_paths["train"],
                    teacher_validation=teacher_paths["validation"],
                    teacher_test=teacher_paths["test"],
                    output_dir=output_dir,
                    threshold=0.5,
                    bins=5,
                    smoothing=1.0,
                    min_count=1,
                    gold_weight=0.25,
                    min_temperature=0.05,
                    max_temperature=20.0,
                    grid_points=51,
                    overwrite=False,
                )
            )
            self.assertEqual(report["result"], "measured")
            self.assertEqual(report["dataset_sha256"], seed_sha)
            self.assertEqual(report["teacher_observations_used_for_training"], ["train"])
            self.assertFalse(report["test_used_for_training_or_calibration"])
            for split in ("train", "validation", "test"):
                agreement = report["teacher_decoding_agreement"][split]
                self.assertEqual(agreement["agreement_rate"], 1.0)
                self.assertEqual(agreement["disagreements"], 0)
            self.assertEqual(set(report["comparison"]), {"validation", "test"})
            for split in ("validation", "test"):
                self.assertEqual(
                    set(report["comparison"][split]),
                    {"teacher", "student_gold", "student_soft"},
                )
                for model_name in ("teacher", "student_gold", "student_soft"):
                    self.assertIn("accuracy", report["comparison"][split][model_name])
            for result in report["calibration"].values():
                self.assertLessEqual(result["nll_after"], result["nll_before"] + 1e-12)
            saved = json.loads((output_dir / "comparison.json").read_text(encoding="utf-8"))
            self.assertFalse(saved["test_used_for_training_or_calibration"])
            self.assertTrue((output_dir / "student-gold-test.jsonl").is_file())
            self.assertTrue((output_dir / "student-soft-test.jsonl").is_file())

            # Приєднуємо фіктивні прогнозування трансформера до тих самих метрик.
            # Ваги справжньої моделі не завантажуються; перевіряється лише контракт.
            transformer_paths = {}
            for split in ("validation", "test"):
                rows = []
                for row in seed_rows:
                    if row["split"] != split:
                        continue
                    rows.append(
                        {
                            "id": row["id"],
                            "split": split,
                            "text": row["text"],
                            "gold": row["gold"],
                            "model_schema": "sens.system-one.transformer-student/1",
                            "base_model": "fixture-mmbert",
                            "training_dataset_sha256": seed_sha,
                            "calibration_temperature": 1.25,
                            "distribution": exact_distribution(row["gold"]),
                        }
                    )
                transformer_path = root / f"transformer-{split}.jsonl"
                write_jsonl(transformer_path, rows)
                transformer_paths[split] = transformer_path

            challenge_path = ROOT / "research" / "system-one-support-challenge-20261022.jsonl"
            challenge_rows, challenge_raw = student.read_jsonl(challenge_path)
            challenge_sha = hashlib.sha256(challenge_raw).hexdigest()
            challenge_teacher_rows = [
                {
                    **row,
                    "dataset_sha256": challenge_sha,
                    "prompt_version": "fixture-prompt-v1",
                    "teacher": "fixture-teacher-v1",
                    "teacher_distribution": exact_distribution(row["gold"]),
                    "teacher_prediction": row["gold"],
                            "teacher_generated_label": row["gold"],
                            "generated_label_matches_top_probability": True,
                }
                for row in challenge_rows
            ]
            challenge_teacher_path = root / "teacher-challenge.jsonl"
            write_jsonl(challenge_teacher_path, challenge_teacher_rows)
            challenge_transformer_rows = [
                {
                    "id": row["id"],
                    "split": "test",
                    "text": row["text"],
                    "gold": row["gold"],
                    "model_schema": "sens.system-one.transformer-student/1",
                    "base_model": "fixture-mmbert",
                    "training_dataset_sha256": seed_sha,
                    "calibration_temperature": 1.25,
                    "distribution": exact_distribution(row["gold"]),
                }
                for row in challenge_rows
            ]
            challenge_transformer_path = root / "challenge-transformer.jsonl"
            write_jsonl(challenge_transformer_path, challenge_transformer_rows)

            transformer_output = root / "comparison-with-transformer"
            transformer_report = comparison.run(
                Namespace(
                    input=seed_path,
                    teacher_train=teacher_paths["train"],
                    teacher_validation=teacher_paths["validation"],
                    teacher_test=teacher_paths["test"],
                    transformer_validation_predictions=transformer_paths["validation"],
                    transformer_test_predictions=transformer_paths["test"],
                    challenge_input=challenge_path,
                    challenge_teacher=challenge_teacher_path,
                    challenge_transformer_predictions=challenge_transformer_path,
                    output_dir=transformer_output,
                    threshold=0.5,
                    bins=5,
                    smoothing=1.0,
                    min_count=1,
                    gold_weight=0.25,
                    min_temperature=0.05,
                    max_temperature=20.0,
                    grid_points=51,
                    overwrite=False,
                )
            )
            self.assertIn("student_transformer", transformer_report["comparison"]["validation"])
            self.assertIn("student_transformer", transformer_report["comparison"]["test"])
            self.assertEqual(
                transformer_report["transformer_student"]["validation"]["base_model"],
                "fixture-mmbert",
            )
            self.assertFalse(transformer_report["test_used_for_training_or_calibration"])
            challenge_report = transformer_report["challenge"]
            self.assertTrue(challenge_report["evaluation_only"])
            self.assertEqual(challenge_report["dataset_sha256"], challenge_sha)
            self.assertEqual(challenge_report["record_count"], 60)
            self.assertFalse(challenge_report["test_used_for_training_or_calibration"])
            self.assertFalse(challenge_report["threshold_selected_on_challenge"])
            self.assertEqual(
                challenge_report["teacher_decoding_agreement"]["agreement_rate"],
                1.0,
            )
            self.assertEqual(
                set(challenge_report["comparison"]),
                {"teacher", "student_gold", "student_soft", "student_transformer"},
            )
            self.assertTrue((transformer_output / "challenge-student-gold.jsonl").is_file())
            self.assertTrue((transformer_output / "challenge-student-soft.jsonl").is_file())

            # Неправильний SHA test-виводу має відхилятися до навчання або запису моделі.
            bad_test_rows, _ = student.read_jsonl(transformer_paths["test"])
            bad_test_rows[0]["training_dataset_sha256"] = "wrong-sha"
            bad_test_path = root / "transformer-test-bad.jsonl"
            write_jsonl(bad_test_path, bad_test_rows)
            bad_output = root / "comparison-bad-transformer"
            with self.assertRaises(comparison.ComparisonError):
                comparison.run(
                    Namespace(
                        input=seed_path,
                        teacher_train=teacher_paths["train"],
                        teacher_validation=teacher_paths["validation"],
                        teacher_test=teacher_paths["test"],
                        transformer_validation_predictions=transformer_paths["validation"],
                        transformer_test_predictions=bad_test_path,
                        output_dir=bad_output,
                        threshold=0.5,
                        bins=5,
                        smoothing=1.0,
                        min_count=1,
                        gold_weight=0.25,
                        min_temperature=0.05,
                        max_temperature=20.0,
                        grid_points=51,
                        overwrite=False,
                    )
                )
            self.assertFalse((bad_output / "student-gold-uncalibrated.json").exists())

    def test_temperature_calibration_uses_validation_only_and_nll_does_not_worsen(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            seed_path = ROOT / "research" / "system-one-support-seed-20261022.jsonl"
            model_path = root / "uncalibrated.json"
            self.assertEqual(
                student.train(
                    Namespace(
                        input=seed_path,
                        teacher=None,
                        output=model_path,
                        smoothing=1.0,
                        min_count=1,
                        gold_weight=None,
                        overwrite=False,
                    )
                ),
                0,
            )
            model = json.loads(model_path.read_text(encoding="utf-8"))
            rows, raw = student.read_jsonl(seed_path)
            corpus_sha = hashlib.sha256(raw).hexdigest()
            calibrated, report = calibrator.fit_temperature(
                model, rows, corpus_sha, grid_points=101
            )
            self.assertEqual(calibrated["calibration"]["split"], "validation")
            self.assertEqual(calibrated["calibration"]["count"], 10)
            self.assertFalse(calibrated["calibration"]["used_test_split"])
            self.assertGreater(calibrated["calibration_temperature"], 0.0)
            self.assertTrue(report["nll_not_worsened"])
            self.assertLessEqual(report["nll_after"], report["nll_before"] + 1e-12)
            test_row = next(row for row in rows if row["split"] == "test")
            distribution = student.probabilities(calibrated, test_row["text"])
            self.assertEqual(sum(distribution.values()), 1)
            with self.assertRaises(calibrator.CalibrationError):
                calibrator.fit_temperature(
                    model,
                    [row for row in rows if row["split"] == "test"],
                    corpus_sha,
                    grid_points=101,
                )
            with self.assertRaises(calibrator.CalibrationError):
                calibrator.fit_temperature(
                    model, rows, "wrong-corpus-sha", grid_points=101
                )

    def test_transformer_helpers_keep_exact_distribution_and_validation_boundary(self):
        probabilities = transformer_student.normalized_probabilities(
            [5.0, -2.0, 1.0, 0.0, 3.0], temperature=2.0
        )
        self.assertAlmostEqual(sum(probabilities), 1.0, places=12)
        distribution = transformer_student.quantize_distribution(probabilities)
        self.assertEqual(set(distribution), set(student.LABELS))
        self.assertEqual(
            sum(value["numerator"] for value in distribution.values()),
            1_000_000_000,
        )
        self.assertTrue(
            all(value["denominator"] == 1_000_000_000 for value in distribution.values())
        )
        with self.assertRaises(transformer_student.TransformerStudentError):
            transformer_student.normalized_probabilities([0, 1, 2, 3, 4], temperature=0)

        validation_rows = []
        validation_logits = []
        for index, label in enumerate(student.LABELS):
            validation_rows.append(
                {"id": f"validation-{index}", "split": "validation", "gold": label, "text": f"текст {index}"}
            )
            validation_logits.append([4.0 if column == index else -1.0 for column in range(5)])
        calibration = transformer_student.fit_temperature(
            validation_logits, validation_rows, grid_points=51
        )
        self.assertEqual(calibration["split"], "validation")
        self.assertFalse(calibration["used_test_split"])
        self.assertLessEqual(
            calibration["nll_after"], calibration["nll_before"] + 1e-12
        )
        with self.assertRaises(transformer_student.TransformerStudentError):
            transformer_student.fit_temperature(
                [[1.0, 0.0, 0.0, 0.0, 0.0]],
                [{"id": "test-1", "split": "test", "gold": "оплата", "text": "не калібрувати"}],
                grid_points=51,
            )

        seed_rows = [
            {"id": "train-1", "split": "train", "gold": "оплата", "text": "платіж"},
            {"id": "validation-1", "split": "validation", "gold": "доставка", "text": "посилка"},
            {"id": "test-1", "split": "test", "gold": "технічне", "text": "помилка"},
        ]
        sha = "fixed-corpus-sha"
        teacher_rows = [
            {
                **seed_rows[0],
                "dataset_sha256": sha,
                "teacher_distribution": exact_distribution("оплата"),
            }
        ]
        train_rows, targets = transformer_student.validate_rows(seed_rows, sha, teacher_rows)
        self.assertEqual([row["id"] for row in train_rows], ["train-1"])
        self.assertEqual(set(targets), {"train-1"})
        teacher_rows.append(
            {
                **seed_rows[1],
                "dataset_sha256": sha,
                "teacher_distribution": exact_distribution("доставка"),
            }
        )
        with self.assertRaises(transformer_student.TransformerStudentError):
            transformer_student.validate_rows(seed_rows, sha, teacher_rows)

    def test_evaluator_refuses_wrong_split_and_incomplete_distribution(self):
        row = {
            "id": "test-1",
            "split": "train",
            "text": "перевірка",
            "gold": "оплата",
            "distribution": exact_distribution("оплата"),
        }
        with self.assertRaises(evaluator.EvaluationError):
            evaluator.score([row], threshold=0.8, bins=10, expected_split="test")
        row["split"] = "test"
        row["distribution"].pop("доставка")
        with self.assertRaises(evaluator.EvaluationError):
            evaluator.score([row], threshold=0.8, bins=10, expected_split="test")


if __name__ == "__main__":
    unittest.main()
