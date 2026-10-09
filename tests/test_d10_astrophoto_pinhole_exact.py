#!/usr/bin/env python3
"""Independent exact pinhole camera reference; research only, no SENS native parity."""
import copy
import json
from fractions import Fraction as F
from itertools import product
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILE = ROOT / "knowledge/d10-astrophoto-exact-pinhole-research-20261009.json"

def rational(v):
    if isinstance(v, (float, bool)):
        raise TypeError("Only exact rational, no float or bool")
    return F(v)

def project(x, y, z, fx, fy, cx, cy):
    x, y, z, fx, fy, cx, cy = map(rational, (x,y,z,fx,fy,cx,cy))
    if z == 0:
        raise ValueError("zero camera-frame depth")
    return (fx * x / z + cx, fy * y / z + cy)

def ray(u, v, fx, fy, cx, cy):
    u, v, fx, fy, cx, cy = map(rational,(u,v,fx,fy,cx,cy))
    if fx == 0 or fy == 0:
        raise ValueError("zero intrinsic focal length")
    return ((u-cx)/fx, (v-cy)/fy, F(1))

def check_source(data):
    assert data["schema"] == "d10-cross-hobby-pinhole-geometric-law/v1"
    assert data["status"] == "HOLD-RESEARCH-UNRATIFIED"
    assert data["snapshot"]["selected"] == 634
    assert data["snapshot"]["d10_git_blob"] == "65014431ac3e64633cd0be3630cfafc5e7a9aea3"
    assert data["policy"]["selected_delta"] == 0
    assert data["policy"]["ratified_delta"] == 0
    assert data["policy"]["coordinate_delta"] == 0
    assert data["policy"]["physical_t5_admission"] is False
    assert data["source"]["url"].startswith("https://docs.opencv.org/")
    expected = ["PINHOLE-IMAGE-PROJECT","PIXEL-TO-CAMERA-RAY"]
    assert [r["semantic_name"] for r in data["candidates"]] == expected
    for row in data["candidates"]:
        assert row["status"] == "HOLD-EXACT-MATH-DERIVABILITY"
        assert row["coordinate"] is None and row["ratified"] is False
        assert row["width"] == 10
        assert len(row["positives"]) >= 2 and len(row["falsifiers"]) >= 3
        assert "dedup" in row and "behavior" in row
    assert len(data["derived_and_hold"]) >= 3

def check_witnesses(data):
    count = 0
    projection, inverse = data["candidates"]
    for e in projection["positives"]:
        assert list(map(str, project(*e["args"]))) == e["expected"]
        count += 1
    for e in inverse["positives"]:
        assert list(map(str, ray(*e["args"]))) == e["expected"]
        count += 1
    all_xy = [F(x, d) for d in (1,2,3,5) for x in range(-5, 6)]
    all_xy = sorted(set(all_xy))
    for x,y,z in product(all_xy, all_xy, (F(1),F(3),F(-2))):
        fx,fy,cx,cy = F(11,3),F(5,2),F(-1,4),F(7,5)
        u,v = project(x,y,z,fx,fy,cx,cy)
        # Independent homogeneous relation, no shared division implementation.
        assert u*z == fx*x+cx*z
        assert v*z == fy*y+cy*z
        for scale in (F(-2), F(2,3)):
            assert project(scale*x,scale*y,scale*z,fx,fy,cx,cy) == (u,v)
        if fx and fy:
            rx,ry,rz = ray(u,v,fx,fy,cx,cy)
            assert rz == 1 and project(rx,ry,rz,fx,fy,cx,cy) == (u,v)
            assert rx == x/z and ry == y/z
        count += 1
    return count

def negative_controls(data):
    changes = [
      lambda j:j["candidates"][0].update(coordinate="0"*10),
      lambda j:j["candidates"][1].update(ratified=True),
      lambda j:j["candidates"][0].update(status="SELECTED"),
      lambda j:j["policy"].update(selected_delta=2),
      lambda j:j["policy"].update(ratified_delta=1),
      lambda j:j["policy"].update(physical_t5_admission=True),
      lambda j:j["snapshot"].update(d10_git_blob="0"*40),
      lambda j:j["candidates"][1]["positives"].clear(),
      lambda j:j["candidates"][0]["falsifiers"].clear(),
      lambda j:j["source"].update(url="https://example.invalid/"),
    ]
    for k,fn in enumerate(changes):
        j=copy.deepcopy(data)
        fn(j)
        try:
            check_source(j)
        except AssertionError:
            continue
        raise AssertionError("Negative control escaped: " + str(k))
    for args in [
        (1,2,0,10,10,0,0),
        (1,2,0.0,10,10,0,0),
    ]:
        try: project(*args)
        except (ValueError,TypeError): pass
        else: raise AssertionError("invalid camera projection accepted")
    for args in [(1,2,0,1,0,0),(1,2,1,0,0,0)]:
        try: ray(*args)
        except ValueError: pass
        else: raise AssertionError("invalid inverse accepted")

def main():
    j=json.loads(FILE.read_text(encoding="utf-8"))
    check_source(j)
    total=check_witnesses(j)
    negative_controls(j)
    assert total>=10000, total
    print(f"D10 PINHOLE: PASS exact_cases={total}, 10 falsified mutation guards, 4 invalid-domain rejections.")
    print("Research HOLD: 0 selected, 0 ratified, 0 coords, native SENS parity NOT claimed.")

if __name__=="__main__":
    main()
