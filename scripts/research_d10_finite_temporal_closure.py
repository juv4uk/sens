#!/usr/bin/env python3
"""#5000 D10 research HOLD: finite integer simple temporal network.

No SENS executable, opcode, grammar, decoder, ratification, or domain bit code.
Edge (i,j,w) means event_time[j] - event_time[i] <= w. Domain is
unbounded mathematical integers, not fixed-length machine-clock registers.

A consistent network yields ALL tight upper difference bounds, with None for
unbounded pairwise differences. Inconsistent yields a verifiable negative-cycle
certificate, not a plausible-looking distance matrix.

Dual algorithms: Floyd's all-pairs min-plus and Bellman's independent relaxation.
External independent real Z3 SAT + Optimize provided by test suite, not this law.
"""
from __future__ import annotations

from itertools import permutations
import json
from pathlib import Path
from typing import Any

MIN_N, MAX_N = 1, 5
MAX_WEIGHT = 1000
SCHEMA = "sens-d10-research-finite-simple-temporal-closure/v1"


class TemporalError(ValueError):
    pass


def _validated(n: int, constraints: list[tuple[int, int, int]]) -> dict[tuple[int,int], int]:
    if type(n) is not int or not MIN_N <= n <= MAX_N:
        raise TemporalError("n must be an integer from 1 to 5")
    if not isinstance(constraints, list) or len(constraints) > 80:
        raise TemporalError("constraints must be a bounded list of directed edges")
    edges: dict[tuple[int,int], int] = {}
    for row in constraints:
        if not isinstance(row, (tuple, list)) or len(row) != 3:
            raise TemporalError("each edge must be (i,j,w)")
        a,b,w = row
        if (type(a) is not int or type(b) is not int or type(w) is not int
            or a < 0 or b < 0 or a >= n or b >= n or abs(w) > MAX_WEIGHT):
            raise TemporalError("indices and integer weights outside finite research contract")
        edge = (a,b)
        edges[edge] = min(edges.get(edge,w),w)
    return edges


def negative_cycle_certificate(n: int, edges: dict[tuple[int,int],int]) -> dict[str,Any] | None:
    """Minimum number of edges, then lexicographically first vertex cycle.

    Exhaustive simple cycles only; no exponential search on user unbounded n.
    Each edge weight is the strongest existing parallel constraint.
    """
    for k in range(1,n+1):
        matches: list[tuple[int,...]] = []
        for vertices in permutations(range(n),k):
            if vertices[0] != min(vertices):  # canonical cyclic rotation
                continue
            cycle = (*vertices, vertices[0])
            if all((cycle[i],cycle[i+1]) in edges for i in range(k)):
                total = sum(edges[cycle[i],cycle[i+1]] for i in range(k))
                if total < 0:
                    matches.append(vertices)
        if matches:
            selected = min(matches)
            closed = (*selected, selected[0])
            weights = [edges[closed[i],closed[i+1]] for i in range(k)]
            return {"vertices":list(closed),"weights":weights,
                    "strict_negative_sum":sum(weights)}
    return None


def floyd_closure(n: int, constraints: list[tuple[int,int,int]]) -> dict[str,Any]:
    """Exact tight all-pairs upper differences or certified inconsistency."""
    edges = _validated(n,constraints)
    d: list[list[int | None]] = [[0 if a == b else None for b in range(n)]
                                 for a in range(n)]
    for (a,b),w in edges.items():
        if d[a][b] is None or w < d[a][b]:
            d[a][b] = w
    for k in range(n):
        for i in range(n):
            if d[i][k] is None:
                continue
            for j in range(n):
                if d[k][j] is None:
                    continue
                proposed = d[i][k] + d[k][j]
                if d[i][j] is None or proposed < d[i][j]:
                    d[i][j] = proposed
    if any(d[k][k] is not None and d[k][k] < 0 for k in range(n)):
        cycle = negative_cycle_certificate(n,edges)
        if cycle is None:
            raise TemporalError("negative diagonal without simple-cycle certificate")
        return {"status":"INCONSISTENT_NEGATIVE_CYCLE",
                "tight_upper_bounds":None, "negative_cycle":cycle}
    return {"status":"CONSISTENT", "tight_upper_bounds":d, "negative_cycle":None}


