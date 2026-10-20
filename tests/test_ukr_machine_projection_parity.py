"""Точний український source-carrying D1/D3–D6/D8 witness.

Не виконує Lisp через Python. Інверсія має побайтово повертати
попередні Git blobs; D8 EQUAL — окрема structural identity, не D3 EQ.
"""
from __future__ import annotations

import hashlib
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = {
  "lib/machine/projection/x86-64.lisp": {
    "sha": "19b42112712001f316e9a332cecb80ac1a66e033",
    "top_forms": 2,
    "changed_lines": [
      7,
      8,
      9,
      11,
      12,
      13,
      14,
      15,
      16,
      17,
      18,
      20,
      21,
      22,
      23,
      24,
      25,
      26,
      27,
      29,
      30,
      31,
      32,
      33,
      34,
      35,
      36,
      37,
      39,
      40,
      41,
      42,
      43,
      44,
      45
    ],
    "edits": [
      [
        269,
        "0011"
      ],
      [
        304,
        "0010"
      ],
      [
        323,
        "110"
      ],
      [
        388,
        "001000"
      ],
      [
        412,
        "100"
      ],
      [
        417,
        "011"
      ],
      [
        449,
        "100"
      ],
      [
        454,
        "011"
      ],
      [
        459,
        "011"
      ],
      [
        485,
        "1110"
      ],
      [
        502,
        "1110"
      ],
      [
        508,
        "001"
      ],
      [
        528,
        "001"
      ],
      [
        555,
        "1110"
      ],
      [
        561,
        "001"
      ],
      [
        581,
        "001"
      ],
      [
        609,
        "1110"
      ],
      [
        615,
        "001"
      ],
      [
        633,
        "001"
      ],
      [
        643,
        "001"
      ],
      [
        665,
        "1110"
      ],
      [
        671,
        "001"
      ],
      [
        745,
        "001000"
      ],
      [
        769,
        "100"
      ],
      [
        774,
        "011"
      ],
      [
        806,
        "100"
      ],
      [
        811,
        "011"
      ],
      [
        816,
        "011"
      ],
      [
        842,
        "1110"
      ],
      [
        859,
        "1110"
      ],
      [
        865,
        "001"
      ],
      [
        885,
        "001"
      ],
      [
        912,
        "1110"
      ],
      [
        918,
        "001"
      ],
      [
        938,
        "001"
      ],
      [
        966,
        "1110"
      ],
      [
        972,
        "001"
      ],
      [
        990,
        "001"
      ],
      [
        1000,
        "001"
      ],
      [
        1022,
        "1110"
      ],
      [
        1028,
        "001"
      ],
      [
        1102,
        "001000"
      ],
      [
        1126,
        "100"
      ],
      [
        1131,
        "011"
      ],
      [
        1163,
        "100"
      ],
      [
        1168,
        "011"
      ],
      [
        1173,
        "011"
      ],
      [
        1199,
        "1110"
      ],
      [
        1216,
        "1110"
      ],
      [
        1222,
        "001"
      ],
      [
        1242,
        "001"
      ],
      [
        1269,
        "1110"
      ],
      [
        1275,
        "001"
      ],
      [
        1295,
        "001"
      ],
      [
        1323,
        "1110"
      ],
      [
        1329,
        "001"
      ],
      [
        1348,
        "001"
      ],
      [
        1358,
        "001"
      ],
      [
        1380,
        "1110"
      ],
      [
        1386,
        "001"
      ],
      [
        1407,
        "010"
      ],
      [
        1416,
        "001"
      ],
      [
        1451,
        "0011"
      ],
      [
        1485,
        "0010"
      ],
      [
        1504,
        "001000"
      ],
      [
        1564,
        "110"
      ],
      [
        1578,
        "010"
      ],
      [
        1599,
        "001"
      ],
      [
        1639,
        "010"
      ]
    ]
  },
}
DOMAIN_ROW = re.compile(r'^\s*\(([01]+)\s+\(ук\s+[^()]*\)\s+\(укр\s+([^\s()]+)\)')
ENCODED = re.compile(r'#(?:d\d+:[01]+|b[01]+)')
NUMERIC_CALL = re.compile(r'\(\s*[01]+(?=\s|\)|$)')


