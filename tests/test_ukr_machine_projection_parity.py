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
  "lib/machine/dispatch/native-first-parity.lisp": {
    "sha": "09a8f664971398b55698726f522f10d383e46be2",
    "top_forms": 6,
    "changed_lines": [
      8,
      9,
      10,
      11,
      13,
      14,
      15,
      17,
      18,
      19,
      20,
      22,
      23,
      24,
      25,
      27,
      28,
      29,
      30,
      31,
      32,
      34,
      38,
      39,
      40,
      41,
      42,
      43,
      44,
      46,
      47,
      53,
      56,
      59,
      62,
      66,
      67,
      68,
      70,
      71,
      73,
      74,
      75,
      77,
      78,
      79,
      80,
      82,
      83,
      84,
      85,
      86,
      87,
      91,
      93,
      95,
      96,
      97,
      98,
      99,
      100,
      101,
      102,
      104
    ],
    "edits": [
      [
        348,
        "0011"
      ],
      [
        381,
        "0010"
      ],
      [
        423,
        "1110"
      ],
      [
        435,
        "001"
      ],
      [
        477,
        "001"
      ],
      [
        494,
        "1110"
      ],
      [
        500,
        "001"
      ],
      [
        533,
        "1110"
      ],
      [
        539,
        "001"
      ],
      [
        568,
        "0011"
      ],
      [
        601,
        "0010"
      ],
      [
        639,
        "1110"
      ],
      [
        651,
        "001"
      ],
      [
        693,
        "001"
      ],
      [
        710,
        "1110"
      ],
      [
        716,
        "001"
      ],
      [
        739,
        "1110"
      ],
      [
        745,
        "001"
      ],
      [
        776,
        "1110"
      ],
      [
        782,
        "001"
      ],
      [
        807,
        "0011"
      ],
      [
        840,
        "0010"
      ],
      [
        856,
        "001001"
      ],
      [
        871,
        "100"
      ],
      [
        905,
        "1001"
      ],
      [
        938,
        "10011"
      ],
      [
        976,
        "100111"
      ],
      [
        1059,
        "0001"
      ],
      [
        1213,
        "1110"
      ],
      [
        1234,
        "001"
      ],
      [
        1271,
        "001"
      ],
      [
        1299,
        "001"
      ],
      [
        1339,
        "1110"
      ],
      [
        1345,
        "001"
      ],
      [
        1376,
        "110"
      ],
      [
        1390,
        "11110111"
      ],
      [
        1445,
        "110"
      ],
      [
        1462,
        "11110111"
      ],
      [
        1648,
        "#d1:1"
      ],
      [
        1726,
        "001"
      ],
      [
        1836,
        "#d1:1"
      ],
      [
        1905,
        "001"
      ],
      [
        1993,
        "0011"
      ],
      [
        2025,
        "0010"
      ],
      [
        2042,
        "110"
      ],
      [
        2061,
        "010"
      ],
      [
        2080,
        "1110"
      ],
      [
        2132,
        "001"
      ],
      [
        2166,
        "001"
      ],
      [
        2198,
        "001"
      ],
      [
        2233,
        "0100"
      ],
      [
        2239,
        "010"
      ],
      [
        2258,
        "111"
      ],
      [
        2298,
        "100"
      ],
      [
        2344,
        "011"
      ],
      [
        2362,
        "0011"
      ],
      [
        2404,
        "0010"
      ],
      [
        2424,
        "110"
      ],
      [
        2436,
        "0100"
      ],
      [
        2442,
        "010"
      ],
      [
        2464,
        "110"
      ],
      [
        2479,
        "11110111"
      ],
      [
        2489,
        "10011"
      ],
      [
        2505,
        "001"
      ],
      [
        2560,
        "001"
      ],
      [
        2618,
        "001"
      ],
      [
        2632,
        "0011"
      ],
      [
        2670,
        "0010"
      ],
      [
        2691,
        "110"
      ],
      [
        2703,
        "0100"
      ],
      [
        2709,
        "010"
      ],
      [
        2735,
        "010"
      ],
      [
        2751,
        "001"
      ],
      [
        2768,
        "0100"
      ],
      [
        2774,
        "010"
      ],
      [
        2797,
        "110"
      ],
      [
        2812,
        "11110111"
      ],
      [
        2857,
        "100"
      ],
      [
        2928,
        "011"
      ]
    ]
  }
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


