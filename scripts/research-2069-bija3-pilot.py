#!/usr/bin/env python3
"""#2069: exact 3-bit bīja3 identity/evidence pilot.

Research only. No production parser/runtime/contract changes.

The witness tests the first owner-directed paradigm slice:
- exact width is part of identity;
- the eight 3-bit seed words are admitted and unique;
- zero-padded 8-bit legacy forms are projections, not equal identities;
- D4+ descendants are not admitted by this pilot;
- semantic seed roles are explicit evidence, not inferred from bit geometry.
"""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class BoundedWord:
    bits: str

    def __post_init__(self) -> None:
        if not self.bits or any(ch not in '01' for ch in self.bits):
            raise ValueError(f'invalid binary word: {self.bits!r}')

    @property
    def width(self) -> int:
        return len(self.bits)

    @property
    def identity(self) -> tuple[int, str]:
        return (self.width, self.bits)


SEEDS = (
    ('000', '00000000', 'ground', 'historical empty-list ground'),
    ('001', '00000001', 'syntax', 'QUOTE seed role'),
    ('010', '00000010', 'predicate', 'ATOM seed role'),
    ('011', '00000011', 'predicate', 'EQ seed role'),
    ('100', '00000100', 'constructor', 'CONS seed role'),
    ('101', '00000101', 'selector', 'CAR seed role'),
    ('110', '00000110', 'selector', 'CDR seed role'),
    ('111', '00000111', 'control', 'COND seed role'),
)

EVIDENCE = (
    'contracts/core1-historical-sid-map.lisp',
    'knowledge/semantic-ownership.lisp',
)


def admit_d3(text: str) -> BoundedWord:
    word = BoundedWord(text)
    if word.width != 3:
        raise ValueError(f'D3 requires exact width=3, got width={word.width}: {text}')
    return word


def run() -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    rows: list[dict[str, str]] = []
    identities: set[tuple[int, str]] = set()

    assert len(SEEDS) == 8
    for bits, legacy, role, note in SEEDS:
        seed = admit_d3(bits)
        legacy_word = BoundedWord(legacy)

        assert seed.identity not in identities
        identities.add(seed.identity)
        assert legacy_word.width == 8
        assert legacy_word.bits.endswith(seed.bits)
        assert legacy_word.identity != seed.identity

        rows.append(
            {
                'word': bits,
                'width': str(seed.width),
                'epistemic_status': 'ground' if bits == '000' else 'primitive-seed',
                'semantic_role_class': role,
                'legacy_projection': legacy,
                'identity_equals_legacy': '0',
                'descendant_admitted': '0',
                'evidence': ';'.join(EVIDENCE),
                'note': note,
            }
        )

    assert len(identities) == 8

    negative_cases = []
    for label, candidate in (
        ('too-short', '10'),
        ('d4-not-admitted', '1010'),
        ('legacy-padding-not-d3', '00000101'),
        ('malformed', '10x'),
    ):
        try:
            admit_d3(candidate)
        except ValueError as exc:
            negative_cases.append(
                {
                    'case': label,
                    'candidate': candidate,
                    'result': 'reject',
                    'reason': str(exc),
                }
            )
        else:
            raise AssertionError(f'negative case unexpectedly admitted: {label} {candidate}')

    return rows, negative_cases


def write_tsv(path: Path, rows: list[dict[str, str]], negative: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8', newline='') as f:
        fields = (
            'kind', 'word', 'width', 'epistemic_status', 'semantic_role_class',
            'legacy_projection', 'identity_equals_legacy', 'descendant_admitted',
            'evidence', 'note'
        )
        writer = csv.DictWriter(f, fieldnames=fields, delimiter='\t', lineterminator='\n')
        writer.writeheader()
        for row in rows:
            writer.writerow({'kind': 'seed', **row})
        for case in negative:
            writer.writerow(
                {
                    'kind': 'negative',
                    'word': case['candidate'],
                    'width': str(len(case['candidate'])),
                    'epistemic_status': 'rejected',
                    'semantic_role_class': 'none',
                    'legacy_projection': 'n/a',
                    'identity_equals_legacy': 'n/a',
                    'descendant_admitted': '0',
                    'evidence': 'pilot admission law',
                    'note': f"{case['case']}: {case['reason']}",
                }
            )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default='docs/research/2069-bija3-pilot.tsv')
    args = ap.parse_args()

    rows, negative = run()
    write_tsv(Path(args.out), rows, negative)

    print('bija3_exact_identities=8')
    print('canonical_width=3')
    print('legacy_width=8 projection_only')
    print(f'negative_cases_rejected={len(negative)}')
    print('d4_descendants_admitted=0')
    print('PASS')


if __name__ == '__main__':
    main()
