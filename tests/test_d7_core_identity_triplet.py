"""Історичний D7 v2 приклад: єдиний фізичний носій, без видавання T5 за T5M-оракул."""
from __future__ import annotations
import json
from pathlib import Path
import re
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from sens_t5_t5m_codec import encode_words, decode_bytes  # noqa: E402

OUT = ROOT / "examples" / "migrated" / "d7-core-identity"

def frame(parts: list[list[str]]) -> list[str]:
    words = ["10"]
    for n, part in enumerate(parts):
        if n:
            words.append("00")
        words.extend(part)
    words.append("01")
    return words

class D7CoreIdentityTriplet(unittest.TestCase):
    def test_one_historical_carrier_contain_exact_d7_code(self):
        # Чинна укр-реальність: джерело — ратифікована укр-голова визначити
        # з D7-кодованим іменем, а не історична двійкова форма
        # (0011 identity (0010 (value) value)). Канонічна тотожність
        # тотожність/значення живе в lib/core.lisp окремо.
        # Параметр звуть передане-значення, а не значення: «значення» —
        # першокласна назва D8 (ук значення = en values, 00110100), тож
        # локальне зв'язування з ним затіняло ратифіковану функцію.
        source = (OUT / "source.lisp").read_text(encoding="utf-8")
        self.assertTrue(source.startswith("(визначити "), source)
        self.assertIn("(визначити тотожність (функція (передане-значення) передане-значення))",
                      (ROOT / "lib/core.lisp").read_text(encoding="utf-8"))
        d7 = json.loads((ROOT / "knowledge/d7-keyboard-v2-ratified.json").read_text(encoding="utf-8"))
        self.assertEqual((d7["schema"], d7["width"], d7["occupancy"]),
                         ("sens.d7.keyboard/v2", 7, 128))
        def binder(name: str) -> list[str]:
            letters = []
            for ch in name:
                n = ord(ch)
                self.assertEqual(d7["table"][n]["ascii"], ch)
                self.assertEqual(d7["table"][n]["bits"], format(n, "07b"))
                letters.append([format(n, "07b")])
            return frame(letters)
        value = binder("value")
        expected = frame([["0011"], binder("identity"), frame([
            ["0010"], frame([value]), value,
        ])])
        visible = (OUT / "identity.bits").read_text(encoding="ascii").split()
        self.assertEqual(visible, expected)
        self.assertEqual(len(visible), 51)
        self.assertEqual(sum(map(len, visible)), 196)
        self.assertTrue(all(re.fullmatch(r"[01]{1,9}", item) for item in visible))
        expected_bytes = encode_words(visible)
        self.assertEqual(len(expected_bytes), 50)
        self.assertEqual(decode_bytes(expected_bytes), visible)
        # Три англійсько/санскритсько/українські копії були
        # побайтово ідентичні source.sens; це не три окремі SENS-механізми.
        raw = (OUT / "source.sens").read_bytes()
        self.assertEqual(raw, expected_bytes)
        self.assertEqual(decode_bytes(raw), expected)
        self.assertEqual((OUT / "source").read_text(encoding="ascii").split(), expected)
        for language in ("uk", "en", "san"):
            self.assertFalse((OUT / f"identity.{language}.sens").exists())

if __name__ == "__main__":
    unittest.main()
