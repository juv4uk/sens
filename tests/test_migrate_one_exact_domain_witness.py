#!/usr/bin/env python3
"""2046 typed coordinates / 256 historical cells / physical T5 is not semantic admission."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from sens_t5_t5m_codec import SensT5Error, decode_bytes, encode_words, typed_sha256

spec = importlib.util.spec_from_file_location(
    "one_file_t5_witness", ROOT / "scripts/migrate-one-to-sens.py")
if spec is None or spec.loader is None:
    raise RuntimeError("missing one-file migrator")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class ExactDomainWitness(unittest.TestCase):
    def test_all_2046_domain_codes_and_t5_boundary(self):
        admissible, seen = [], set()
        for width in range(1, 11):
            text = (ROOT / "lib/domains" / f"d{width}.lisp").read_text(encoding="utf-8")
            rows = re.findall(r"(?m)^  \(([01]{1,10}) \(ук ", text)
            self.assertEqual(rows, [f"{i:0{width}b}" for i in range(1 << width)])
            for bits in rows:
                self.assertNotIn((width, bits), seen)
                seen.add((width, bits))
                if width < 10:
                    admissible.append(bits)
                else:
                    self.assertEqual(decode_bytes(encode_words([bits])), [bits])
        self.assertEqual(len(seen), 2046)
        self.assertEqual(len(admissible), 1022)
        owner = json.loads((ROOT / "knowledge/d10-owner-whole-domain-ratification-20261012.json").read_text(encoding="utf-8"))
        self.assertIs(owner["ratified"], True)
        self.assertIs(owner["evidence_separation"]["physical_runtime_t5_opcode_admission"], False)
        packed = encode_words(admissible)
        self.assertEqual(sum(map(len, admissible)), 8194)
        self.assertEqual(len(packed), 1843)
        self.assertEqual(decode_bytes(packed), admissible)
        self.assertNotEqual(typed_sha256(["0", "00"]), typed_sha256(["000"]))

    def test_256_legacy_codes_have_separate_dispositions(self):
        rows = json.loads((ROOT / "knowledge/sens8-current-coverage-v1.json").read_text(encoding="utf-8"))["rows"]
        self.assertEqual({r["legacy_code"] for r in rows}, {f"{i:08b}" for i in range(256)})
        self.assertEqual(len(rows), 256)
        allowed = {"DIRECT-CURRENT-IDENTITY", "CURRENT-PROJECTION-DERIVED"}
        self.assertEqual(sum(r["classification"] in allowed for r in rows), 173)
        self.assertEqual(sum(r["classification"] == "D10-RECOVERY-CANDIDATE" for r in rows), 4)

    def test_corrupt_upstream_evidence_is_not_publishable(self):
        words = ["10", "0011", "00", "111", "01"]
        payload = encode_words(words)
        row = {
            "path": "demo.lisp", "output": "demo.sens", "status": "written",
            "bytes": len(payload), "semantic_word_count": len(words),
            "semantic_bits": sum(map(len, words)),
            "transport_trits": sum(map(len, words)) + len(words)-1,
            "physical_sha256": hashlib.sha256(payload).hexdigest(),
            "typed_word_sha256": typed_sha256(words),
            "passes": {"pass2-my-lisp": 1}, "semantic_admitted": False,
            "zig_transport": {"physical_sha256": hashlib.sha256(payload).hexdigest(),
                              "source_pin_status": "MATCHED_CALLER_SUPPLIED_SHA256",
                              "zig_binary_sha256": "a" * 64},
        }
        report = {"schema": "sens-three-pass-t5-migration/v3",
                  "mode": "write-new-only-zig-minted",
                  "physical_producer": "PINNED_ZIG_T5_CARRY",
                  "file_format": {"physical": "binary-T5-five-trits-per-byte",
                                  "source_surface": "default"},
                  "summary": {"files_seen": 1, "files_written": 1, "files_blocked": 0},
                  "files": [row]}
        codec = mod.load_codec()
        witness = mod.verify_upstream_t5_witness(report, "demo.lisp", words, payload, "t5", codec)
        self.assertEqual(witness["semantic_bits"], 13)
        for field, wrong in (
            ("bytes", len(payload)+1), ("semantic_word_count", len(words)+1),
            ("semantic_bits", 14), ("transport_trits", 18),
            ("physical_sha256", "0"*64), ("typed_word_sha256", "0"*64),
            ("status", "would-write"), ("path", "wrong.lisp"),
            ("output", "wrong.sens"), ("passes", None),
        ):
            with self.subTest(field=field):
                tampered = copy.deepcopy(report)
                tampered["files"][0][field] = wrong
                with self.assertRaisesRegex(ValueError, "THREE_PASS_WITNESS"):
                    mod.verify_upstream_t5_witness(tampered, "demo.lisp", words, payload, "t5", codec)
        for field, wrong in (("schema", "v2"), ("physical_producer", "PYTHON_REFERENCE_ONLY"), ("mode", "dry-run")):
            altered = copy.deepcopy(report)
            altered[field] = wrong
            with self.assertRaises(ValueError):
                mod.verify_upstream_t5_witness(altered, "demo.lisp", words, payload, "t5", codec)
        for field, wrong in (("files_seen", 2), ("files_written", 0), ("files_blocked", 1)):
            altered = copy.deepcopy(report)
            altered["summary"][field] = wrong
            with self.assertRaises(ValueError):
                mod.verify_upstream_t5_witness(altered, "demo.lisp", words, payload, "t5", codec)


if __name__ == "__main__":
    unittest.main()
