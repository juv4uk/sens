#!/usr/bin/env python3
"""Fail-closed review of D10 proposals already covered by exact D9 residents.

Run from a COMPLETE sens repository checkout. This program never modifies tables.
"""
import argparse
import hashlib
import json
from pathlib import Path

REVIEW = 'knowledge/d10-d9-donor-dedup-v1.json'
D9 = 'knowledge/d1-d9-foundation.json'
D10 = 'knowledge/d10-v1-semantic-inventory.json'


def sha_blob(raw):
    return hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()


def verify(root):
    root = Path(root)
    review = json.loads((root / REVIEW).read_text(encoding='utf8'))
    foundation = json.loads((root / D9).read_text(encoding='utf8'))
    inventory = json.loads((root / D10).read_text(encoding='utf8'))
    assert review['schema'] == 'sens-d10-d9-donor-dedup-v1'
    assert review['status'] == 'RESEARCH-HOLD-NO-INVENTORY-MUTATION'
    assert review['ratified_d10_snapshot'] == 0
    assert inventory['accounting']['ratified_d10_residents'] == 0
    assert len(inventory['rows']) == inventory['accounting']['selected_semantic_candidates']
    assert len(inventory['rows']) >= review['selected_main_snapshot']
    d9 = foundation['domains']['D9']['residents']
    selected = {row['semantic_name'].upper() for row in inventory['rows']}
    donors = {}
    for source in review['donors']:
        raw = (root / source['path']).read_bytes()
        assert sha_blob(raw) == source['git_blob_sha'], source['path']
        donors[source['path']] = raw.decode('utf8').splitlines()
    assert len(review['d9_existing']) == 7
    for row in review['d9_existing']:
        assert d9[row['coordinate']] == row['semantic_name'], row
        assert row['semantic_name'] not in selected, row
        assert row['conclusion'] == 'EXISTING-D9'
        line = donors[row['donor']][row['line']-1].strip()
        assert line.startswith('(00001001 ' + row['source_name'] + ' ') or line == '(00001001 ' + row['source_name'] or line.startswith('(00001011 ' + row['source_name'] + ' ' ) or line == '(00001011 ' + row['source_name'], (row,line)
    seen = {row['semantic_name'] for row in review['d9_existing']}
    assert len(seen) == 7
    assert len(review['false_promotions']) >= 5
    for row in review['false_promotions']:
        assert row['verdict'] == 'HOLD-D9-EQUIVALENCE'
        assert row['existing'] in seen
        assert row['falsifier']
    assert {x['name'] for x in review['separate_review']} == {'APPLICABLE-METHODS','STANDARD-METHOD-COMBINATION','FIND-RESTART'}
    assert all(x['coordinate'] is None and x['status']=='PENDING-OWNER-REVIEW' and x['falsifier'] for x in review['separate_review'])
    assert not any(x['name'] in selected for x in review['separate_review'])
    return {'d9_residents_verified':len(seen), 'false_promotions_held':len(review['false_promotions']), 'other_reviews':len(review['separate_review']), 'new_d10_selected':0, 'ratified':0}


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--root',default='.')
    args=p.parse_args()
    print('D10/D9 DEDUP PASS',json.dumps(verify(args.root),sort_keys=True))


if __name__=='__main__':
    main()
