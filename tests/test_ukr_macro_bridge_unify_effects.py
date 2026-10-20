"""Статичні regressions для exact-width українських Lisp-проєкцій (не Python-SENS evaluator)."""
from __future__ import annotations
import hashlib
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PINNED = {
  "lib/unify-observe.lisp": {
    "sha": "ae97885c67a24ab457966b4093331021abb084be",
    "changed": 4,
    "edits": [
      [
        709,
        "0011"
      ],
      [
        747,
        "0010"
      ],
      [
        1077,
        "0011"
      ],
      [
        1099,
        "0010"
      ]
    ]
  },
  "lib/bridge/prolog-to-datalog.lisp": {
    "sha": "501173f6423c20ed8b089e81979ab6f1346dcdb5",
    "changed": 38,
    "edits": [
      [
        591,
        "0011"
      ],
      [
        630,
        "0010"
      ],
      [
        654,
        "110"
      ],
      [
        673,
        "0100"
      ],
      [
        679,
        "010"
      ],
      [
        700,
        "111"
      ],
      [
        705,
        "1110"
      ],
      [
        716,
        "100"
      ],
      [
        816,
        "0011"
      ],
      [
        862,
        "0010"
      ],
      [
        887,
        "0010"
      ],
      [
        940,
        "110"
      ],
      [
        954,
        "0100"
      ],
      [
        960,
        "010"
      ],
      [
        991,
        "1110"
      ],
      [
        997,
        "001"
      ],
      [
        1022,
        "001"
      ],
      [
        1058,
        "010"
      ],
      [
        1089,
        "1110"
      ],
      [
        1095,
        "001"
      ],
      [
        1120,
        "001"
      ],
      [
        1158,
        "0100"
      ],
      [
        1164,
        "010"
      ],
      [
        1195,
        "110"
      ],
      [
        1212,
        "0100"
      ],
      [
        1218,
        "010"
      ],
      [
        1250,
        "1110"
      ],
      [
        1256,
        "001"
      ],
      [
        1281,
        "001"
      ],
      [
        1323,
        "010"
      ],
      [
        1355,
        "1110"
      ],
      [
        1361,
        "001"
      ],
      [
        1386,
        "001"
      ],
      [
        1430,
        "0100"
      ],
      [
        1436,
        "010"
      ],
      [
        1468,
        "110"
      ],
      [
        1488,
        "0100"
      ],
      [
        1494,
        "010"
      ],
      [
        1527,
        "1110"
      ],
      [
        1533,
        "001"
      ],
      [
        1558,
        "001"
      ],
      [
        1596,
        "010"
      ],
      [
        1629,
        "1110"
      ],
      [
        1635,
        "001"
      ],
      [
        1660,
        "001"
      ],
      [
        1700,
        "0100"
      ],
      [
        1706,
        "010"
      ],
      [
        1739,
        "1110"
      ],
      [
        1762,
        "001"
      ],
      [
        1803,
        "1110"
      ],
      [
        1809,
        "001"
      ],
      [
        1849,
        "001"
      ],
      [
        1911,
        "1110"
      ],
      [
        1917,
        "001"
      ],
      [
        1957,
        "100"
      ],
      [
        1962,
        "011"
      ],
      [
        2002,
        "1110"
      ],
      [
        2008,
        "001"
      ],
      [
        2114,
        "100"
      ],
      [
        2119,
        "011"
      ],
      [
        2164,
        "011"
      ]
    ]
  },
  "lib/machine/lowering/semantic-effects.lisp": {
    "sha": "a1ecf30cd1860558874bdc8489fa333ab6df35b0",
    "changed": 10,
    "edits": [
      [
        494,
        "0011"
      ],
      [
        537,
        "0010"
      ],
      [
        589,
        "110"
      ],
      [
        677,
        "#d1:1"
      ],
      [
        690,
        "#d1:0"
      ],
      [
        874,
        "0011"
      ],
      [
        918,
        "0010"
      ],
      [
        952,
        "110"
      ],
      [
        1299,
        "#d1:1"
      ],
      [
        1313,
        "001"
      ]
    ]
  }
}
ROW = re.compile(r'^\s*\(([01]+)\s+\(ук\s+[^()]*\)\s+\(укр\s+([^\s()]+)\)')
HEAD = re.compile(r'\(\s*[01]+(?=\s|\)|$)')
LITERAL = re.compile(r'#(?:d\d+:[01]+|b[01]+)')

def peers():
    result = {}
    for width in (1, 3, 4):
        lines = (ROOT / 'lib' / 'domains' / f'd{width}.lisp').read_text(encoding='utf-8').splitlines()
        for line in lines:
            match = ROW.match(line)
            if match and len(match[1]) == width:
                assert match[1] not in result
                result[match[1]] = match[2]
    assert len(result) == 25  # D3:000 denotes structural (), not a callable head
    return result

def invert(text, edits, authority):
    coordinates, delta, last = [], 0, -1
    for original_offset, old in edits:
        assert original_offset > last, 'Дубль координати/невпорядковані edits'
        last = original_offset
        bits = old.split(':')[-1] if old.startswith('#d1:') else old
        assert bits in authority and len(bits) in (1, 3, 4)
        new = authority[bits]
        coordinates.append((original_offset + delta, old, new))
        delta += len(new) - len(old)
    for offset, old, new in reversed(coordinates):
        assert text[offset:offset + len(new)] == new, f'Порушено точну проєкцію {old} на {offset}'
        text = text[:offset] + old + text[offset + len(new):]
    return text

