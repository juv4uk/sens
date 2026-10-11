#!/usr/bin/env python3
"""D10 source-grounded research-only affine arithmetic reference, not SENS execution."""
import json
from dataclasses import dataclass
from fractions import Fraction as Q
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
MANIFEST=ROOT/'knowledge/d10-affine-correlated-uncertainty-v1.json'
FOUNDATION=ROOT/'knowledge/d1-d9-foundation.json'
INVENTORY=ROOT/'knowledge/d10-v1-semantic-inventory.json'

@dataclass(frozen=True)
class Affine:
    center: Q
    coeff: tuple

    @staticmethod
    def make(center,coeff):
        if not isinstance(center,Q) or any(not isinstance(k,str) or not k or not isinstance(v,Q) for k,v in coeff.items()):
            raise TypeError('exact rationals and nonempty noise identities required')
        return Affine(center,tuple(sorted((k,v) for k,v in coeff.items() if v)))

    def dictionary(self):
        return dict(self.coeff)

    def hull(self):
        radius=sum((abs(v) for _,v in self.coeff),Q(0))
        return self.center-radius,self.center+radius

    def value(self,epsilon):
        if any(k not in epsilon or abs(epsilon[k])>1 for k,_ in self.coeff):
            raise ValueError('noise valuation outside [-1,1] or missing')
        return self.center+sum((v*epsilon[k] for k,v in self.coeff),Q(0))

def linear(x,y,sign=1):
    coeff=x.dictionary()
    for k,v in y.coeff:
        coeff[k]=coeff.get(k,Q(0))+sign*v
    return Affine.make(x.center+sign*y.center,coeff)

def product_enclosure(x,y,fresh):
    if not isinstance(fresh,str) or not fresh or fresh in x.dictionary() or fresh in y.dictionary():
        raise ValueError('fresh identity required: reuse is forbidden')
    a=x.dictionary();b=y.dictionary()
    c={k:x.center*b.get(k,Q(0))+y.center*a.get(k,Q(0)) for k in (a.keys()|b.keys())}
    # For all |epsilon|<=1 the residual R=(sum ai*ei)(sum bj*ej)
    # satisfies |R| <= (sum |ai|)(sum |bj|). New noise is an
    # enclosure symbol, NOT a claim of statistical independence.
    r=sum((abs(v) for v in a.values()),Q(0))*sum((abs(v) for v in b.values()),Q(0))
    if r:c[fresh]=r
    return Affine.make(x.center*y.center,c)

def check(manifest,foundation=None,inventory=None):
    if not __debug__:raise RuntimeError('optimized Python disables safety assertions')
    assert manifest['schema']=='d10-affine-correlated-uncertainty-research/v1'
    assert manifest['status']=='RESEARCH-UNRATIFIED-NOT-IN-INVENTORY'
    assert manifest['snapshot']['selected_baseline']==630
    assert manifest['snapshot']['canonical_inventory_mutated'] is False
    rows=manifest['rows']
    assert len(rows)==2
    assert {r['semantic_name'] for r in rows}=={'CORRELATED-AFFINE-COMBINATION','SOUND-AFFINE-PRODUCT-ENCLOSURE'}
    assert len({r['id'] for r in rows})==2
    for row in rows:
        assert row['status']=='HOLD-CORE-MATH-DERIVABILITY'
        assert row['coordinate'] is None and row['ratified_resident'] is False
        assert row['selected_in_canonical_inventory'] is False and row['physical_t5_authorized'] is False
        assert row['primary_source'] in manifest['primary_sources']
        assert row['surface_uk'] and row['surface_ukr'] and row['law'] and row['signature']
        assert len(row['positive_witnesses'])>=2 and len(row['falsifiers'])>=2
    if foundation is not None and inventory is not None:
        assert len(inventory['rows'])==inventory['accounting']['selected_semantic_candidates']
        assert inventory['accounting']['selected_semantic_candidates']>=630
        assert inventory['accounting']['ratified_d10_residents']==0
        lower={str(name).upper() for dom in foundation['domains'].values() for name in dom.get('residents',{}).values()}
        selected={str(row['semantic_name']).upper() for row in inventory['rows']}
        assert not ({r['semantic_name'] for r in rows}&(lower|selected)), 'new identity overlaps lower or selected D10'
    return {'proposals':2,'selected_additions':0,'ratified_additions':0}

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--require-checkout',action='store_true')
    args=p.parse_args()
    if args.require_checkout:
        assert FOUNDATION.is_file() and INVENTORY.is_file(), 'real SENS checkout required'
    manifest=json.loads(MANIFEST.read_text())
    f=json.loads(FOUNDATION.read_text()) if FOUNDATION.is_file() else None
    i=json.loads(INVENTORY.read_text()) if INVENTORY.is_file() else None
    print('D10 AFFINE RESEARCH PASS',check(manifest,f,i))
