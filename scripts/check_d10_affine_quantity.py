#!/usr/bin/env python3
"""D10 research-only exact affine physical quantity POINT/DELTA law.

Mathematical donor: NIST SP811 §8.5 Celsius absolute temperature vs interval.
No floating-point coercion, no hardware IO, no selected D10 opcode.
"""
from __future__ import annotations
import argparse
import copy
from dataclasses import dataclass
from fractions import Fraction
import json
import random
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
CORPUS=ROOT/"knowledge/d10-affine-quantity-point-delta-20261009.json"
INVENTORY=ROOT/"knowledge/d10-v1-semantic-inventory.json"
FOUNDATION=ROOT/"knowledge/d1-d9-foundation.json"
NAME="AFFINE-QUANTITY-TRANSPORT"
TEMP=(0,0,0,0,1,0,0)
LENGTH=(1,0,0,0,0,0,0)
DIMLESS=(0,0,0,0,0,0,0)


def exact(x):
    if type(x) is int or isinstance(x, Fraction):
        return Fraction(x)
    if type(x) is str and x:
        return Fraction(x)
    raise TypeError("only explicit exact rational (not float or bool)")


@dataclass(frozen=True)
class Unit:
    dimensions: tuple[Fraction,...]
    scale: Fraction
    origin: Fraction

    def __init__(self, dimensions, scale, origin):
        if len(dimensions)!=7:
            raise ValueError("seven exact base-dimension exponents required")
        ds=tuple(exact(d) for d in dimensions)
        a,b=exact(scale),exact(origin)
        if a<=0:
            raise ValueError("unit scale must be positive")
        object.__setattr__(self,"dimensions",ds)
        object.__setattr__(self,"scale",a)
        object.__setattr__(self,"origin",b)


def transport(value,kind,source:Unit,target:Unit):
    x=exact(value)
    if kind not in ("POINT","DELTA"):
        raise ValueError("kind must be POINT or DELTA")
    if not isinstance(source,Unit) or not isinstance(target,Unit):
        raise TypeError("unit descriptors required")
    if source.dimensions!=target.dimensions:
        raise ValueError("dimension mismatch, no implicit unit coercion")
    if kind=="POINT":
        return ((source.scale*x+source.origin-target.origin)/target.scale,kind)
    return ((source.scale*x)/target.scale,kind)


def independently_solve(value,kind,source,target):
    """Compare separately derived inverse matrix of rational affine map."""
    x=exact(value)
    if source.dimensions!=target.dimensions:
        raise ValueError("dimension mismatch")
    slope=source.scale/target.scale
    intercept=Fraction(0) if kind=="DELTA" else (
        source.origin-target.origin)/target.scale
    return slope*x+intercept


def verify(data,inv,lower):
    c=data["candidate"]
    assert data["schema"]=="d10-affine-quantity-point-delta/v1"
    assert data["status"]=="RESEARCH-PENDING-OWNER-REVIEW"
    assert c["semantic_name"]==NAME
    assert c["stable_proposal_id"]=="D10P-6101"
    assert c["coordinate"] is None and c["ratified"] is False
    assert c["selected"] is False and c["domain_width"]==10
    assert c["proposal_status"]=="pending-review"
    assert c["surface_uk"] and c["surface_ukr"] and c["law"]
    assert len(data["sources"])>=2
    assert data["sources"][0]["url"].startswith("https://www.nist.gov/")
    assert data["sources"][1]["url"].startswith("https://www.bipm.org/")
    assert data["source_boundary"].startswith("NIST/BIPM")
    assert len(c["witnesses"])>=6 and len(c["falsifiers"])>=6
    assert len(data["holds"])==4
    assert all(x["status"].startswith("HOLD-") for x in data["holds"])
    assert data["accounting"]=={"selected_added":0,"ratified_added":0,"coordinate_added":0,"ledger_rows_if_approved":1}
    assert c["mathematically_derivable"] is True
    assert inv["domain"]=="D10" and inv["capacity"]==1024
    assert inv["accounting"]["selected_semantic_candidates"]>=630
    assert inv["accounting"]["ratified_d10_residents"]==0
    assert len(inv["rows"])==inv["accounting"]["selected_semantic_candidates"]
    names={r["semantic_name"] for r in inv["rows"]}
    assert NAME not in names, "already selected, coordinate with canonical transition writer"
    assert {n["semantic_name"] for n in c["preselected_neighbors"]} <= names
    assert lower["status"]=="owner-ratified"
    assert NAME not in {str(n).upper()
                        for d in lower["domains"].values()
                        for n in d["residents"].values()}
    assert data["snapshot"]["d10_inventory_sha"]=="a55f307c27f17091795d75ebfcd7d051547d80bc"
    print("D10 AFFINE-QUANTITY: source-pinned NOT-SELECTED candidate PASS")


