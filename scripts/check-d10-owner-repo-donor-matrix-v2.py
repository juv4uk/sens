#!/usr/bin/env python3
import json
from pathlib import Path

root=Path(__file__).resolve().parents[1]
m=json.loads((root/"knowledge/d10-owner-repo-donor-matrix-v2.json").read_text(encoding="utf-8"))

assert m["schema"]=="d10-owner-repo-donor-matrix-v2/v1"
assert m["status"]=="AUDIT-COMPLETE"
assert m["authority"]=="#4049"
assert m["scope"]["repositories_accounted"]==87

rows=m["rows"]
assert len(rows)==87
assert len({r["repository"] for r in rows})==87
assert len({r["name"] for r in rows})==87
assert all(r["repository"]==f"juv4uk/{r['name']}" for r in rows)

expected={
    "CORE-LANGUAGE-DONOR":1,
    "CORE-HISTORICAL-DONOR":11,
    "BACKEND-OR-MECHANISM":11,
    "PACKAGE-OR-DOMAIN":33,
    "REFERENCE-OR-UPSTREAM":31,
    "REVIEW-REQUIRED":0,
}
assert m["class_counts"]==expected
actual={}
for r in rows:
    actual[r["primary_class"]]=actual.get(r["primary_class"],0)+1
assert actual==expected

by={r["name"]:r for r in rows}

# Semantic authority / historical donors.
assert by["sens"]["primary_class"]=="CORE-LANGUAGE-DONOR"
assert by["mccarthy-eval"]["primary_class"]=="CORE-HISTORICAL-DONOR"

# Known backend boundaries must never become direct Core donors.
for name in (
    "cml","fpga-lisp","wsm-my-lisp","my-lisp-cyberpunk","sens-futhark",
    "wsm-graalvm","wsm-cuda","wsm-lazarus","wsm-os","wsm-os-lisp","wsm-target-contract"
):
    assert by[name]["primary_class"]=="BACKEND-OR-MECHANISM"
    assert by[name]["d10_action"]=="REVIEW-SEAM-ONLY"

# Domain/tooling repos with explicit authority boundaries.
for name in ("panca-vac","my-lisp-panini","my-idea","ecosystem","ecosystem-observer","spanda","tauricode","wsm","WSM-24","pravda"):
    assert by[name]["primary_class"]=="PACKAGE-OR-DOMAIN"

# Known forks/upstream/reference projects discovered during deep review.
for name in ("basalt","graph-heavy-basalt","knowledge-graph-basalt","hydra","maitreya8","TH","chebupelka","cl-nlp","cl-tursas"):
    assert by[name]["primary_class"]=="REFERENCE-OR-UPSTREAM"
    assert by[name]["d10_action"]=="REFERENCE-ONLY"

# Only explicitly unresolved repository after first-pass deep review.
review=[r["name"] for r in rows if r["primary_class"]=="REVIEW-REQUIRED"]
assert review==[]
assert by["vault-semantic-mcp"]["primary_class"]=="PACKAGE-OR-DOMAIN"
assert by["vault-semantic-mcp"]["d10_action"]=="NO-DIRECT-CORE-ADMISSION"
assert by["vault-semantic-mcp"]["deep_review_status"]=="COMPLETE"

# Core admission is deliberately narrow.
for r in rows:
    if r["d10_action"] in {"REVIEW-CURRENT-LANGUAGE-GAPS","REVIEW-FOR-MISSING-HISTORICAL-SEMANTICS"}:
        assert r["primary_class"] in {"CORE-LANGUAGE-DONOR","CORE-HISTORICAL-DONOR"}

assert "No donor repository contributes coordinates." in m["doctrine"]

print("D10-OWNER-REPO-DONOR-MATRIX-V2=PASS")
print("repos=87 core-authority=1 historical=11 backend=11 package=33 reference=31 review=0")
