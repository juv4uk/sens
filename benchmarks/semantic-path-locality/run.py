#!/usr/bin/env python3
"""#2009 research-only semantic-path locality benchmark."""

from __future__ import annotations

import argparse
import csv
import json
import os
import platform
import re
import shutil
import statistics
import subprocess
import tempfile
from pathlib import Path

DEPTHS = (4, 8, 12, 16)
LOCALITIES = ("hot1", "hot16", "mix80", "uniform", "adversarial")
STRATEGIES = ("bitwalk", "flat", "cache")


def checked(cmd, *, env=None):
    return subprocess.run(cmd, text=True, capture_output=True, check=True, env=env)


def generate_c() -> str:
    return r'''
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct { uint32_t key; uint32_t value; } CacheEntry;

static uint32_t xorshift32(uint32_t *state) {
    uint32_t x=*state;
    x ^= x << 13;
    x ^= x >> 17;
    x ^= x << 5;
    *state=x;
    return x;
}

__attribute__((noinline))
static uint32_t bitwalk(uint32_t path, unsigned depth) {
    uint32_t node=1u;
    for (unsigned i=0;i<depth;i++) {
        unsigned shift=depth-1u-i;
        uint32_t bit=(path >> shift) & 1u;
        node=(node << 1) | bit;
    }
    return node;
}

static void fill_workload(uint32_t *out, size_t n, unsigned depth, const char *kind) {
    const uint32_t mask=(depth == 32) ? 0xffffffffu : ((1u << depth) - 1u);
    uint32_t state=0x9e3779b9u ^ depth;
    if (strcmp(kind,"hot1")==0) {
        uint32_t p=0x5a5au & mask;
        for(size_t i=0;i<n;i++) out[i]=p;
    } else if (strcmp(kind,"hot16")==0) {
        uint32_t hot[16];
        for(unsigned j=0;j<16;j++) hot[j]=(j*40503u + 97u) & mask;
        for(size_t i=0;i<n;i++) out[i]=hot[i & 15u];
    } else if (strcmp(kind,"mix80")==0) {
        uint32_t hot[8];
        for(unsigned j=0;j<8;j++) hot[j]=(j*7919u + 17u) & mask;
        for(size_t i=0;i<n;i++) {
            if ((i % 5u) != 0u) out[i]=hot[i & 7u];
            else out[i]=xorshift32(&state) & mask;
        }
    } else if (strcmp(kind,"uniform")==0) {
        for(size_t i=0;i<n;i++) out[i]=xorshift32(&state) & mask;
    } else if (strcmp(kind,"adversarial")==0) {
        const uint32_t slot=37u & mask;
        if (depth <= 10) {
            for(size_t i=0;i<n;i++) out[i]=slot;
        } else {
            uint32_t variants=1u << (depth-10u);
            for(size_t i=0;i<n;i++) {
                uint32_t high=(uint32_t)(i % variants);
                out[i]=((high << 10) | slot) & mask;
            }
        }
    } else {
        abort();
    }
}

static uint32_t *build_flat(unsigned depth) {
    size_t count=(size_t)1u << depth;
    uint32_t *table=(uint32_t*)malloc(count*sizeof(uint32_t));
    if(!table) abort();
    for(size_t p=0;p<count;p++) table[p]=bitwalk((uint32_t)p,depth);
    return table;
}

static void init_cache(CacheEntry *cache, size_t count) {
    for(size_t i=0;i<count;i++) {
        cache[i].key=UINT32_MAX;
        cache[i].value=0;
    }
}

int main(int argc, char **argv) {
    if(argc != 6) {
        fprintf(stderr,"usage: %s STRATEGY DEPTH LOCALITY WORKLOAD_N EXEC_N\n",argv[0]);
        return 2;
    }
    const char *strategy=argv[1];
    unsigned depth=(unsigned)strtoul(argv[2],NULL,10);
    const char *locality=argv[3];
    size_t workload_n=(size_t)strtoull(argv[4],NULL,10);
    size_t exec_n=(size_t)strtoull(argv[5],NULL,10);
    if(exec_n>workload_n || depth>16 || depth<1) return 3;

    uint32_t *work=(uint32_t*)malloc(workload_n*sizeof(uint32_t));
    if(!work) return 4;
    fill_workload(work,workload_n,depth,locality);

    uint32_t *flat=NULL;
    CacheEntry cache[1024];
    if(strcmp(strategy,"flat")==0) flat=build_flat(depth);
    if(strcmp(strategy,"cache")==0) init_cache(cache,1024);

    uint64_t hits=0, misses=0;
    volatile uint64_t sink=0;
    for(size_t i=0;i<exec_n;i++) {
        uint32_t p=work[i];
        uint32_t value;
        if(strcmp(strategy,"base")==0) {
            value=p;
        } else if(strcmp(strategy,"bitwalk")==0) {
            value=bitwalk(p,depth);
        } else if(strcmp(strategy,"flat")==0) {
            value=flat[p];
        } else if(strcmp(strategy,"cache")==0) {
            CacheEntry *e=&cache[p & 1023u];
            if(e->key==p) {
                hits++;
                value=e->value;
            } else {
                misses++;
                value=bitwalk(p,depth);
                e->key=p;
                e->value=value;
            }
        } else {
            return 5;
        }
        sink ^= value;
    }

    if(getenv("REPORT_STATS") && strcmp(strategy,"cache")==0)
        fprintf(stderr,"hits=%llu misses=%llu\n",
                (unsigned long long)hits,(unsigned long long)misses);

    free(flat);
    free(work);
    return sink==0x1234567812345678ull ? 9 : 0;
}
'''


