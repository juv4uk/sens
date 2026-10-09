#!/usr/bin/env python3
"""D10 research-only guard; never assign words, ratify, or write .sens."""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
def validate(data, inventory, foundation):
    assert data['schema']=='sens-d10-cross-hobby-transducer-research/v1'
    assert data['status']=='HOLD-RESEARCH-UNRATIFIED'
    assert inventory['domain']=='D10'
    assert inventory['accounting']['ratified_d10_residents']==0
    assert set(foundation['current_domains'])=={f'D{i}' for i in range(1,10)}
    selected={str(x.get('semantic_name','')).upper() for x in inventory['rows']}
    laws=data['roots']
    assert len(laws)==2
    assert {r['semantic_name'] for r in laws}=={'FINITE-MEALY-RUN','FINITE-TRANSDUCER-COMPOSE'}
    for r in laws:
        assert r['semantic_name'] not in selected
        assert r['coordinate'] is None and r['ratified'] is False and r['selected'] is False
        assert len(r['witnesses'])>=3 and len(r['falsifiers'])>=3
        assert r['surface_uk'] and r['surface_ukr'] and r['law']
    owners=data['owner_donors']
    assert len(owners)>=5
    for donor in owners:
        assert donor['repo'].startswith('juv4uk/')
        assert len(donor['git_blob'])==40 and donor['path'] and donor['meaning']
    assert 'no canonical selection' not in data.get('governance','').lower() or len(laws)==2
    return {'result':'HOLD','candidate_laws':len(laws),'selected_added':0,'ratified_added':0,'owner_donors':len(owners)}

def main():
    dossier=json.loads((ROOT/'knowledge/d10-finite-transducer-cross-hobby-v1.json').read_text())
    inv=json.loads((ROOT/'knowledge/d10-v1-semantic-inventory.json').read_text())
    foundation=json.loads((ROOT/'knowledge/d1-d9-foundation.json').read_text())
    print(json.dumps(validate(dossier,inv,foundation)))

if __name__=='__main__':main()
