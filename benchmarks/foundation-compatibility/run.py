#!/usr/bin/env python3
"""#2113 research-only foundation compatibility benchmark."""

from __future__ import annotations

import argparse
import csv
import json
import platform
import re
import shutil
import statistics
import subprocess
import tempfile
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

SIZES = (8, 32, 128, 512)
SHAPES = ("chain", "cycle", "fanout", "fanin", "mixed", "one_state")
IREF_SIZES = (32, 128)
IREF_SHAPES = ("chain", "fanout", "mixed", "one_state")
STRATEGIES = ("explicit", "compat", "hybrid")


class DSU:
    def __init__(self, n: int):
        self.parent = list(range(n))
        self.rank = [0] * n

    def find(self, x: int) -> int:
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def union(self, a: int, b: int) -> bool:
        a, b = self.find(a), self.find(b)
        if a == b:
            return False
        if self.rank[a] < self.rank[b]:
            a, b = b, a
        self.parent[b] = a
        if self.rank[a] == self.rank[b]:
            self.rank[a] += 1
        return True


def make_system(shape: str, n: int) -> list[tuple[int, int]]:
    if shape == "chain":
        return [(i, i + 1) for i in range(n)]
    if shape == "cycle":
        return [(i, (i + 1) % n) for i in range(n)]
    if shape == "fanout":
        return [(0, i + 1) for i in range(n)]
    if shape == "fanin":
        return [(i + 1, 0) for i in range(n)]
    if shape == "one_state":
        return [(0, 0) for _ in range(n)]
    if shape == "mixed":
        chain_n = max(2, n // 2)
        remaining = n - chain_n
        fanout_n = remaining // 2
        fanin_n = remaining - fanout_n
        edges = [(i, i + 1) for i in range(chain_n)]
        base = chain_n + 1
        edges.extend((base, base + 1 + i) for i in range(fanout_n))
        base2 = base + 1 + fanout_n
        edges.extend((base2 + 1 + i, base2) for i in range(fanin_n))
        assert len(edges) == n
        return edges
    raise ValueError(shape)


@dataclass
class LogicalRow:
    shape: str
    n: int
    transformations: int
    boundary_occurrences: int
    true_equal_pairs: int
    distinct_pairs: int
    compatibility_facts: int
    compat_recovered_pairs: int
    compat_recall: float
    residual_facts: int
    hybrid_recovered_pairs: int
    hybrid_recall: float
    false_positives_compat: int
    false_positives_hybrid: int
    explicit_label_fields: int
    explicit_est_bytes: int
    compat_est_bytes: int
    hybrid_est_bytes: int
    composition_closed_est_bytes: int
    derived_equal_pairs_compat: int
    derived_equal_pairs_hybrid: int


def logical_row(shape: str, n: int) -> LogicalRow:
    edges = make_system(shape, n)
    m = len(edges)
    states = [0] * (2 * m)
    for i, (src, dst) in enumerate(edges):
        states[2 * i] = src
        states[2 * i + 1] = dst

    true_pairs = []
    distinct_pairs = 0
    for a in range(2 * m):
        for b in range(a + 1, 2 * m):
            if states[a] == states[b]:
                true_pairs.append((a, b))
            else:
                distinct_pairs += 1

    comp = []
    dsu = DSU(2 * m)
    for i, (_, dst) in enumerate(edges):
        for j, (src, _) in enumerate(edges):
            if dst == src:
                a, b = 2 * i + 1, 2 * j
                comp.append((a, b))
                dsu.union(a, b)

    compat_recovered = sum(dsu.find(a) == dsu.find(b) for a, b in true_pairs)
    false_compat = sum(
        dsu.find(a) == dsu.find(b)
        for a in range(2 * m)
        for b in range(a + 1, 2 * m)
        if states[a] != states[b]
    )

    residual = []
    by_state = defaultdict(list)
    for idx, state in enumerate(states):
        by_state[state].append(idx)
    for members in by_state.values():
        component_reps = {}
        for x in members:
            component_reps.setdefault(dsu.find(x), x)
        reps = list(component_reps.values())
        if reps:
            anchor = reps[0]
            for other in reps[1:]:
                residual.append((anchor, other))
                dsu.union(anchor, other)

    hybrid_recovered = sum(dsu.find(a) == dsu.find(b) for a, b in true_pairs)
    false_hybrid = sum(
        dsu.find(a) == dsu.find(b)
        for a in range(2 * m)
        for b in range(a + 1, 2 * m)
        if states[a] != states[b]
    )

    true_count = len(true_pairs)
    compat_count = len(comp)
    residual_count = len(residual)
    return LogicalRow(
        shape=shape,
        n=n,
        transformations=m,
        boundary_occurrences=2 * m,
        true_equal_pairs=true_count,
        distinct_pairs=distinct_pairs,
        compatibility_facts=compat_count,
        compat_recovered_pairs=compat_recovered,
        compat_recall=(compat_recovered / true_count) if true_count else 1.0,
        residual_facts=residual_count,
        hybrid_recovered_pairs=hybrid_recovered,
        hybrid_recall=(hybrid_recovered / true_count) if true_count else 1.0,
        false_positives_compat=false_compat,
        false_positives_hybrid=false_hybrid,
        explicit_label_fields=2 * m,
        explicit_est_bytes=2 * m * 4,
        compat_est_bytes=compat_count * 2 * 4,
        hybrid_est_bytes=(compat_count + residual_count) * 2 * 4,
        composition_closed_est_bytes=compat_count * 3 * 4,
        derived_equal_pairs_compat=max(0, compat_recovered - compat_count),
        derived_equal_pairs_hybrid=max(
            0, hybrid_recovered - compat_count - residual_count
        ),
    )


def checked(cmd):
    return subprocess.run(cmd, text=True, capture_output=True, check=True)


def generate_c() -> str:
    return r"""
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct { uint32_t a, b; } Pair;
typedef struct { uint32_t *p; uint8_t *rank; } DSU;

static void dsu_init(DSU *d, size_t n) {
    d->p=(uint32_t*)malloc(n*sizeof(uint32_t));
    d->rank=(uint8_t*)calloc(n,1);
    if(!d->p || !d->rank) abort();
    for(size_t i=0;i<n;i++) d->p[i]=(uint32_t)i;
}
static void dsu_free(DSU *d) { free(d->p); free(d->rank); }
static uint32_t dsu_find(DSU *d, uint32_t x) {
    uint32_t r=x;
    while(d->p[r]!=r) r=d->p[r];
    while(d->p[x]!=x) {
        uint32_t nx=d->p[x];
        d->p[x]=r;
        x=nx;
    }
    return r;
}
static int dsu_union(DSU *d, uint32_t a, uint32_t b) {
    a=dsu_find(d,a);
    b=dsu_find(d,b);
    if(a==b) return 0;
    if(d->rank[a] < d->rank[b]) {
        uint32_t t=a; a=b; b=t;
    }
    d->p[b]=a;
    if(d->rank[a]==d->rank[b]) d->rank[a]++;
    return 1;
}

static void build_edges(
    const char *shape, uint32_t n, uint32_t *src, uint32_t *dst
) {
    if(strcmp(shape,"chain")==0) {
        for(uint32_t i=0;i<n;i++) { src[i]=i; dst[i]=i+1; }
    } else if(strcmp(shape,"cycle")==0) {
        for(uint32_t i=0;i<n;i++) { src[i]=i; dst[i]=(i+1)%n; }
    } else if(strcmp(shape,"fanout")==0) {
        for(uint32_t i=0;i<n;i++) { src[i]=0; dst[i]=i+1; }
    } else if(strcmp(shape,"fanin")==0) {
        for(uint32_t i=0;i<n;i++) { src[i]=i+1; dst[i]=0; }
    } else if(strcmp(shape,"one_state")==0) {
        for(uint32_t i=0;i<n;i++) { src[i]=0; dst[i]=0; }
    } else if(strcmp(shape,"mixed")==0) {
        uint32_t chain_n=n/2;
        if(chain_n<2) chain_n=2;
        uint32_t rem=n-chain_n, fo=rem/2, fi=rem-fo, k=0;
        for(uint32_t i=0;i<chain_n;i++,k++) {
            src[k]=i; dst[k]=i+1;
        }
        uint32_t base=chain_n+1;
        for(uint32_t i=0;i<fo;i++,k++) {
            src[k]=base; dst[k]=base+1+i;
        }
        uint32_t base2=base+1+fo;
        for(uint32_t i=0;i<fi;i++,k++) {
            src[k]=base2+1+i; dst[k]=base2;
        }
        if(k!=n) abort();
    } else {
        abort();
    }
}

static uint32_t boundary_state(
    const uint32_t *src, const uint32_t *dst, uint32_t b
) {
    uint32_t i=b>>1;
    return (b&1u) ? dst[i] : src[i];
}

int main(int argc, char **argv) {
    if(argc!=7) {
        fprintf(stderr,
            "usage: %s STRATEGY SHAPE N QUERY_N EXEC_N REPORT\n", argv[0]);
        return 2;
    }
    const char *strategy=argv[1], *shape=argv[2];
    uint32_t n=(uint32_t)strtoul(argv[3],NULL,10);
    size_t query_n=(size_t)strtoull(argv[4],NULL,10);
    size_t exec_n=(size_t)strtoull(argv[5],NULL,10);
    int report=atoi(argv[6]);
    if(n<2 || exec_n>query_n) return 3;

    uint32_t *src=(uint32_t*)malloc(n*sizeof(uint32_t));
    uint32_t *dst=(uint32_t*)malloc(n*sizeof(uint32_t));
    if(!src || !dst) abort();
    build_edges(shape,n,src,dst);

    size_t comp_cap=(size_t)n*(size_t)n;
    size_t equal_cap=(size_t)(2*n)*(2*n-1)/2 + 1;
    Pair *comp=(Pair*)malloc((comp_cap?comp_cap:1)*sizeof(Pair));
    Pair *equal=(Pair*)malloc(equal_cap*sizeof(Pair));
    Pair *residual=(Pair*)malloc((2u*(size_t)n+1)*sizeof(Pair));
    if(!comp || !equal || !residual) abort();
    size_t comp_n=0, equal_n=0, residual_n=0;

    for(uint32_t i=0;i<n;i++) {
        for(uint32_t j=0;j<n;j++) {
            if(dst[i]==src[j]) {
                comp[comp_n++]=(Pair){2*i+1,2*j};
            }
        }
    }
    for(uint32_t a=0;a<2*n;a++) {
        for(uint32_t b=a+1;b<2*n;b++) {
            if(boundary_state(src,dst,a)==boundary_state(src,dst,b)) {
                equal[equal_n++]=(Pair){a,b};
            }
        }
    }
    if(equal_n==0) return 4;

    DSU oracle;
    dsu_init(&oracle,2*n);
    for(size_t i=0;i<comp_n;i++) {
        dsu_union(&oracle,comp[i].a,comp[i].b);
    }
    for(size_t i=0;i<equal_n;i++) {
        uint32_t a=equal[i].a, b=equal[i].b;
        if(dsu_find(&oracle,a)!=dsu_find(&oracle,b)) {
            residual[residual_n++]=(Pair){a,b};
            dsu_union(&oracle,a,b);
        }
    }
    dsu_free(&oracle);

    DSU d={0};
    if(strcmp(strategy,"compat")==0 || strcmp(strategy,"hybrid")==0) {
        dsu_init(&d,2*n);
        for(size_t i=0;i<comp_n;i++) {
            dsu_union(&d,comp[i].a,comp[i].b);
        }
        if(strcmp(strategy,"hybrid")==0) {
            for(size_t i=0;i<residual_n;i++) {
                dsu_union(&d,residual[i].a,residual[i].b);
            }
        }
    }

    volatile uint64_t sink=0;
    for(size_t q=0;q<exec_n;q++) {
        Pair p=equal[q % equal_n];
        uint32_t ans=0;
        if(strcmp(strategy,"base")==0) {
            ans=(p.a ^ p.b) & 1u;
        } else if(strcmp(strategy,"explicit")==0) {
            ans=boundary_state(src,dst,p.a)==boundary_state(src,dst,p.b);
        } else if(
            strcmp(strategy,"compat")==0 || strcmp(strategy,"hybrid")==0
        ) {
            ans=dsu_find(&d,p.a)==dsu_find(&d,p.b);
        } else {
            return 5;
        }
        sink += ans + (uint32_t)(q&1u);
    }

    if(report) {
        fprintf(stderr,
            "comp=%zu residual=%zu equal=%zu sink=%llu\n",
            comp_n, residual_n, equal_n, (unsigned long long)sink);
    }
    if(d.p) dsu_free(&d);
    free(residual);
    free(equal);
    free(comp);
    free(dst);
    free(src);
    return sink==0x1234567812345678ull ? 9 : 0;
}
"""


def parse_irefs(stderr: str) -> int:
    match = re.search(r"I\s+refs:\s*([\d,]+)", stderr)
    if not match:
        raise RuntimeError(stderr)
    return int(match.group(1).replace(",", ""))


def measure(
    vg: str,
    binary: Path,
    strategy: str,
    shape: str,
    n: int,
    query_n: int,
    exec_n: int,
) -> int:
    p = subprocess.run(
        [
            vg,
            "--tool=cachegrind",
            "--cache-sim=no",
            "--branch-sim=no",
            "--cachegrind-out-file=/dev/null",
            str(binary),
            strategy,
            shape,
            str(n),
            str(query_n),
            str(exec_n),
            "0",
        ],
        text=True,
        capture_output=True,
        check=True,
    )
    return parse_irefs(p.stderr)


def version(cmd: list[str]) -> str:
    try:
        p = checked(cmd)
        return (p.stdout or p.stderr).splitlines()[0].strip()
    except Exception:
        return "unknown"


def write_logical(out: Path) -> list[LogicalRow]:
    rows = [logical_row(shape, n) for shape in SHAPES for n in SIZES]
    with (out / "logical.tsv").open("w", newline="") as fh:
        fieldnames = list(rows[0].__dict__.keys())
        w = csv.DictWriter(fh, fieldnames=fieldnames, delimiter="\t")
        w.writeheader()
        for row in rows:
            data = row.__dict__.copy()
            data["compat_recall"] = f"{row.compat_recall:.6f}"
            data["hybrid_recall"] = f"{row.hybrid_recall:.6f}"
            w.writerow(data)
    return rows


def write_irefs(out: Path, calls: int, reps: int) -> None:
    gcc, vg = shutil.which("gcc"), shutil.which("valgrind")
    if not gcc or not vg:
        raise SystemExit(
            "gcc and valgrind are required unless --logical-only is used"
        )

    with tempfile.TemporaryDirectory(prefix="sens2113-") as temp:
        td = Path(temp)
        src, binary = td / "bench.c", td / "bench"
        src.write_text(generate_c())
        checked(
            [
                gcc,
                "-O2",
                "-std=gnu11",
                "-fno-omit-frame-pointer",
                "-o",
                str(binary),
                str(src),
            ]
        )

        rows = []
        for shape in IREF_SHAPES:
            for n in IREF_SIZES:
                base_setup_samples = [
                    measure(vg, binary, "base", shape, n, calls, 0)
                    for _ in range(reps)
                ]
                base_full_samples = [
                    measure(vg, binary, "base", shape, n, calls, calls)
                    for _ in range(reps)
                ]
                base_setup = statistics.median(base_setup_samples)
                base_exec = statistics.median(base_full_samples) - base_setup

                logical = logical_row(shape, n)
                for strategy in STRATEGIES:
                    setup_samples = [
                        measure(vg, binary, strategy, shape, n, calls, 0)
                        for _ in range(reps)
                    ]
                    full_samples = [
                        measure(vg, binary, strategy, shape, n, calls, calls)
                        for _ in range(reps)
                    ]
                    setup = statistics.median(setup_samples)
                    full = statistics.median(full_samples)
                    net_per_query = (full - setup - base_exec) / calls
                    if strategy == "explicit":
                        stored = logical.explicit_label_fields
                    elif strategy == "compat":
                        stored = logical.compatibility_facts
                    else:
                        stored = (
                            logical.compatibility_facts + logical.residual_facts
                        )
                    rows.append(
                        {
                            "shape": shape,
                            "n": n,
                            "candidate": strategy,
                            "net_i_refs_per_true_equality_query": (
                                f"{net_per_query:.3f}"
                            ),
                            "setup_i_refs_over_base": int(setup - base_setup),
                            "true_equal_pairs": logical.true_equal_pairs,
                            "compat_recall": f"{logical.compat_recall:.6f}",
                            "residual_facts": logical.residual_facts,
                            "stored_fact_proxy": stored,
                        }
                    )

        with (out / "irefs.tsv").open("w", newline="") as fh:
            w = csv.DictWriter(
                fh, fieldnames=list(rows[0].keys()), delimiter="\t"
            )
            w.writeheader()
            w.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--out-dir",
        default="benchmarks/foundation-compatibility/results/current",
    )
    parser.add_argument("--calls", type=int, default=50000)
    parser.add_argument("--reps", type=int, default=3)
    parser.add_argument("--logical-only", action="store_true")
    args = parser.parse_args()

    repo = Path(__file__).resolve().parents[2]
    out = (repo / args.out_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)

    logical_rows = write_logical(out)
    if not args.logical_only:
        write_irefs(out, args.calls, args.reps)

    provenance = {
        "git_sha": version(["git", "-C", str(repo), "rev-parse", "HEAD"]),
        "cpu": platform.processor()
        or version(
            [
                "sh",
                "-c",
                "grep -m1 'model name' /proc/cpuinfo | cut -d: -f2-",
            ]
        ),
        "gcc": version([shutil.which("gcc") or "gcc", "--version"]),
        "valgrind": version(
            [shutil.which("valgrind") or "valgrind", "--version"]
        ),
        "kernel": platform.release(),
        "calls": args.calls,
        "reps": args.reps,
        "logical_shapes": SHAPES,
        "logical_sizes": SIZES,
        "iref_shapes": IREF_SHAPES,
        "iref_sizes": IREF_SIZES,
        "note": (
            "research-only; absence of a compatibility path is UNKNOWN, "
            "never semantic inequality"
        ),
    }
    (out / "provenance.json").write_text(
        json.dumps(provenance, indent=2) + "\n"
    )

    print(
        "shape\tn\tcompat_recall\tresidual_facts\t"
        "compat_facts\texplicit_labels"
    )
    for row in logical_rows:
        print(
            f"{row.shape}\t{row.n}\t{row.compat_recall:.6f}\t"
            f"{row.residual_facts}\t{row.compatibility_facts}\t"
            f"{row.explicit_label_fields}"
        )
    if not args.logical_only:
        print("\nI-ref matrix written to", out / "irefs.tsv")


if __name__ == "__main__":
    main()