def undo_current_native_first_parity_selector(path: str, text: str) -> str:
    """Undo the later, source-only D3 composition before frozen historical inverse.

    The original Git manifest still verifies its exact bytes. This is an
    additional, explicit step, not an edited legacy expectation or a parser
    exception. D9:110110101 FIFTH cannot be spelled with the ASCII-apostrophe
    Ukrainian surface in the current reader; current executable form uses
    D3 CAR after four D3 CDRs on a five-field parity record.
    """
    if path != "lib/machine/dispatch/native-first-parity.lisp":
        return text
    current = "(error-class (перше (решта (решта (решта (решта row))))))"
    previous = "(error-class (110110101 row))"
    if text.count(current) != 1 or previous in text or "(п'ятий row)" in text:
        raise AssertionError("Поточний native-first D3-селектор змінився")
    return text.replace(current, previous, 1)


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
                    undo_current_native_first_parity_selector(path, current),
                    evidence['edits'], self.authority)
                self.assertEqual(git_blob_sha(restored), evidence['sha'])

    def test_new_source_lines_have_no_old_encoded_callable_heads(self):
        for path, evidence in MANIFEST.items():
            with self.subTest(source=path):
                now = (ROOT / path).read_text(encoding='utf-8')
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
        self.assertRegex(core4, r'\((?:0011|визначити)\s+однакові\?\s+equal\?\)')
        parity = (ROOT / 'lib/machine/dispatch/native-first-parity.lisp').read_text(encoding='utf-8')
        self.assertIn('(однакові? evaluator-value expected)', parity)

    def test_later_native_parity_selector_inverse_rejects_wrong_peer(self):
        path = 'lib/machine/dispatch/native-first-parity.lisp'
        source = (ROOT / path).read_text(encoding='utf-8')
        restored = undo_current_native_first_parity_selector(path, source)
        self.assertIn('(error-class (110110101 row))', restored)
        mutant = source.replace(
            '(error-class (перше (решта (решта (решта (решта row))))))',
            '(error-class (перше (решта (решта (решта row)))))', 1,
        )
        self.assertNotEqual(mutant, source)
        with self.assertRaisesRegex(AssertionError, 'селектор'):
            undo_current_native_first_parity_selector(path, mutant)

    def test_projections_do_not_change_host_call_names(self):
        proj = (ROOT / 'lib/machine/projection/x86-64.lisp').read_text(encoding='utf-8')
        parity = (ROOT / 'lib/machine/dispatch/native-first-parity.lisp').read_text(encoding='utf-8')
        self.assertIn('(визначити x86-project-machine-effect', proj)
        self.assertIn('(визначити x86-encode-machine-effect', proj)
        self.assertIn('(визначити native-first-parity-run', parity)
        self.assertIn('(визначити native-first-parity-all-pass?', parity)
        self.assertIn('(нехай ', proj)
        self.assertIn('(нехай-послідовно ', parity)

    def test_negative_wrong_peer_cannot_pass_inverse(self):
        path = 'lib/machine/projection/x86-64.lisp'
        text = (ROOT / path).read_text(encoding='utf-8')
        mutated = text.replace('(визначити x86-project-machine-effect',
                               '(визначити-невірно x86-project-machine-effect', 1)
        self.assertNotEqual(mutated, text)
        with self.assertRaises(AssertionError):
            invert_projection(mutated, MANIFEST[path]['edits'], self.authority)


if __name__ == '__main__':
    unittest.main(verbosity=2)
