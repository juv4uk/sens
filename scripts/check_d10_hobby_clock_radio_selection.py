#!/usr/bin/env python3
"""D10 source-anchored exact clock/SDR law witnesses, not native runtime parity."""
from __future__ import annotations
import argparse, copy, itertools, json
from fractions import Fraction as F
from pathlib import Path
from check_d10_selection_transition_history import verify_history
ROOT=Path(__file__).resolve().parents[1]
P=ROOT/"knowledge/d10-clock-radio-math-selection-20261009.json"
I=ROOT/"knowledge/d10-v1-semantic-inventory.json"
S=ROOT/"knowledge/d10-fill-v1-state.json"
FND=ROOT/"knowledge/d1-d9-foundation.json"
H=ROOT/"knowledge/d10-selection-transition-history.json"
D=ROOT/"docs/architecture/ARCHIPELAGO-V1.uk.md"
NAMES=("ALLAN-VARIANCE","DIFFERENTIAL-ENCODE","DIFFERENTIAL-DECODE","DIFFERENTIAL-PHASOR")
def read(p):return json.loads(p.read_text(encoding="utf-8"))
def avar(seq):
    values=[F(x) for x in seq]
    if len(values)<2:raise ValueError("Allan variance requires N>=2")
    return sum(((b-a)**2 for a,b in zip(values,values[1:])),F(0))/(2*(len(values)-1))
def enc(symbols,M,prev):
    if not isinstance(M,int) or M<2 or not (0<=prev<M):raise ValueError("invalid alphabet/state")
    out=[]
    for x in symbols:
        if not isinstance(x,int) or not (0<=x<M):raise ValueError("invalid symbol")
        prev=(x+prev)%M
        out.append(prev)
    return out,prev
def dec(symbols,M,prev):
    if not isinstance(M,int) or M<2 or not (0<=prev<M):raise ValueError("invalid alphabet/state")
    out=[]
    for encoded in symbols:
        if not isinstance(encoded,int) or not (0<=encoded<M):raise ValueError("invalid symbol")
        out.append((encoded-prev)%M)
        prev=encoded
    return out,prev
def mul_conj(a,b):
    x,y=F(a[0]),F(a[1]);u,v=F(b[0]),F(b[1])
    return (x*u+y*v,y*u-x*v)
def phasor(xs,prev):
    out=[]
    for z in xs:
        out.append(mul_conj(z,prev))
        prev=z
    return out,prev
def check(p,i,s,f,h,doc):
    assert p["schema"]=="d10-clock-radio-math-intake/v1"
    assert p["status"]=="SELECTED-RESEARCH-ONLY-UNRATIFIED"
    assert p["accounting"]=={"before":630,"added":4,"after":634,"unplaced":378,"remaining":390,"forced_coordinates_unchanged":256,"ratified":0}
    assert len(i["rows"])==634 and len(i["sources"])>=1
    assert [r["semantic_name"] for r in p["selected_rows"]]==list(NAMES)
    assert [r["semantic_name"] for r in i["rows"][-4:]]==list(NAMES)
    assert len({r["stable_id"] for r in i["rows"]})==634
    assert len({r["semantic_name"] for r in i["rows"]})==634
    assert i["accounting"]=={"selected_semantic_candidates":634,"law_forced_coordinates":256,"unplaced_selected_candidates":378,"remaining_semantic_inventory":390,"ratified_d10_residents":0}
    assert s["target"]["selected_semantic_candidates"]==634
    assert s["target"]["remaining_semantic_candidates"]==390
    assert s["target"]["unplaced_selected_candidates"]==378
    assert s["target"]["ratified_residents"]==0
    assert "D10 selected              634/1024" in doc
    assert "unplaced                  378" in doc
    assert "remaining                 390" in doc
    assert i["sources"][-1]=="knowledge/d10-clock-radio-math-selection-20261009.json"
    assert len(h["transitions"])>=3
    assert h["transitions"][-1]["id"]=="d10.hobby.clock-radio.20261009"
    assert h["transitions"][-1]["added_stable_ids"]==[r["stable_id"] for r in p["selected_rows"]]
    verify_history(i,h)
    lower={str(x).upper() for z in f["domains"].values() for x in z["residents"].values()}
    assert not lower.intersection(NAMES)
    assert sum(r["coordinate"] is not None for r in i["rows"])==256
    for proposal,row in zip(p["selected_rows"],i["rows"][-4:]):
        assert proposal["semantic_name"]==row["semantic_name"] and proposal["stable_id"]==row["stable_id"]
        assert row["source_class"]=="HOBBY-CLOCK-RADIO-PRIMARY-20261009" and row["status"]=="SELECTED-RESEARCH-CANDIDATE"
        assert proposal["decision"]=="SELECT-D10-CANDIDATE"
        assert proposal["source_class"]==row["source_class"]
        assert proposal["primary_url"]==row["primary_url"] and row["source_path"]==i["sources"][-1]
        assert row["coordinate"] is None and row["coordinate_basis"]=="UNPLACED"
        assert row["ratified_resident"] is False and proposal["ratified_resident"] is False
        assert row["physical_t5_authorized"] is False and proposal["physical_t5_authorized"] is False
        assert row["surface_uk"] and row["surface_ukr"]
        assert proposal["witnesses"] and proposal["falsifiers"] and proposal["nearest"] and proposal["owner_question"]
    return True