BRIDGE_HEAD_PROJECTIONS = (
    (
      "(знайти-за-ключем (як-є source-ref) (решта observation))",
      "(11100 (001 source-ref) (011 observation))",
    ),
    (
      "(знайти-за-ключем (як-є variable) (решта observation))",
      "(11100 (001 variable) (011 observation))",
    ),
    (
      "(знайти-за-ключем (як-є values) (решта observation))",
      "(11100 (001 values) (011 observation))",
    ),
)

def restore_bridge_source_layer(text):
    for projected, encoded in BRIDGE_HEAD_PROJECTIONS:
        assert text.count(projected) == 1, f'Очікувалася рівно одна проєкція {projected}'
        text = text.replace(projected, encoded, 1)
    return text

def restore_source(path, text, witness, authority):
    if path == 'lib/bridge/prolog-to-datalog.lisp':
        text = restore_bridge_source_layer(text)
    return invert(text, witness['edits'], authority)

def blob_sha(text):
    raw = text.encode('utf-8')
    return hashlib.sha1(b'blob ' + str(len(raw)).encode('ascii') + b'\0' + raw).hexdigest()

def mask_comment_and_strings(line):
    return re.sub(r'"(?:\\.|[^"\\])*"|;[^\n]*', lambda m: ' ' * len(m.group()), line)

class ExactDomainMigrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.authority = peers()

    def test_inverse_recovers_original_git_blobs_exactly(self):
        for path, witness in PINNED.items():
            with self.subTest(path=path):
                src = (ROOT / path).read_text(encoding='utf-8')
                restored = restore_source(path, src, witness, self.authority)
                self.assertEqual(blob_sha(restored), witness['sha'])

    def test_no_new_encoded_literals_on_changed_lines(self):
        for path, witness in PINNED.items():
            with self.subTest(path=path):
                src = (ROOT / path).read_text(encoding='utf-8')
                old = restore_source(path, src, witness, self.authority)
                previous, current = old.splitlines(), src.splitlines()
                self.assertEqual(len(previous), len(current))
                changed = [i + 1 for i, (x, y) in enumerate(zip(previous, current)) if x != y]
                self.assertEqual(len(changed), witness['changed'])
                for index in changed:
                    line = mask_comment_and_strings(current[index - 1])
                    self.assertNotRegex(line, HEAD, f'{path}:{index}')
                    self.assertNotRegex(line, LITERAL, f'{path}:{index}')

    def test_macro_quote_uses_ratified_ukrainian_d4_names(self):
        # Старий blob залишається у Git. Чинний макрос цитує людську
        # проєкцію функції/визначення без машинних літералів.
        src = (ROOT / 'lib/macro.lisp').read_text(encoding='utf-8')
        d4 = (ROOT / 'lib/domains/d4.lisp').read_text(encoding='utf-8')
        self.assertIn('(0010 (ук функція) (укр функція)', d4)
        self.assertIn('(0011 (ук визначити) (укр визначити)', d4)
        for form in ('(як-є функція)', '(як-є визначити)'):
            with self.subTest(form=form):
                self.assertIn(form, src)
        self.assertNotIn('(як-є 0010)', src)
        self.assertNotIn('(як-є 0011)', src)
        self.assertIn('(функція сирі-форми', src)
        self.assertIn('((атом? (решта (решта сирі-форми)))', src)
        self.assertIn('(як-є визначити)', src)
        self.assertIn('(як-є функція)', src)
        self.assertIn('(як-є макрос)', src)
        self.assertIn('(перше сирі-форми)', src)
        self.assertIn('(решта сирі-форми)', src)
        self.assertNotIn('побудувати-макровизначення', src)

    def test_public_names_and_unknown_d5_preserved(self):
        checks = {
            'lib/unify-observe.lisp': ('unify-observe', 'уніфікація-спостереження-стан'),
            'lib/machine/lowering/semantic-effects.lisp': (
                'machine-effect-current-domain-key?', 'machine-lower-current-binary-effect'),
        }
        for path, names in checks.items():
            src = (ROOT / path).read_text(encoding='utf-8')
            for name in names:
                with self.subTest(path=path, name=name):
                    self.assertIn('(визначити ' + name, src)
        bridge = (ROOT / 'lib/bridge/prolog-to-datalog.lisp').read_text(encoding='utf-8')
        for name in ('перетворити-значення-пролог-на-факти-даталог',
                     'перетворити-підстановки-пролог-на-факти-даталог'):
            with self.subTest(name=name):
                self.assertIn('(визначити ' + name, bridge)
        for legacy_name in ('prolog-values-to-datalog-facts',
                            'prolog-substitutions-to-datalog-facts'):
            with self.subTest(legacy_name=legacy_name):
                self.assertNotIn('(визначити ' + legacy_name, bridge)
        for field in ('source-ref', 'variable', 'values'):
            with self.subTest(field=field):
                projected = f'(знайти-за-ключем (як-є {field}) (решта спостереження))'
                encoded = f'(11100 (001 {field}) (011 спостереження))'
                self.assertIn(projected, bridge)
                self.assertNotIn(encoded, bridge)

    def test_incorrect_projection_is_not_accepted(self):
        path = 'lib/unify-observe.lisp'
        src = (ROOT / path).read_text(encoding='utf-8')
        mutated = src.replace('(визначити unify-observe', '(визначити-неправильно unify-observe', 1)
        self.assertNotEqual(src, mutated)
        with self.assertRaises(AssertionError):
            invert(mutated, PINNED[path]['edits'], self.authority)

if __name__ == '__main__':
    unittest.main(verbosity=2)
