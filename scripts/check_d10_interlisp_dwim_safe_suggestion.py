#!/usr/bin/env python3
"""Research-only historical DWIM diagnostics; no SENS language/identity admission.

Safely suggest one candidate from an explicit set (surface, canonical identity).
OSA edit distance is OUR bounded formalization, not a claim of Interlisp parity.
"""
from __future__ import annotations
import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESEARCH = ROOT / 'knowledge/d10-interlisp-dwim-safe-suggestion-v1.json'
FOUNDATION = ROOT / 'knowledge/d1-d9-foundation.json'
INVENTORY = ROOT / 'knowledge/d10-v1-semantic-inventory.json'
SEMANTIC_NAME = 'UNIQUE-SURFACE-CORRECTION-SUGGESTION'


def osa_distance(a: str, b: str) -> int:
    """Full OSA edit distance, including one adjacent transposition.

    OSA deliberately does NOT mean full unrestricted Damerau-Levenshtein.
    """
    if not isinstance(a, str) or not isinstance(b, str):
        raise TypeError('surfaces must be strings')
    d = [[0] * (len(b) + 1) for _ in range(len(a) + 1)]
    for i in range(len(a) + 1):
        d[i][0] = i
    for j in range(len(b) + 1):
        d[0][j] = j
    for i in range(1, len(a) + 1):
        for j in range(1, len(b) + 1):
            subst_cost = int(a[i-1] != b[j-1])
            d[i][j] = min(d[i-1][j]+1, d[i][j-1]+1, d[i-1][j-1]+subst_cost)
            if i > 1 and j > 1 and a[i-1] == b[j-2] and a[i-2] == b[j-1]:
                d[i][j] = min(d[i][j], d[i-2][j-2]+1)
    return d[-1][-1]


def eligible_surface(value: str) -> bool:
    # SENS exact bit words and D2 source punctuation are *never* auto-corrected.
    # This is only a suggestion about nonempty *unquoted*, indivisible surface labels.
    if not isinstance(value, str) or not value or re.fullmatch(r'[01]+', value):
        return False
    if any(c.isspace() or c in '().\'"`;,\\/' or ord(c) < 32 for c in value):
        return False
    return True


def propose(surface: str, candidates: list[tuple[str, str]], *, limit: int = 1) -> dict:
    """Data-only lookup. Never modify input, candidate table, nor execute identity."""
    if type(limit) is not int or limit not in (0, 1, 2):
        raise ValueError('limit must be exact integer 0, 1, or 2')
    if not eligible_surface(surface):
        return {'status': 'BLOCKED-SURFACE', 'candidate': None, 'distance': None, 'alternatives': []}
    by_identity = {}
    for entry in candidates:
        if not (isinstance(entry, (list, tuple)) and len(entry) == 2):
            raise TypeError('candidate must be (surface, binary-identity) pair')
        name, identity = entry
        if not eligible_surface(name) or not isinstance(identity, str) or not re.fullmatch('[01]+', identity):
            raise ValueError('invalid candidate surface or binary identity')
        if identity in by_identity and by_identity[identity] != name:
            raise ValueError('a binary identity may not have conflicting canonical surfaces')
        by_identity[identity] = name
    scored = [(osa_distance(surface, name), name, identity) for identity, name in by_identity.items()]
    if not scored:
        return {'status': 'ABSENT', 'candidate': None, 'distance': None, 'alternatives': []}
    min_distance = min(r[0] for r in scored)
    if min_distance > limit:
        return {'status': 'ABSENT', 'candidate': None, 'distance': min_distance, 'alternatives': []}
    winners = sorted(((name, identity) for dist, name, identity in scored if dist == min_distance), key=lambda z: (z[0], z[1]))
    if len(winners) != 1:
        return {'status': 'AMBIGUOUS', 'candidate': None, 'distance': min_distance, 'alternatives': [list(w) for w in winners]}
    name, identity = winners[0]
    return {'status': 'EXACT' if min_distance == 0 else 'SUGGEST', 'candidate': [name, identity], 'distance': min_distance, 'alternatives': []}


def validate_dossier(data: dict, foundation: dict | None = None, inventory: dict | None = None) -> dict:
    if sys.flags.optimize:
        raise RuntimeError('Python optimization disables assert-based research gates')
    assert data['schema'] == 'sens-d10-interlisp-dwim-safe-suggestion/v1'
    assert data['status'] == 'RESEARCH-PENDING-NOT-SELECTED'
    assert data['candidate']['semantic_name'] == SEMANTIC_NAME
    assert data['candidate']['coordinate'] is None
    assert data['candidate']['ratified'] is False
    assert data['candidate']['selected'] is False
    assert data['candidate']['physical_t5_authorized'] is False
    assert data['candidate']['automatic_rewrite_authorized'] is False
    assert data['candidate']['automatic_execute_authorized'] is False
    assert data['candidate']['arity'] == 3
    assert len(data['candidate']['positive_witnesses']) >= 4
    assert len(data['candidate']['negative_falsifiers']) >= 4
    assert data['source_provenance'][0]['url'].startswith('https://interlisp.org/')
    assert data['source_provenance'][1]['url'].startswith('https://interlisp.org/')
    assert data['snapshot']['selected_at_claim'] >= 630
    assert data['snapshot']['ratified'] == 0
    assert data['hold']['semantic_derivability'] is True
    if foundation is not None and inventory is not None:
        lower = {str(name).upper() for v in foundation['domains'].values() for name in v['residents'].values()}
        selected = {str(row['semantic_name']).upper() for row in inventory['rows']}
        assert len(selected) == len(inventory['rows']) == inventory['accounting']['selected_semantic_candidates']
        assert inventory['accounting']['ratified_d10_residents'] == 0
        assert SEMANTIC_NAME not in lower
        assert SEMANTIC_NAME not in selected
    return {'research': 1, 'selected': 0, 'ratified': 0, 'coord': None}


def verify_repo(root: Path) -> dict:
    d = json.loads((root / 'knowledge/d10-interlisp-dwim-safe-suggestion-v1.json').read_text())
    f = json.loads((root / 'knowledge/d1-d9-foundation.json').read_text())
    i = json.loads((root / 'knowledge/d10-v1-semantic-inventory.json').read_text())
    result = validate_dossier(d, f, i)
    assert all(name == '' or not (re.fullmatch('[01]+', name)) for name in [d['candidate']['semantic_name']])
    return result


def main():
    if sys.flags.optimize:
        raise RuntimeError('Do not use Python -O: it disables fail-closed assertions')
    p = argparse.ArgumentParser()
    p.add_argument('--verify-repo', action='store_true', help='Require complete SENS checkout and current domain inventories')
    args = p.parse_args()
    if args.verify_repo:
        print('D10 DWIM SAFE CHECK PASS', json.dumps(verify_repo(ROOT), sort_keys=True))
    else:
        print('D10 DWIM RESEARCH CHECK PASS', json.dumps(validate_dossier(json.loads(RESEARCH.read_text())), sort_keys=True))


if __name__ == '__main__':
    main()