def witnesses():
    assert avar([0,0])==0
    assert avar([0,1])==F(1,2)
    assert avar([0,1,0])==F(1,2)
    assert avar([1,2,3])==F(1,2)
    assert avar([F(1,3),F(2,3)])==F(1,18)
    for shift in (-7,F(1,5),0,10):
        assert avar([shift+x for x in [0,1,0]])==F(1,2)
    for bad in ([],[0]):
        try: avar(bad)
        except ValueError:pass
        else:raise AssertionError("short Allan sample accepted")
    assert enc([1,2,3],4,0)==([1,3,2],2)
    assert dec([1,3,2],4,0)==([1,2,3],2)
    assert enc([],4,3)==([],3) and dec([],4,3)==([],3)
    assert enc([1,1],4,0)==([1,2],2)
    tests=0
    for M in range(2,7):
        for length in range(0,5):
            for sample in itertools.product(range(M),repeat=length):
                for initial in range(M):
                    y,last=enc(sample,M,initial)
                    x,previous_input=dec(y,M,initial)
                    assert x==list(sample) and previous_input==last
                    for split in range(length+1):
                        aa,state1=enc(sample[:split],M,initial)
                        bb,state2=enc(sample[split:],M,state1)
                        assert aa+bb==y and state2==last
                        ca,state3=dec(y[:split],M,initial)
                        cb,state4=dec(y[split:],M,state3)
                        assert ca+cb==x and state4==last
                    tests+=1
    one=(F(1),F(0));ii=(F(0),F(1));minus=(F(-1),F(0))
    xs=[one,ii,minus]
    assert phasor(xs,one)==([one,ii,ii],minus)
    scaled=[(F(2),F(0)),(F(0),F(3))]
    assert phasor(scaled,one)==([(F(2),F(0)),(F(0),F(6))],scaled[-1])
    assert phasor([],ii)==([],ii)
    assert mul_conj(minus,ii)==ii
    return tests
def adverse(p,i,s,f,h,doc):
    def reject(change):
        pp,ii,ss,hh=(copy.deepcopy(x) for x in (p,i,s,h))
        change(pp,ii,ss,hh)
        try:check(pp,ii,ss,f,hh,doc)
        except (AssertionError,ValueError):return
        raise AssertionError("adversarial metadata mutation not rejected")
    reject(lambda p,i,s,h:i["rows"][-1].__setitem__("coordinate","1111111111"))
    reject(lambda p,i,s,h:i["rows"][-1].__setitem__("ratified_resident",True))
    reject(lambda p,i,s,h:p["selected_rows"][-1].__setitem__("ratified_resident",True))
    reject(lambda p,i,s,h:i["rows"][4].__setitem__("behavior","FORGED"))
    reject(lambda p,i,s,h:i["rows"][-1].__setitem__("semantic_name","DPB"))
    reject(lambda p,i,s,h:p["selected_rows"][0].__setitem__("primary_url","https://wrong.example"))
    reject(lambda p,i,s,h:i["sources"].pop())
    reject(lambda p,i,s,h:s["target"].__setitem__("selected_semantic_candidates",630))
    reject(lambda p,i,s,h:h["transitions"][-1].__setitem__("previous_inventory_blob_sha","0"*40))
    reject(lambda p,i,s,h:p["selected_rows"][0].__setitem__("witnesses",[]))
def main():
    a=argparse.ArgumentParser();a.add_argument("--self-test",action="store_true");o=a.parse_args()
    p,i,s,f,h=map(read,(P,I,S,FND,H));doc=D.read_text(encoding="utf-8")
    check(p,i,s,f,h,doc);n=witnesses()
    if o.self_test:adverse(p,i,s,f,h,doc)
    print("PASS D10 hobby clock-radio four selected 630->634, exact differential roundtrip cases",n,"10 adversarial checks; 0 coords/ratified")
if __name__=="__main__":main()
