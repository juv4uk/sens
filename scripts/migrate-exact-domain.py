#!/usr/bin/env python3
"""Міграція Lisp-голів тільки за ратифікованими D3/D4 українськими поверхнями.

Старі восьмибітні слоти не визначають поточну identity/викличність.
T5M — лише транспорт уже сформованих слів.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
from pathlib import Path
import re
import operator

ROOT = Path(__file__).resolve().parents[1]
WORD8 = re.compile(r"[01]{8}\Z")
FIELD = re.compile(r'\((ук|укр|san|en|LISP|sym)\s+("(?:\\.|[^"\\])*"|\(\)|[^()\s]+)\)')
SAFE_OLD = {
    ("D3", "QUOTE"), ("D3", "ATOM"), ("D3", "EQ"),
    ("D3", "CAR"), ("D3", "CDR"), ("D3", "CONS"),
    ("D4", "LAMBDA"), ("D4", "DEFINE"),
}


@dataclass(frozen=True)
class Identity:
    domain: str
    bits: str
    label: str
    українська: str


@dataclass(frozen=True)
class Edit:
    start: int
    end: int
    source: str
    identity: Identity


def load_authority(root: Path = ROOT):
    foundation = json.loads(
        (root / "knowledge/d1-d9-foundation.json").read_text(encoding="utf-8")
    )
    if foundation.get("status") != "owner-ratified":
        raise ValueError("missing exact-domain owner authority")

    surfaces = {}
    ambiguous = set()
    for domain in ("D3", "D4"):
        table = (root / "lib/domains" / (domain.lower() + ".lisp")).read_text(encoding="utf-8")
        residents = foundation["domains"][domain]["residents"]
        for line in table.splitlines():
            row = re.match(r"^\s*\(([01]{3,4})\s+(.*)$", line)
            if not row:
                continue
            bits, tail = row.groups()
            if len(bits) != int(domain[1:]):
                continue
            label = residents.get(bits)
            if label is None:
                raise ValueError(f"owner table drift at {domain}:{bits}")
            fields = dict(FIELD.findall(tail))
            raw_ukr = fields.get("укр", "()")
            if raw_ukr == "()":
                if label != "EMPTY":
                    raise ValueError(f"missing Ukrainian projection at {domain}:{bits}")
                continue
            українська = json.loads(raw_ukr) if raw_ukr.startswith('"') else raw_ukr
            if not isinstance(українська, str) or not українська:
                raise ValueError(f"invalid Ukrainian projection at {domain}:{bits}")
            identity = Identity(domain, bits, label, українська)
            for _, raw in FIELD.findall(tail):
                if raw == "()":
                    continue
                surface = json.loads(raw) if raw.startswith('"') else raw
                key = surface.casefold()
                if key in surfaces and surfaces[key] != identity:
                    ambiguous.add(key)
                else:
                    surfaces[key] = identity
    for key in ambiguous:
        del surfaces[key]
    if not all(x in surfaces for x in ("car", "quote", "перше", "атом?")):
        raise ValueError("missing owner-ratified D3 surfaces")

    return surfaces


def reject_shadowed_surfaces(source, surfaces):
    """Owner policy: no SHADOWED_SURFACE_BLOCK / BINDING_FORM_BLOCK.

    Ukrainian surface spellings as DEFINE names, LAMBDA parameters, or LET
    variables are intentional (opt-in aliases and natural ukr binding names).
    T5M / SENS handles scope. Do not reintroduce artificial blockers.
    """
    return