def parse_irefs(stderr: str) -> int:
    m = re.search(r"I\s+refs:\s*([\d,]+)", stderr)
    if not m:
        raise RuntimeError(stderr)
    return int(m.group(1).replace(",", ""))


def measure(vg: str, binary: Path, strategy: str, depth: int, locality: str, n: int, exec_n: int) -> int:
    p = subprocess.run(
        [
            vg, "--tool=cachegrind", "--cache-sim=no", "--branch-sim=no",
            "--cachegrind-out-file=/dev/null",
            str(binary), strategy, str(depth), locality, str(n), str(exec_n)
        ],
        text=True, capture_output=True, check=True
    )
    return parse_irefs(p.stderr)


def cache_stats(binary: Path, depth: int, locality: str, n: int) -> tuple[int, int]:
    env = dict(os.environ)
    env["REPORT_STATS"] = "1"
    p = checked([str(binary), "cache", str(depth), locality, str(n), str(n)], env=env)
    m = re.search(r"hits=(\d+)\s+misses=(\d+)", p.stderr)
    if not m:
        raise RuntimeError(p.stderr)
    return int(m.group(1)), int(m.group(2))


def version(cmd):
    try:
        p = checked(cmd)
        return (p.stdout or p.stderr).splitlines()[0].strip()
    except Exception:
        return "unknown"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", default="benchmarks/semantic-path-locality/results/current")
    ap.add_argument("--calls", type=int, default=50000)
    ap.add_argument("--reps", type=int, default=3)
    args = ap.parse_args()

    gcc, vg = shutil.which("gcc"), shutil.which("valgrind")
    if not gcc or not vg:
        raise SystemExit("gcc and valgrind are required")

    repo = Path(__file__).resolve().parents[2]
    out = (repo / args.out_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="sens2009-") as td:
        td = Path(td)
        src, binary = td / "bench.c", td / "bench"
        src.write_text(generate_c())
        checked([gcc, "-O2", "-std=gnu11", "-fno-omit-frame-pointer", "-o", str(binary), str(src)])

        rows = []
        for depth in DEPTHS:
            flat_bytes = (1 << depth) * 4
            for locality in LOCALITIES:
                base_samples = [measure(vg, binary, "base", depth, locality, args.calls, args.calls)
                                for _ in range(args.reps)]
                base_setup_samples = [measure(vg, binary, "base", depth, locality, args.calls, 0)
                                      for _ in range(args.reps)]
                base_exec = statistics.median(base_samples) - statistics.median(base_setup_samples)

                hits, misses = cache_stats(binary, depth, locality, args.calls)
                for strategy in STRATEGIES:
                    setup_samples = [measure(vg, binary, strategy, depth, locality, args.calls, 0)
                                     for _ in range(args.reps)]
                    full_samples = [measure(vg, binary, strategy, depth, locality, args.calls, args.calls)
                                    for _ in range(args.reps)]
                    setup = statistics.median(setup_samples)
                    full = statistics.median(full_samples)
                    net_exec = (full - setup - base_exec) / args.calls
                    setup_over_base = setup - statistics.median(base_setup_samples)
                    rows.append({
                        "depth": depth,
                        "locality": locality,
                        "candidate": strategy,
                        "net_i_refs_per_call": f"{net_exec:.3f}",
                        "setup_i_refs_over_base": int(setup_over_base),
                        "cache_hits": hits if strategy == "cache" else "",
                        "cache_misses": misses if strategy == "cache" else "",
                        "cache_hit_rate": f"{hits/(hits+misses):.6f}" if strategy == "cache" else "",
                        "state_bytes": flat_bytes if strategy == "flat" else 8192 if strategy == "cache" else 0,
                        "semantic_steps": depth if strategy in ("bitwalk","cache") else 0
                    })

        with (out / "summary.tsv").open("w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()), delimiter="\t")
            w.writeheader()
            w.writerows(rows)

        provenance = {
            "git_sha": version(["git", "-C", str(repo), "rev-parse", "HEAD"]),
            "cpu": platform.processor() or version(["sh","-c","grep -m1 'model name' /proc/cpuinfo | cut -d: -f2-"]),
            "gcc": version([gcc, "--version"]),
            "valgrind": version([vg, "--version"]),
            "kernel": platform.release(),
            "calls": args.calls,
            "reps": args.reps,
            "cache_entries": 1024,
            "note": "research-only semantic-path locality mechanism; Cachegrind cache/branch simulation disabled"
        }
        (out / "provenance.json").write_text(json.dumps(provenance, indent=2) + "\n")
        print((out / "summary.tsv").read_text(), end="")


if __name__ == "__main__":
    main()
