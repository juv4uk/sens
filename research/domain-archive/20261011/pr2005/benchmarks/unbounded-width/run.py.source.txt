#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,hashlib,re,statistics,subprocess,tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
SRC=HERE/"width_scale.c"
BIN=HERE/"width_scale"
IRE=re.compile(r"I\s*refs:\s*([0-9,]+)")
KV=re.compile(r"([A-Za-z_]+)=([^\s]+)")
WIDTHS=(3,4,5,6,7,8,16,32,64,65,128,255,256,257,512,1024,2048,4096)
OPS=("eq","hash","bit","prefix","append","parent","clone")
SMOKE_WIDTHS=(64,65,128,255,256,257,1024,4096)
SMOKE_OPS=("eq","prefix","append")

def sha256(p:Path)->str:
    h=hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda:f.read(1<<20),b""):
            h.update(chunk)
    return h.hexdigest()

def build():
    subprocess.run(["gcc","-O2","-std=c11","-Wall","-Wextra","-Werror","-o",str(BIN),str(SRC)],check=True)

def run(cand,op,width,iters,mode,vg):
    cmd=[str(BIN),cand,op,str(width),str(iters),mode]
    if not vg:
        cp=subprocess.run(cmd,text=True,capture_output=True,check=True)
        return None,dict(KV.findall(cp.stdout))
    with tempfile.TemporaryDirectory() as td:
        log=Path(td)/"vg.log"
        subprocess.run(["valgrind","--tool=cachegrind","--cache-sim=no","--cachegrind-out-file=/dev/null",f"--log-file={log}",*cmd],
                       text=True,capture_output=True,check=True)
        m=IRE.search(log.read_text(errors="replace"))
        if not m:
            raise RuntimeError(log.read_text(errors="replace")[-2000:])
        cp=subprocess.run(cmd,text=True,capture_output=True,check=True)
        return int(m.group(1).replace(",","")),dict(KV.findall(cp.stdout))

def provenance():
    def out(cmd): return subprocess.run(cmd,text=True,capture_output=True,check=True).stdout.strip()
    cpu=""
    for line in Path("/proc/cpuinfo").read_text(errors="replace").splitlines():
        if line.lower().startswith("model name"):
            cpu=line.split(":",1)[1].strip();break
    ch=ROOT/"channels.scm"
    return {
        "git_sha":out(["git","rev-parse","HEAD"]),
        "binary_sha":sha256(BIN),
        "guix_channels_sha":sha256(ch) if ch.exists() else "",
        "cpu":cpu,
        "valgrind_version":out(["valgrind","--version"]),
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--smoke",action="store_true")
    ap.add_argument("--iters",type=int,default=1000)
    ap.add_argument("--reps",type=int,default=3)
    ap.add_argument("--out",type=Path,default=ROOT/"docs/research/2000-unbounded-width.tsv")
    a=ap.parse_args()
    build(); prov=provenance(); rows=[]
    widths=SMOKE_WIDTHS if a.smoke else WIDTHS
    ops=SMOKE_OPS if a.smoke else OPS
    for cand in ("heap","spill"):
        for width in widths:
            for op in ops:
                pre=[];full=[];meta={}
                for _ in range(a.reps):
                    x,_=run(cand,op,width,a.iters,"prepare",True)
                    y,meta=run(cand,op,width,a.iters,"full",True)
                    pre.append(x);full.append(y)
                p=int(statistics.median(pre));f=int(statistics.median(full));d=f-p
                row={
                    "case_id":f"{cand}-{op}-{width}","candidate":cand,"operation":op,"width":width,
                    "i_refs":d,"i_refs_per_op":f"{d/a.iters:.3f}",
                    "allocations":meta["allocations"],"allocated_bytes":meta["allocated_bytes"],
                    "allocations_per_op":f"{int(meta['allocations'])/a.iters:.6f}",
                    "allocated_bytes_per_op":f"{int(meta['allocated_bytes'])/a.iters:.3f}",
                    "object_bytes":meta["object_bytes"],"payload_bytes":meta["payload_bytes"],
                    "spilled":meta["spilled"],"prepare_i_refs":p,"full_i_refs":f,
                    "reps":a.reps,"iters":a.iters,**prov
                }
                rows.append(row);print(row)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    with a.out.open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]),delimiter="\t");w.writeheader();w.writerows(rows)
    print("wrote",a.out)

if __name__=="__main__":
    main()
