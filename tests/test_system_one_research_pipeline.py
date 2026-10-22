"""Точкова перевірка локального вчителя, компактного учня та оцінювання."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import tempfile
import unittest
from argparse import Namespace
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
