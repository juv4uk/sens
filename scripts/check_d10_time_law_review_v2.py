#!/usr/bin/env python3
"""D10 time-law research gate. NEVER allocate a D10 bit coordinate from a proposal.

Run inside a complete sens clone for source/dedup checks; supports structural-only
check outside the repo. Behavioral witnesses are *reference models*, not a claim
that the Lisp runtime passed those cases.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys

ROOT=Path(os.environ.get('SENS_ROOT',Path(__file__).resolve().parents[1]))
LEDGER=ROOT/'knowledge/d10-time-law-review-v2.json'

def verify(data, root, *, require_checkout=False):
    if not __debug__:
        raise RuntimeError("BLOCK: Python -O disables assertion-based research gates")
    assert data['schema']=='d10-time-law-review-v2/v1'
    assert data['status']=='RESEARCH-REVIEW-ONLY-NOT-SELECTED'
    assert data['accounting']['counted_in_main']==0
    assert data['accounting']['ratified']==0
    assert data['audit']['proposed_selection_effect']==0
    assert data['audit']['proposed_ratification_effect']==0
    rows=data['rows']; assert len(rows)==data['accounting']['reviewed_new_names']==9
    assert sum(r['triage_status']=='SEMANTIC-CANDIDATE' for r in rows)==5
    assert sum(r['triage_status'].startswith('HOLD-') for r in rows)==4
    assert sum(len(r['witnesses']) for r in rows)==data['audit']['witness_count']
    assert len({r['proposal_id'] for r in rows})==len(rows)
    assert len({r['semantic_name'].upper() for r in rows})==len(rows)
    for row in rows:
        assert row['coordinate'] is None and row['ratified_resident'] is False
        assert row['selected_in_canonical_inventory'] is False
        assert row['source_file']=='lib/time.lisp'
        assert row['source_definition_form']=='00001001'
        assert row['source_git_blob_sha']==data['source_git_blob_sha']
        assert row['observable_law'] and row['falsifier']
        assert row['surface_uk'] and row['surface_ukr']
        assert row['owner_decision']=='PENDING-REVIEW'
        assert row['independent_language_oracle']=='PENDING'
        assert row['behavior_equivalence_proven'] is False
        assert row['unblock_fanout'] is None and row['expressibility_gap'] is None
        assert len(row['witnesses'])>=2
        assert all('input' in v and 'expect' in v for v in row['witnesses'])
    source=root/'lib/time.lisp'
    if source.exists():
        raw=source.read_bytes()
        blob=hashlib.sha1(b'blob '+str(len(raw)).encode()+bytes([0])+raw).hexdigest()
        assert blob==data['source_git_blob_sha'],f'source moved: {blob}'
        lines=raw.decode('utf-8').splitlines()
        for r in rows:
            line=lines[r['source_line']-1]
            prefix='('+r['source_definition_form']+' '+r['semantic_name'].lower()
            assert line.startswith(prefix),(r['semantic_name'],r['source_line'])
            assert line[len(prefix):][:1] in ('',' ',chr(9),')')
        print('SOURCE: pinned Git blob and exact definition lines PASS')
    elif require_checkout:
        raise AssertionError('BLOCK: pinned lib/time.lisp missing; cannot validate source provenance')
    else:
        print('SOURCE: SKIP, no lib/time.lisp in checkout (research fixture only)')
    inventory=root/'knowledge/d10-v1-semantic-inventory.json'
    foundation=root/'knowledge/d1-d9-foundation.json'
    if inventory.exists() and foundation.exists():
        inv=json.loads(inventory.read_text(encoding='utf-8'))
        fd=json.loads(foundation.read_text(encoding='utf-8'))
        old={r['semantic_name'].upper() for r in inv['rows']}
        lower={str(n).upper() for d in fd['domains'].values() for n in d.get('residents',{}).values()}
        names={r['semantic_name'].upper() for r in rows}
        assert not(names&old),names&old
        assert not(names&lower),names&lower
        assert inv['accounting']['ratified_d10_residents']==0
        print(f'DEDUP: 0 collisions against D1-D9 and {len(inv["rows"])} selected D10')
    elif require_checkout:
        raise AssertionError('BLOCK: domain registries missing; cannot validate D1-D10 duplicate status')
    else:
        print('DEDUP: SKIP, full D1-D10 registries unavailable in checkout (research fixture only)')
    if require_checkout:
        assert inv['accounting']['selected_semantic_candidates'] == len(inv['rows'])
        assert inv['accounting']['selected_semantic_candidates'] >= 625
    print(f'D10-TIME-REVIEW-V2: PASS ({len(rows)} reviewed, {sum(len(r["witnesses"]) for r in rows)} reference cases; selected 0; ratified 0)')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--require-checkout', action='store_true', help='Fail closed without pinned lib/time.lisp and canonical D1–D10 registries')
    args=parser.parse_args()
    verify(json.loads(LEDGER.read_text(encoding='utf-8')), ROOT, require_checkout=args.require_checkout)
