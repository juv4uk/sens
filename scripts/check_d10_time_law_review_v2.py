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
import subprocess
import sys

ROOT=Path(os.environ.get('SENS_ROOT',Path(__file__).resolve().parents[1]))
LEDGER=ROOT/'knowledge/d10-time-law-review-v2.json'

# Чинні українські імена перевіряємо за живим SENS-джерелом.
# Історичні semantic_name та surface_ukr у дослідницькому журналі
# не є викличними головами і не призначають координат D10.
LIVE_UKRAINIAN_DEFINITIONS = {
    'CIVIL-FROM-DAYS': 'грегоріанська-дата-з-числа-днів',
    'INTERNET-TIME-MODE-VALID?': 'інтернет-час-режим-припустимий?',
    'INTERNET-TIME-STRATUM-VALID?': 'інтернет-час-рівень-припустимий?',
    'INTERNET-TIME-FIELDS->OBSERVATION': 'тлумачити-поля-відповіді-часу',
    'INTERNET-TIME-RAW->OBSERVATION': 'перетворити-сирі-дані-часу-на-спостереження',
    'INTERNET-TIME-OBSERVATION->UTC': 'дати-календарне-значення-схваленому-часу',
    'TIMEZONE-DECLARATIONS->OBSERVATION': 'обрати-достовірне-джерело-часового-поясу',
    'TIMEZONE-RAW->OBSERVATION': 'часовий-пояс-сирий-до-спостереження',
    'TIMEZONE-CONFIG': 'створити-перевірене-значення-поясу',
}

def verify(data, root, *, require_checkout=False, pinned_source=None):
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
        assert row['source_definition_form']=='0011'
        assert row['source_git_blob_sha']==data['source_git_blob_sha']
        assert row['observable_law'] and row['falsifier']
        assert row['surface_uk'] and row['surface_ukr']
        assert row['owner_decision']=='PENDING-REVIEW'
        assert row['independent_language_oracle']=='PENDING'
        assert row['behavior_equivalence_proven'] is False
        assert row['unblock_fanout'] is None and row['expressibility_gap'] is None
        assert len(row['witnesses'])>=2
        assert all('input' in v and 'expect' in v for v in row['witnesses'])
    # Source history and live SENS have DIFFERENT ownership and lifetimes.
    # The pinned SHA is an immutable research witness, not the required SHA
    # of the evolving source file. A lawful D1/D4 migration must not alter
    # the historical proof or silently ratify D10 candidates.
    source=root/'lib/time.lisp'
    if source.exists():
        assert set(LIVE_UKRAINIAN_DEFINITIONS)=={row['semantic_name'] for row in rows}, (
            'LIVE: дослідницький перелік і українські свідки розійшлися'
        )
        current_lines=source.read_text(encoding='utf-8').splitlines()
        for row in rows:
            українське_імя=LIVE_UKRAINIAN_DEFINITIONS[row['semantic_name']]
            prefix='(визначити '+українське_імя
            matches=[
                line for line in current_lines
                if line.startswith(prefix)
                and line[len(prefix):][:1] in ('',' ',chr(9),')')
            ]
            assert len(matches)==1, (
                f"LIVE: українське D4 DEFINE missing/duplicated: "
                f"{row['semantic_name']} -> {українське_імя}"
            )
        print('LIVE: девʼять українських D4-визначень існують; архівний SHA незалежний')
    elif require_checkout:
        raise AssertionError('BLOCK: pinned lib/time.lisp missing; cannot validate live source')
    else:
        print('LIVE: SKIP, no lib/time.lisp in checkout (research fixture only)')

    archived=None
    if pinned_source is not None:
        path=Path(pinned_source)
        assert path.is_file(), f'BLOCK: pinned source snapshot missing: {path}'
        archived=path.read_bytes()
    else:
        # A full local clone can supply historical Git objects without network.
        # CI may be shallow; its workflow fetches this exact blob via GitHub.
        result=subprocess.run(
            ['git','-C',str(root),'cat-file','blob',data['source_git_blob_sha']],
            capture_output=True, check=False,
        )
        if result.returncode==0:
            archived=result.stdout
    if archived is not None:
        sha=hashlib.sha1(b'blob '+str(len(archived)).encode()+b'\0'+archived).hexdigest()
        assert sha==data['source_git_blob_sha'], f'pinned source moved: {sha}'
        frozen_lines=archived.decode('utf-8').splitlines()
        for row in rows:
            assert 0<row['source_line']<=len(frozen_lines),row['semantic_name']
            line=frozen_lines[row['source_line']-1]
            prefix='('+row['source_definition_form']+' '+row['semantic_name'].lower()
            assert line.startswith(prefix),(row['semantic_name'],row['source_line'])
            assert line[len(prefix):][:1] in ('',' ',chr(9),')')
        print('ARCHIVE: verified immutable Git blob and nine exact historical D4 definitions')
    elif require_checkout:
        raise AssertionError('BLOCK: pinned historical Git blob unavailable; supply --pinned-source')
    else:
        print('ARCHIVE: SKIP, historical blob not present in this partial clone')
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
    parser.add_argument('--pinned-source', type=Path, help='Immutable source fetched by the ledger Git blob SHA')
    args=parser.parse_args()
    verify(json.loads(LEDGER.read_text(encoding='utf-8')), ROOT, require_checkout=args.require_checkout, pinned_source=args.pinned_source)
