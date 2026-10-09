#!/usr/bin/env python3
"""Research-only finite binary codebook unique decipherability certificate.

Pure Python reference witness; NOT a SENS evaluator, D2 reader or T5 decoder.
"""
from __future__ import annotations

if not __debug__:
    raise RuntimeError("D10 research gate must not run with Python -O; assertions are required")
from collections import deque
from pathlib import Path
import argparse
import json

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / 'knowledge/d10-unique-decipherability-historical-20261009.json'


def _check_codebook(codebook):
    if not isinstance(codebook, (list, tuple)):
        raise ValueError('expected ordered [(identity,binary-codeword),...]')
    seen = set()
    for row in codebook:
        if not isinstance(row, (list, tuple)) or len(row) != 2:
            raise ValueError('each row is an exact pair')
        symbol, word = row
        if not isinstance(symbol, str) or not symbol or symbol in seen:
            raise ValueError('identity must be a unique nonempty string')
        seen.add(symbol)
        if not isinstance(word, str) or not word or any(c not in '01' for c in word):
            raise ValueError('codeword must be a nonempty binary string')


def unique_decoding_with_witness(codebook):
    """Return (uniquely_decodable, two distinct sequences or None).

    BFS states track the *remaining unmatched suffix* and its owner. A state
    with the same (side, residual) need not be revisited; the code is finite.
    The first witness is shortest in total number of source symbols for this
    deterministic search traversal, not necessarily fewest encoded bits.
    """
    _check_codebook(codebook)
    if len(codebook) < 2:
        return True, None
    by_name = dict(codebook)
    q = deque()
    visited = set()
    def enqueue(side, suffix, left, right):
        if not suffix:
            assert left != right
            assert ''.join(by_name[x] for x in left) == ''.join(by_name[x] for x in right)
            return (False, (left, right))
        key = (side, suffix)
        if key not in visited:
            visited.add(key)
            q.append((side, suffix, left, right))
        return None

    for i, (left_name, left_word) in enumerate(codebook):
        for right_name, right_word in codebook[i+1:]:
            if left_word.startswith(right_word):
                result = enqueue('L', left_word[len(right_word):],
                                 (left_name,), (right_name,))
            elif right_word.startswith(left_word):
                result = enqueue('R', right_word[len(left_word):],
                                 (left_name,), (right_name,))
            else:
                result = None
            if result:
                return result
    while q:
        side, residual, left, right = q.popleft()
        for name, word in codebook:
            # Append one codeword to the currently shorter decoding.
            newleft = left + (name,) if side == 'R' else left
            newright = right + (name,) if side == 'L' else right
            if residual.startswith(word):
                outcome = enqueue(side, residual[len(word):], newleft, newright)
            elif word.startswith(residual):
                outcome = enqueue('R' if side == 'L' else 'L', word[len(residual):],
                                  newleft, newright)
            else:
                outcome = None
            if outcome:
                return outcome
    return True, None


def sardinas_patterson_decision(codebook):
    """Independent fixed-point residual-set implementation, not BFS witness.

    No bound on number of rounds is guessed; finite suffix closure terminates.
    """
    _check_codebook(codebook)
    words = [w for _, w in codebook]
    if len(set(words)) != len(words):
        return False
    c = set(words)
    frontier = {v[len(u):] for u in c for v in c
                if len(v) > len(u) and v.startswith(u)}
    seen = set()
    while frontier:
        if '' in frontier or (frontier & c):
            return False
        unseen = frontier - seen
        if not unseen:
            return True
        seen |= unseen
        frontier = {r[len(u):] for r in unseen for u in c if r.startswith(u)} | {
            u[len(r):] for r in unseen for u in c if u.startswith(r)
        }
    return True


def validate_ledger(ledger, foundation, inventory):
    assert ledger['schema'] == 'sens-d10-unique-decipherability-research/v1'
    assert ledger['research_status'] == 'HOLD-D10-DERIVABILITY-AND-D2-BOUNDARY'
    assert ledger['selected_delta'] == 0
    assert ledger['ratified_delta'] == 0
    assert ledger['changes_to_d2_or_t5'] is False
    assert ledger['snapshot_selected_at_authoring'] <= len(inventory['rows'])
    assert inventory['accounting']['selected_semantic_candidates'] == len(inventory['rows'])
    assert inventory['accounting']['ratified_d10_residents'] == 0
    names = {str(x['semantic_name']).upper() for x in inventory['rows']}
    low = {str(name).upper() for dom in foundation['domains'].values()
           for name in dom.get('residents', {}).values()}
    for row in ledger['proposals']:
        name = row['semantic_name'].upper()
        assert name not in names and name not in low, 'lower-domain or D10 name collision'
        assert row['coordinate'] is None and row['ratified'] is False
        assert row['selected'] is False and row['physical_t5_authorized'] is False
        assert row['surface_uk'] and row['surface_ukr'] and row['semantic_law']
        assert row['positive_witnesses'] and row['falsifiers']
        assert row['source_urls'] and all(x.startswith('https://') for x in row['source_urls'])
        assert row['ownership_boundary']
    return {'existing_selected':len(inventory['rows']),'newly_selected':0,
            'ratified':0,'proposals':len(ledger['proposals'])}


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--repo-root', type=Path, default=ROOT)
    ap.add_argument('--self-test', action='store_true')
    a=ap.parse_args()
    if a.self_test:
        examples = [
            ([('a','0'),('b','11')], True),
            ([('a','0'),('b','01')], True),
            ([('a','0'),('b','01'),('c','10')], False),
            ([('a','0'),('b','1'),('c','000000')], False),
            ([('a','00'),('b','00')], False),
            ([], True),
        ]
        for codebook, expect in examples:
            assert unique_decoding_with_witness(codebook)[0] is expect
            assert sardinas_patterson_decision(codebook) is expect
        print('SARDINAS-PATTERSON SELF-TEST PASS',len(examples),'cases')
        return
    root=a.repo_root
    paths=[root/'knowledge/d10-unique-decipherability-historical-20261009.json',
           root/'knowledge/d1-d9-foundation.json',
           root/'knowledge/d10-v1-semantic-inventory.json']
    data=[json.loads(x.read_text(encoding='utf-8')) for x in paths]
    result=validate_ledger(*data)
    print('D10 UD SOURCE/DUPLICATE GUARD PASS', json.dumps(result,sort_keys=True))

if __name__=='__main__': main()