def bellman_reference(n: int, constraints: list[tuple[int,int,int]]) -> dict[str,Any]:
    """Different algorithm: per-source repeated edge relaxation, no Floyd pivot."""
    edges = _validated(n,constraints)
    arc = sorted((a,b,w) for (a,b),w in edges.items())
    results: list[list[int | None]]=[]
    for source in range(n):
        dist: list[int | None] = [0 if v==source else None for v in range(n)]
        for _ in range(n-1):
            prev = dist[:]
            nxt = prev[:]
            for i,j,w in arc:
                if prev[i] is None:
                    continue
                x = prev[i]+w
                if nxt[j] is None or x < nxt[j]:
                    nxt[j] = x
            dist=nxt
        for i,j,w in arc:
            if dist[i] is not None and (dist[j] is None or dist[i]+w < dist[j]):
                cycle=negative_cycle_certificate(n,edges)
                if cycle is None:
                    raise TemporalError("Bellman contradiction without cycle")
                return {"status":"INCONSISTENT_NEGATIVE_CYCLE",
                        "tight_upper_bounds":None, "negative_cycle":cycle}
        results.append(dist)
    return {"status":"CONSISTENT","tight_upper_bounds":results,"negative_cycle":None}


def check_certificate(n:int,constraints:list[tuple[int,int,int]],result:dict[str,Any])->bool:
    edges=_validated(n,constraints)
    if result.get("status")=="INCONSISTENT_NEGATIVE_CYCLE":
        c=result.get("negative_cycle")
        if not isinstance(c,dict):
            return False
        vs=c.get("vertices")
        ws=c.get("weights")
        if (not isinstance(vs,list) or not isinstance(ws,list)
                or len(vs)<2 or len(vs)!=len(ws)+1 or vs[0]!=vs[-1]
                or len(set(vs[:-1]))!=len(vs)-1):
            return False
        try:
            weight=[edges[vs[i],vs[i+1]] for i in range(len(ws))]
        except (KeyError,TypeError):
            return False
        return (weight==ws and sum(ws)<0 and c.get("strict_negative_sum")==sum(ws)
                and result.get("tight_upper_bounds") is None
                and c==negative_cycle_certificate(n,edges))
    if result.get("status")!="CONSISTENT" or result.get("negative_cycle") is not None:
        return False
    d=result.get("tight_upper_bounds")
    if not isinstance(d,list) or len(d)!=n or any(not isinstance(row,list) or len(row)!=n for row in d):
        return False
    # A legitimate all-pairs candidate must satisfy all single-edge upper bounds,
    # triangle closure and exact diagonal. Minimality is DIFFERENT and enforced
    # by independent Bellman and external actual Z3 Optimize oracle.
    if any(d[i][i]!=0 for i in range(n)):
        return False
    for (i,j),w in edges.items():
        if d[i][j] is None or type(d[i][j]) is not int or d[i][j]>w:
            return False
    for i in range(n):
        for k in range(n):
            for j in range(n):
                if d[i][k] is not None and d[k][j] is not None:
                    if d[i][j] is None or d[i][j]>d[i][k]+d[k][j]:
                        return False
    return True


def run_survey()->dict[str,Any]:
    from random import Random
    rnd=Random(1971)
    cases=0
    inconsistent=0
    unbounded=0
    for n in range(1,5):
        for sample in range(96):
            plan=[rnd.randint(-5,5) for _ in range(n)]
            e=[]
            for i in range(n):
                for j in range(n):
                    if rnd.random()<0.56:
                        slack=rnd.randint(0,4)
                        e.append((i,j,plan[j]-plan[i]+slack))
                        if rnd.random()<0.25:
                            e.append((i,j,plan[j]-plan[i]+slack+4))
            if sample%3==1:
                e.extend([(0,0,-1)])
            elif sample%3==2 and n>=2:
                e.extend([(0,1,-3),(1,0,2)])  # strict negative 2-cycle
            left=floyd_closure(n,e)
            right=bellman_reference(n,e)
            if left!=right or not check_certificate(n,e,left):
                raise TemporalError(f"independent bounded graph oracle mismatch: n={n}, sample={sample}")
            cases+=1
            inconsistent+=(left["status"]=="INCONSISTENT_NEGATIVE_CYCLE")
            if left["status"]=="CONSISTENT":
                unbounded+=sum(v is None for row in left["tight_upper_bounds"] for v in row)
    return {"schema":SCHEMA,"status":"RESEARCH_HOLD_NOT_SELECTED",
            "cases":cases,"inconsistent":inconsistent,
            "unbounded_pairs":unbounded,"d1_d9_changed":False,
            "d10_selected_delta":0,"ratified_delta":0,
            "original_sens_migrations":0}


if __name__=="__main__":
    import argparse
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--report",type=Path)
    args=p.parse_args()
    report=run_survey()
    print(json.dumps(report,ensure_ascii=False,sort_keys=True))
    if args.report:
        args.report.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
