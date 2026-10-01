#!/usr/bin/env python3
"""#1989 Cachegrind runner for carrier_bench.c.

Differential I-refs:
  op_i_refs = median(full) - median(prepare)

Both modes perform identical process startup and candidate preparation.
The inner loop is identical length; prepare substitutes a tiny checksum loop.
"""

from __future__ import annotations
import argparse, csv, os, re, statistics, subprocess, tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
SRC=HERE/"carrier_bench.c"
BIN=HERE/"carrier_bench"

FULL_WIDTHS=(3,4,5,6,8,16,32,64,65,128)
OPS=("construct","eq","hash","bit","append","parent","prefix","project","clone")
CANDS=("sens8","inline64","bitbytes","spill")
SMOKE=[
    ("sens8","eq",8),
    ("inline64","eq",8),
    ("bitbytes","eq",8),
    ("spill","eq",8),
    ("inline64","append",64),
    ("bitbytes","append",64),
    ("spill","append",64),
    ("bitbytes","eq",128),
    ("spill","eq",128),
    ("bitbytes","prefix",128),
    ("spill","prefix",128),
]

IRE=re.compile(r"I\s*refs:\s*([0-9,]+)")
KV=re.compile(r"([a-zA-Z_]+)=([^\s]+)")

def build():
    subprocess.run(["gcc","-O2","-std=c11","-Wall","-Wextra","-o",str(BIN),str(SRC)],check=True)

def invoke(cand,op,width,iters,mode,valgrind):
    cmd=[str(BIN),cand,op,str(width),str(iters),mode]
    if not valgrind:
        cp=subprocess.run(cmd,text=True,capture_output=True,check=True)
        return None,dict(KV.findall(cp.stdout))
    with tempfile.TemporaryDirectory() as td:
        log=Path(td)/"vg.log"
        cmd=["valgrind","--tool=cachegrind","--cache-sim=no","--cachegrind-out-file=/dev/null",
             f"--log-file={log}",*cmd]
        cp=subprocess.run(cmd,text=True,capture_output=True,check=True)
        data=log.read_text(errors="replace")
        m=IRE.search(data)
        if not m: raise RuntimeError(data[-2000:])
        return int(m.group(1).replace(",","")),dict(KV.findall(cp.stdout))

def cases(smoke):
    if smoke: return list(SMOKE)
    out=[]
    for c in CANDS:
        for w in FULL_WIDTHS:
            for op in OPS:
                if c=="sens8" and w!=8: continue
                out.append((c,op,w))
    return out

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--smoke",action="store_true")
    ap.add_argument("--iters",type=int,default=20000)
    ap.add_argument("--reps",type=int,default=3)
    ap.add_argument("--out",type=Path,default=ROOT/"docs/research/1989-carrier-bench.tsv")
    args=ap.parse_args()
    build()
    rows=[]
    for cand,op,width in cases(args.smoke):
        # correctness/support probe without valgrind
        _,meta=invoke(cand,op,width,1,"full",False)
        if meta.get("supported")!="1":
            rows.append(dict(case_id=f"{cand}-{op}-{width}",candidate=cand,operation=op,width=width,
                             supported=0,i_refs="",allocations="",allocated_bytes="",
                             object_bytes=meta.get("object_bytes",""),payload_bytes=meta.get("payload_bytes",""),
                             reps=args.reps,iters=args.iters))
            continue
        pre=[]; full=[]; last={}
        for _ in range(args.reps):
            ir0,_=invoke(cand,op,width,args.iters,"prepare",True)
            ir1,last=invoke(cand,op,width,args.iters,"full",True)
            pre.append(ir0);full.append(ir1)
        med0=int(statistics.median(pre));med1=int(statistics.median(full));delta=med1-med0
        rows.append(dict(case_id=f"{cand}-{op}-{width}",candidate=cand,operation=op,width=width,
                         supported=1,i_refs=delta,i_refs_per_op=f"{delta/args.iters:.3f}",
                         allocations=last.get("allocations",""),allocated_bytes=last.get("allocated_bytes",""),
                         allocations_per_op=f"{int(last.get('allocations','0'))/args.iters:.6f}",
                         allocated_bytes_per_op=f"{int(last.get('allocated_bytes','0'))/args.iters:.3f}",
                         object_bytes=last.get("object_bytes",""),payload_bytes=last.get("payload_bytes",""),
                         spilled=last.get("spilled","0"),prepare_i_refs=med0,full_i_refs=med1,
                         reps=args.reps,iters=args.iters))
        print(rows[-1])
    fields=["case_id","candidate","operation","width","supported","i_refs","i_refs_per_op",
            "allocations","allocated_bytes","allocations_per_op","allocated_bytes_per_op",
            "object_bytes","payload_bytes","spilled","prepare_i_refs","full_i_refs","reps","iters"]
    args.out.parent.mkdir(parents=True,exist_ok=True)
    with args.out.open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fields,delimiter="\t",extrasaction="ignore");w.writeheader();w.writerows(rows)
    print(f"wrote {args.out}")

if __name__=="__main__": main()
