#!/usr/bin/env python3
"""#2027 selector self-description benchmark.

Compares flat metadata, compact proof certificate, typed graph traversal, and
hybrid graph-verified certificate use. Research-only; no semantic authority.
"""

from __future__ import annotations
import argparse,csv,hashlib,json,os,platform,re,statistics,subprocess,tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
SOURCE=Path(__file__).with_name("bench.rs")
MODES=("flat","certificate","graph","hybrid")
DEPTHS=(0,1,2,4,8,16)
PATTERNS=("repeated","random")
IREF_RE=re.compile(r"I\s+refs:\s+([0-9,]+)")

def sh(args,check=True):
    return subprocess.run(args,cwd=ROOT,text=True,capture_output=True,check=check)

def compile_bench(out):
    sh(["rustc","-O","-C","debuginfo=0",str(SOURCE),"-o",str(out)])

def parse_metrics(stdout):
    out={}
    checksum=None
    for line in stdout.splitlines():
        if line.startswith("METRIC\t"):
            _,k,v=line.split("\t",2); out[k]=int(v)
        elif line.startswith("CHECKSUM\t"):
            checksum=int(line.split("\t",1)[1])
    return checksum,out

def cachegrind(binary,mode,phase,depth,pattern,calls,cpu):
    cmd=["valgrind","--tool=cachegrind","--cache-sim=no","--branch-sim=no",
         "--cachegrind-out-file=/tmp/cg-2027.out",str(binary),mode,phase,str(depth),pattern,str(calls)]
    if cpu is not None: cmd=["taskset","-c",str(cpu)]+cmd
    env=os.environ.copy(); env["LC_ALL"]="C"
    p=subprocess.run(cmd,cwd=ROOT,text=True,capture_output=True,env=env)
    if p.returncode: raise RuntimeError(p.stderr)
    m=IREF_RE.search(p.stderr)
    if not m: raise RuntimeError("missing I refs\n"+p.stderr)
    return int(m.group(1).replace(",",""))

def envfacts(binary,sha):
    def o(args):
        try:return sh(args).stdout.strip()
        except Exception as e:return f"unknown ({e})"
    cpu="unknown"
    try:
        for line in Path("/proc/cpuinfo").read_text().splitlines():
            if line.startswith("model name"): cpu=line.split(":",1)[1].strip(); break
    except OSError: pass
    return {
      "source_sha":sha or o(["git","rev-parse","HEAD"]),
      "source_sha256":hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
      "binary_sha256":hashlib.sha256(binary.read_bytes()).hexdigest(),
      "rustc":o(["rustc","--version"]),"valgrind":o(["valgrind","--version"]),
      "python":platform.python_version(),"kernel":platform.release(),"cpu":cpu}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--depths",default=",".join(map(str,DEPTHS)))
    ap.add_argument("--patterns",default=",".join(PATTERNS))
    ap.add_argument("--calls",type=int,default=20000)
    ap.add_argument("--samples",type=int,default=3)
    ap.add_argument("--cpu",type=int,default=None)
    ap.add_argument("--out",required=True)
    ap.add_argument("--source-sha",default=None)
    ap.add_argument("--check-only",action="store_true")
    args=ap.parse_args()
    depths=tuple(map(int,args.depths.split(",")))
    patterns=tuple(args.patterns.split(","))
    out=Path(args.out); out.mkdir(parents=True,exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="sens-2027-") as td:
      binary=Path(td)/"bench"; compile_bench(binary)
      for d in depths:
        for ptn in patterns:
          p=sh([str(binary),"certificate","verify",str(d),ptn,str(min(args.calls,5000))])
          if "VERIFY\tPASS" not in p.stdout: raise RuntimeError(p.stdout+p.stderr)
      if args.check_only:
        print("self-description parity: PASS"); return

      (out/"environment.json").write_text(json.dumps(envfacts(binary,args.source_sha),indent=2)+"\n")
      rows=[]
      for d in depths:
        for ptn in patterns:
          for mode in MODES:
            proc=sh([str(binary),mode,"full",str(d),ptn,str(args.calls)])
            checksum,metrics=parse_metrics(proc.stdout)
            prep=[]; full=[]
            for _ in range(args.samples):
              prep.append(cachegrind(binary,mode,"prepare",d,ptn,args.calls,args.cpu))
              full.append(cachegrind(binary,mode,"full",d,ptn,args.calls,args.cpu))
            diffs=[f-p for p,f in zip(prep,full,strict=True)]
            row={
              "depth":d,"pattern":ptn,"mode":mode,"calls":args.calls,"samples":args.samples,
              "checksum":checksum,
              "prepare_i_refs":int(statistics.median(prep)),
              "full_i_refs":int(statistics.median(full)),
              "explain_i_refs":int(statistics.median(diffs)),
              "explain_i_refs_min":min(diffs),"explain_i_refs_max":max(diffs),
              "i_refs_per_explanation":f"{statistics.median(diffs)/args.calls:.3f}",
              "prepare_i_refs_raw":",".join(map(str,prep)),
              "full_i_refs_raw":",".join(map(str,full)),
              "explain_i_refs_raw":",".join(map(str,diffs)),
            }
            row.update(metrics); rows.append(row)
            print(d,ptn,mode,row["i_refs_per_explanation"])

      keys=[]
      for r in rows:
        for k in r:
          if k not in keys: keys.append(k)
      for r in rows:
        for k in keys:r.setdefault(k,0)
      with (out/"instructions.tsv").open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=keys,delimiter="\t",lineterminator="\n")
        w.writeheader();w.writerows(rows)

if __name__=="__main__":main()
