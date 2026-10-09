#!/usr/bin/env python3
"""#2190: Cachegrind evidence for exact-width dense packing."""

from __future__ import annotations
import argparse, csv, json, platform, re, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
IREF_RE = re.compile(r"I\s+refs:\s+([0-9,]+)")
WORKLOADS = ("d1","d2","d3","mixed","w4","w5","w6","w7","w8")
MODES = ("unpacked","pack","decode")

def run(cmd, *, check=True):
    return subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True, check=check)

def parse_result(text):
    line = next(x for x in text.splitlines() if x.startswith("PACK_BENCH\t"))
    out = {}
    for field in line.split("\t")[1:]:
        k,v = field.split("=",1)
        out[k]=v
    return out

def cachegrind(binary, mode, workload, n, reps):
    p = run([
        "valgrind","--tool=cachegrind","--cache-sim=no","--branch-sim=no",
        str(binary),mode,workload,str(n),str(reps)
    ])
    m = IREF_RE.search(p.stderr)
    if not m:
        raise RuntimeError(p.stderr)
    return int(m.group(1).replace(",","")), parse_result(p.stdout)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--binary",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    ap.add_argument("--sizes",default="64,1024")
    ap.add_argument("--reps",type=int,default=32)
    ap.add_argument("--workloads",default=",".join(WORKLOADS))
    args=ap.parse_args()

    sizes=[int(x) for x in args.sizes.split(",") if x]
    workloads=[x for x in args.workloads.split(",") if x]
    args.out.mkdir(parents=True,exist_ok=True)

    rows=[]
    for workload in workloads:
        for n in sizes:
            verify = run([str(args.binary),"verify",workload,str(n),"1"])
            baseline=parse_result(verify.stdout)
            semantic_bits=int(baseline["semantic_bits"])
            physical_bytes=int(baseline["physical_bytes"])
            unpacked_bytes=n
            utilization=semantic_bits/(physical_bytes*8) if physical_bytes else 1.0
            density=physical_bytes/unpacked_bytes if unpacked_bytes else 0.0

            base_irefs,base_result=cachegrind(args.binary,"base",workload,n,args.reps)
            for mode in MODES:
                irefs,result=cachegrind(args.binary,mode,workload,n,args.reps)
                ops=n*args.reps
                net_irefs=irefs-base_irefs
                if net_irefs < 0:
                    raise RuntimeError(
                        f"negative base-adjusted I refs: {workload=} {n=} {mode=}"
                    )
                rows.append({
                    "workload":workload,
                    "n":n,
                    "mode":mode,
                    "reps":args.reps,
                    "semantic_bits":semantic_bits,
                    "unpacked_bytes_proxy":unpacked_bytes,
                    "packed_bytes":physical_bytes,
                    "packed_to_unpacked_ratio":f"{density:.6f}",
                    "payload_utilization":f"{utilization:.6f}",
                    "base_i_refs":base_irefs,
                    "raw_i_refs":irefs,
                    "net_i_refs":net_irefs,
                    "net_i_refs_per_word":f"{net_irefs/ops:.3f}",
                    "checksum":result["checksum"],
                })
                print(
                    workload,n,mode,
                    f"raw={irefs}",
                    f"base={base_irefs}",
                    f"net={net_irefs}",
                    f"bytes={physical_bytes}",
                )

    keys=list(rows[0])
    with (args.out/"results.tsv").open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=keys,delimiter="\t",lineterminator="\n")
        w.writeheader(); w.writerows(rows)

    env={
        "python":platform.python_version(),
        "git_sha":run(["git","rev-parse","HEAD"]).stdout.strip(),
        "rustc":run(["rustc","--version"]).stdout.strip(),
        "valgrind":run(["valgrind","--version"]).stdout.strip(),
    }
    (args.out/"environment.json").write_text(json.dumps(env,indent=2)+"\n",encoding="utf-8")

if __name__=="__main__":
    main()