def mutate_check(data,inv,lower):
    changes=[
      lambda x:x["candidate"].update(selected=True),
      lambda x:x["candidate"].update(ratified=True),
      lambda x:x["candidate"].update(coordinate="1000000000"),
      lambda x:x["candidate"].update(domain_width=9),
      lambda x:x["candidate"].update(semantic_name="SCIENCE-MERGE-DIMENSIONS"),
      lambda x:x["candidate"].update(falsifiers=[]),
      lambda x:x["accounting"].update(selected_added=1),
      lambda x:x["sources"][0].update(url="https://example.invalid"),
      lambda x:x.update(status="SELECTED"),
      lambda x:x["candidate"].update(mathematically_derivable=False),
    ]
    for i,fn in enumerate(changes):
        m=copy.deepcopy(data)
        fn(m)
        try:
            verify(m,inv,lower)
        except AssertionError:
            continue
        raise AssertionError(f"forged research document mutation {i} escaped")
    print("D10 AFFINE-QUANTITY: 10/10 adversarial dossier mutations rejected")


class LawTests(unittest.TestCase):
    def setUp(self):
        self.K=Unit(TEMP,1,0)
        self.C=Unit(TEMP,1,Fraction(27315,100))
        self.F=Unit(TEMP,Fraction(5,9),Fraction(45967,180))

    def test_si_points_and_deltas(self):
        self.assertEqual(transport(0,"POINT",self.C,self.K),(Fraction(27315,100),"POINT"))
        self.assertEqual(transport(5,"DELTA",self.C,self.K),(Fraction(5),"DELTA"))
        self.assertEqual(transport(32,"POINT",self.F,self.K),(Fraction(27315,100),"POINT"))
        self.assertEqual(transport(9,"DELTA",self.F,self.K),(Fraction(5),"DELTA"))
        self.assertEqual(transport(Fraction(27315,100),"POINT",self.K,self.C),(Fraction(0),"POINT"))
        self.assertEqual(transport(100,"POINT",self.C,self.F),(Fraction(212),"POINT"))

    def test_roundtrip_and_composition(self):
        units=[self.K,self.C,self.F,Unit(TEMP,Fraction(11,13),Fraction(3,7))]
        for a in units:
            for b in units:
                for c in units:
                    for kind in ("POINT","DELTA"):
                        for value in [-7,-2,Fraction(3,7),0,9,99]:
                            y=transport(value,kind,a,b)[0]
                            self.assertEqual(transport(y,kind,b,c),
                                             transport(value,kind,a,c))
                            self.assertEqual(transport(y,kind,b,a),
                                             (Fraction(value),kind))

    def test_independent_affine_coefficients(self):
        rng=random.Random(20261009)
        for _ in range(5000):
            a=Unit(DIMLESS,Fraction(rng.randint(1,100),rng.randint(1,200)),
                   Fraction(rng.randint(-500,500),rng.randint(1,150)))
            b=Unit(DIMLESS,Fraction(rng.randint(1,100),rng.randint(1,200)),
                   Fraction(rng.randint(-500,500),rng.randint(1,150)))
            x=Fraction(rng.randint(-500,500),rng.randint(1,150))
            for kind in ("POINT","DELTA"):
                self.assertEqual(transport(x,kind,a,b)[0],
                                 independently_solve(x,kind,a,b))

    def test_point_difference_covariance(self):
        a,b=self.C,self.F
        for x in [Fraction(-3,7),0,Fraction(20),100]:
            for y in [-41,Fraction(3,11),0,21]:
                difference=transport(x,"POINT",a,b)[0]-transport(y,"POINT",a,b)[0]
                delta=transport(x-y,"DELTA",a,b)[0]
                self.assertEqual(difference,delta)

    def test_calibration_origin_only_affects_points(self):
        a=Unit(DIMLESS,1,Fraction(-1,10))
        b=Unit(DIMLESS,1,Fraction(1,10))
        self.assertEqual(transport(4,"POINT",a,b),(Fraction(19,5),"POINT"))
        self.assertEqual(transport(4,"DELTA",a,b),(Fraction(4),"DELTA"))

    def test_mismatched_dimensions_and_bad_inputs(self):
        u=Unit(LENGTH,1,0)
        for kind in ("POINT","DELTA"):
            with self.assertRaises(ValueError):
                transport(2,kind,self.C,u)
        for val in [0.5,True,None]:
            with self.assertRaises(TypeError):
                transport(val,"POINT",self.K,self.C)
        for bad in [0,-1]:
            with self.assertRaises(ValueError):
                Unit(TEMP,bad,0)
        for bad in [(0,0), (0,)*8]:
            with self.assertRaises(ValueError):
                Unit(bad,1,0)
        with self.assertRaises(ValueError):
            transport(2,"unknown",self.C,self.K)
        with self.assertRaises(TypeError):
            Unit(TEMP,1,0.1)

    def test_source_registry_and_negative_controls(self):
        data=json.loads(CORPUS.read_text(encoding="utf-8"))
        inv=json.loads(INVENTORY.read_text(encoding="utf-8"))
        lower=json.loads(FOUNDATION.read_text(encoding="utf-8"))
        verify(data,inv,lower)
        mutate_check(data,inv,lower)


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--self-test",action="store_true")
    args=p.parse_args()
    dossier=json.loads(CORPUS.read_text(encoding="utf-8"))
    inventory=json.loads(INVENTORY.read_text(encoding="utf-8"))
    foundation=json.loads(FOUNDATION.read_text(encoding="utf-8"))
    verify(dossier,inventory,foundation)
    if args.self_test:
        suite=unittest.defaultTestLoader.loadTestsFromTestCase(LawTests)
        result=unittest.TextTestRunner(verbosity=2).run(suite)
        if not result.wasSuccessful():
            raise SystemExit(1)