def exact_authority() -> dict[tuple[int, str], str]:
    index = {}
    for d in (1, 3, 4, 5, 6, 8):
        source = (ROOT / 'lib' / 'domains' / f'd{d}.lisp').read_text(encoding='utf-8')
        for line in source.splitlines():
            m = DOMAIN_ROW.match(line)
            if m is not None and len(m[1]) == d:
                index[(d, m[1])] = m[2]
    return index


def git_blob_sha(text: str) -> str:
    payload = text.encode('utf-8')
    return hashlib.sha1(b'blob ' + str(len(payload)).encode() + b'\x00' + payload).hexdigest()


def undo_current_lexical_binders(path: str, source: str) -> str:
    """Строго відновити докомітні локальні імена до історичного inverse.

    Це лише α-перейменування. Жоден цитований payload чи виклична голова
    не змінюється; точний Git blob і число відповідностей перевіряються.
    """
    from tests.test_machine_projection_ukr_locals import SOURCE, rewrite_bound_atoms, historical_projection_source
    old_sha, forward = SOURCE[path]
    backward = {new: old for old, new in forward.items()}
    restored, count = rewrite_bound_atoms(historical_projection_source(source), backward)
    expected = {
        "lib/machine/projection/x86-64.lisp": 27,
    }[path]
    if count != expected or git_blob_sha(restored) != old_sha:
        raise AssertionError(f"Лексичний inverse змінив джерело: {path}")
    return restored


def invert_projection(text: str, edits: list, authority: dict) -> str:
    shifts = []
    delta = 0
    last_offset = -1
    for original_offset, encoded_word in edits:
        if original_offset <= last_offset:
            raise AssertionError('Непослідовні source offsets')
        last_offset = original_offset
        bits = encoded_word.split(':')[-1] if encoded_word.startswith('#d1:') else encoded_word
        domain_width = len(bits)
        if domain_width not in (1, 3, 4, 5, 6, 8):
            raise AssertionError('Нератифікована бітність')
        if domain_width == 8 and bits != '11110111':
            raise AssertionError('Не доведено D8 callability')
        peer = authority.get((domain_width, bits))
        if not peer:
            raise AssertionError('Відсутня ратифікована укр-проєкція')
        shifts.append((original_offset + delta, encoded_word, peer))
        delta += len(peer) - len(encoded_word)

    for offset, old, peer in reversed(shifts):
        if text[offset:offset + len(peer)] != peer:
            raise AssertionError(f'Змінена проєкція/позиція для {old} в {offset}')
        text = text[:offset] + old + text[offset + len(peer):]
    return text


def mask_comments_and_strings(line: str) -> str:
    return re.sub(r'"(?:\\.|[^"\\])*"|;[^\n]*',
                  lambda m: ' ' * len(m[0]), line)


class MachineUkrMigrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.authority = exact_authority()

    def test_exact_git_blob_inverse_preserves_every_original_byte(self):
        for path, evidence in MANIFEST.items():
            with self.subTest(source=path):
                current = (ROOT / path).read_text(encoding='utf-8')
                restored = invert_projection(
                    undo_current_native_first_parity_selector(
                        path, undo_current_lexical_binders(path, current)),
                    evidence['edits'], self.authority)
                self.assertEqual(git_blob_sha(restored), evidence['sha'])

    def test_new_source_lines_have_no_old_encoded_callable_heads(self):
        for path, evidence in MANIFEST.items():
            with self.subTest(source=path):
                now = undo_current_lexical_binders(
                    path, (ROOT / path).read_text(encoding='utf-8'))
                old = invert_projection(
                    undo_current_native_first_parity_selector(path, now),
                    evidence['edits'], self.authority)
                a, b = old.splitlines(), now.splitlines()
                self.assertEqual(len(a), len(b))
                changed = [n+1 for n, (x, y) in enumerate(zip(a, b)) if x != y]
                expected_lines = list(evidence['changed_lines'])
                if path == 'lib/machine/dispatch/native-first-parity.lisp':
                    # Exactly one later, D3-defined fifth-field selector on line 33.
                    self.assertNotIn(33, expected_lines)
                    expected_lines.append(33)
                    expected_lines.sort()
                self.assertEqual(changed, expected_lines)
                for n in changed:
                    line = mask_comments_and_strings(b[n-1])
                    self.assertIsNone(ENCODED.search(line), f'{path}:{n}')
                    self.assertIsNone(NUMERIC_CALL.search(line), f'{path}:{n}')

    def test_structural_equal_d8_identity_and_callable_alias_not_atom_eq(self):
        self.assertEqual(self.authority[(8, '11110111')], 'однакові?')
        self.assertEqual(self.authority[(3, '101')], 'тотожне?')
        self.assertNotEqual('однакові?', self.authority[(3, '101')])
        core4 = (ROOT / 'lib/core4.lisp').read_text(encoding='utf-8')
        # Після міграції D8:11110111 є первинним українським визначенням;
        # equal? збережено лише як посилання сумісності на те саме замикання.
        self.assertIn('(визначити однакові?\n  (функція', core4)
        self.assertIn('(визначити equal? однакові?)', core4)
        self.assertNotIn('(визначити однакові? equal?)', core4)
        parity = (ROOT / 'lib/machine/dispatch/native-first-parity.lisp').read_text(encoding='utf-8')
        self.assertIn('(однакові? результат-обчислювача очікуване)', parity)
        self.assertIn('(однакові? результат-машини очікуваний-результат-машини)', parity)
        self.assertNotIn('(визначити native-first-parity-', parity)

    def test_current_native_parity_selector_is_ukrainian_and_width_preserving(self):
        path = 'lib/machine/dispatch/native-first-parity.lisp'
        source = (ROOT / path).read_text(encoding='utf-8')
        self.assertIn('(визначити нативний-паритет-пятичленний?', source)
        self.assertIn('(перше (решта (решта (решта (решта рядок))))))', source)
        self.assertNotIn("(п'ятий рядок)", source)
        self.assertNotIn('(110110101 ', source)
        mutant = source.replace(
            '(перше (решта (решта (решта (решта рядок))))))',
            '(перше (решта (решта (решта рядок)))))', 1,
        )
        self.assertNotEqual(mutant, source)
        self.assertNotIn('(перше (решта (решта (решта (решта рядок))))))', mutant)

    def test_projection_has_only_current_ukrainian_calls(self):
        proj = (ROOT / 'lib/machine/projection/x86-64.lisp').read_text(encoding='utf-8')
        parity = (ROOT / 'lib/machine/dispatch/native-first-parity.lisp').read_text(encoding='utf-8')
        self.assertIn('(визначити проєктувати-машинний-ефект-на-х86', proj)
        self.assertIn('(визначити закодувати-машинний-ефект-на-х86', proj)
        self.assertNotIn('(визначити x86-project-machine-effect', proj)
        self.assertNotIn('(визначити x86-encode-machine-effect', proj)
        self.assertIn('(визначити нативний-паритет-перевірити-корпус', parity)
        self.assertIn('(визначити нативний-паритет-усі-вердикти-успішні?', parity)
        self.assertNotIn('(визначити native-first-parity-', parity)
        self.assertIn('(нехай ', proj)
        self.assertIn('(нехай-послідовно ', parity)

    def test_negative_wrong_peer_cannot_pass_inverse(self):
        path = 'lib/machine/projection/x86-64.lisp'
        source = (ROOT / path).read_text(encoding='utf-8')
        mutated = source.replace('(визначити проєктувати-машинний-ефект-на-х86',
                                 '(визначити-невірно проєктувати-машинний-ефект-на-х86', 1)
        self.assertNotEqual(mutated, source)
        from tests.test_machine_projection_ukr_locals import historical_projection_source
        with self.assertRaises(AssertionError):
            historical_projection_source(mutated)
            restored = undo_current_lexical_binders(path, mutated)
            invert_projection(restored, MANIFEST[path]['edits'], self.authority)


if __name__ == '__main__':
    unittest.main(verbosity=2)
