#!/usr/bin/env python3
"""History-aware source-head resolver for SENS migration.

This module reconstructs the real source transitions recorded in git history:

  current exact-width head (already migrated)
  -> Pass 1: legacy SID8/Sens8 exact 8-bit head
  -> Pass 2: my-lisp / admitted human-symbol surface
  -> Pass 3: historical Lisp I / Lisp 1.5 UPPERCASE name

Resolution never derives a current coordinate from legacy bit shape.  A legacy
form may reach a current D3-D6 identity only through independently named role /
surface evidence and the owner-ratified current foundation.
"""
from __future__ import annotations

from dataclasses import dataclass
import ast
import json
from pathlib import Path
import re
from typing import Iterable

from domain_tables import read_domain_table

HISTORICAL_ROW_RE = re.compile(
    r"^\s*\(row\s+([01]{8})\s+([^\s()]+)\s+([^\s()]+)\s+"
    r"([^\s()]+)\s+([^\s()]+)\s+([^\s()]+)\s*\)",
    re.MULTILINE,
)

REGISTRY_FIELD_RE = re.compile(
    r'\((en|ук|укр|sa|sym)\s+("(?:\\.|[^"\\])*"|\(\)|[^()\s]+)\)'
)


@dataclass(frozen=True)
class HistoricalRow:
    sid8: str
    my_lisp: str
    historical: str
    source: str
    fit: str
    status: str


@dataclass(frozen=True)
class CurrentIdentity:
    domain: str
    width: int
    bits: str
    label: str


@dataclass(frozen=True)
class Resolution:
    kind: str
    pass_number: int
    token: str
    current: CurrentIdentity | None
    legacy_sid8: str | None = None
    my_lisp: str | None = None
    historical: str | None = None
    evidence: tuple[str, ...] = ()
    ambiguous: tuple[str, ...] = ()

    @property
    def resolved(self) -> bool:
        return self.current is not None and not self.ambiguous

    @property
    def legacy_unmapped(self) -> bool:
        return self.pass_number in (1, 2, 3) and self.current is None and not self.ambiguous


def _strip_semicolon_comments(text: str) -> str:
    return "\n".join(line.split(";", 1)[0] for line in text.splitlines())


def _norm_label(name: str) -> str:
    """Normalize a role-like spelling only for label matching, not source class."""
    value = name.strip()
    aliases = {
        "+": "PLUS",
        "-": "DIFFERENCE",
        "*": "TIMES",
        "/": "QUOTIENT",
        "<": "LESSP",
        ">": "GREATERP",
        "NIL": "EMPTY",
        "EMPTY-LIST": "EMPTY",
    }
    if value in aliases:
        return aliases[value]
    upper = value.upper()
    if upper.endswith("?"):
        upper = upper[:-1]
    # Historical Lisp commonly uses P suffix where my-lisp used ?.
    predicate_aliases = {
        "ATOM": "ATOM",
        "EQ": "EQ",
        "NULL": "NULL",
        "NUMBER": "NUMBERP",
        "INTEGER": "INTEGERP",
        "RATIONAL": "RATIONALP",
        "ZERO": "ZEROP",
        "EVEN": "EVENP",
        "ODD": "ODDP",
        "MEMBER": "MEMBER",
    }
    return predicate_aliases.get(upper, upper)


def load_historical_rows(path: Path) -> list[HistoricalRow]:
    text = _strip_semicolon_comments(path.read_text(encoding="utf-8"))
    rows = [HistoricalRow(*m.groups()) for m in HISTORICAL_ROW_RE.finditer(text)]
    if not rows:
        raise ValueError(f"{path}: no historical rows")
    return rows


def load_current_foundation(path: Path) -> tuple[
    dict[str, CurrentIdentity],
    dict[tuple[int, str], CurrentIdentity],
]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("status") != "owner-ratified":
        raise ValueError(f"{path}: foundation is not owner-ratified")

    by_label: dict[str, CurrentIdentity] = {}
    by_word: dict[tuple[int, str], CurrentIdentity] = {}
    for domain in ("D3", "D4", "D5", "D6"):
        desc = data["domains"][domain]
        width = int(desc["width"])
        for bits, label in desc["residents"].items():
            identity = CurrentIdentity(domain, width, bits, str(label))
            key = str(label).upper()
            if key in by_label and by_label[key] != identity:
                raise ValueError(f"duplicate current label: {key}")
            by_label[key] = identity
            by_word[(width, bits)] = identity
    return by_label, by_word


def load_domain_surfaces(
    paths: Iterable[Path],
    current_by_word: dict[tuple[int, str], CurrentIdentity],
) -> dict[str, set[CurrentIdentity]]:
    out: dict[str, set[CurrentIdentity]] = {}
    for path in paths:
        for row in read_domain_table(path):
            identity = current_by_word.get((row.width, row.bits))
            if identity is None:
                continue
            for spelling in (row.en, row.uk, row.ukr, row.san, row.lisp, row.sym):
                if spelling:
                    out.setdefault(spelling, set()).add(identity)
    return out


def load_registry(path: Path) -> tuple[
    dict[str, list[tuple[str, str]]],
    dict[str, set[str]],
]:
    """Return sid->[(namespace, spelling)] and exact spelling->sid set."""
    sid_fields: dict[str, list[tuple[str, str]]] = {}
    surface_sids: dict[str, set[str]] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        match = re.match(r"^\s*\(([01]{8})\s+(.*)\)\s*$", raw)
        if not match:
            continue
        sid = match.group(1)
        fields: list[tuple[str, str]] = []
        for namespace, raw_value in REGISTRY_FIELD_RE.findall(match.group(2)):
            value = ast.literal_eval(raw_value) if raw_value.startswith('"') else raw_value
            if not value or value == "()":
                continue
            fields.append((namespace, value))
            surface_sids.setdefault(value, set()).add(sid)
        if fields:
            sid_fields[sid] = fields
    return sid_fields, surface_sids


class SourceResolver:
    def __init__(
        self,
        historical_rows: list[HistoricalRow],
        current_by_label: dict[str, CurrentIdentity],
        current_by_word: dict[tuple[int, str], CurrentIdentity],
        domain_surfaces: dict[str, set[CurrentIdentity]],
        registry_sid_fields: dict[str, list[tuple[str, str]]],
        registry_surface_sids: dict[str, set[str]],
        *,
        prefer_current_surface: bool = False,
    ):
        self.current_by_label = current_by_label
        self.current_by_word = current_by_word
        self.domain_surfaces = domain_surfaces
        self.registry_sid_fields = registry_sid_fields
        self.registry_surface_sids = registry_surface_sids
        self.prefer_current_surface = prefer_current_surface

        self.hist_by_sid: dict[str, list[HistoricalRow]] = {}
        self.hist_by_my: dict[str, list[HistoricalRow]] = {}
        self.hist_by_upper: dict[str, list[HistoricalRow]] = {}
        for row in historical_rows:
            self.hist_by_sid.setdefault(row.sid8, []).append(row)
            self.hist_by_my.setdefault(row.my_lisp, []).append(row)
            upper = row.historical.upper()
            if any(ch.isalpha() for ch in upper):
                self.hist_by_upper.setdefault(upper, []).append(row)

        # Build exact source-spelling -> current identity evidence.  No case
        # folding: source-era classification depends on spelling.
        self.current_surface: dict[str, set[CurrentIdentity]] = {
            spelling: set(ids) for spelling, ids in domain_surfaces.items()
        }

        # Historical my-lisp spellings may name current roles even when the
        # current projection chose a different English surface (e.g. + -> PLUS).
        for row in historical_rows:
            for identity in self._current_candidates_from_names(
                [row.my_lisp, row.historical]
            ):
                self.current_surface.setdefault(row.my_lisp, set()).add(identity)

        # Legacy registry aliases inherit a current role only when that legacy
        # SID resolves uniquely through named evidence.
        for sid, fields in registry_sid_fields.items():
            candidates = self._current_candidates_for_sid_without_registry_aliases(sid)
            if len(candidates) != 1:
                continue
            identity = next(iter(candidates))
            for _namespace, spelling in fields:
                self.current_surface.setdefault(spelling, set()).add(identity)

    def _current_candidates_from_names(
        self, names: Iterable[str]
    ) -> set[CurrentIdentity]:
        out: set[CurrentIdentity] = set()
        for name in names:
            if not name or name == "()":
                continue
            direct = self.domain_surfaces.get(name)
            if direct:
                out.update(direct)
            label = self.current_by_label.get(_norm_label(name))
            if label is not None:
                out.add(label)
        return out

    def _current_candidates_for_sid_without_registry_aliases(
        self, sid: str
    ) -> set[CurrentIdentity]:
        names: list[str] = []
        for row in self.hist_by_sid.get(sid, []):
            names.extend([row.my_lisp, row.historical])
        for namespace, spelling in self.registry_sid_fields.get(sid, []):
            # English/symbolic names are strongest for role matching; other
            # languages still resolve through current domain surface tables.
            if namespace in {"en", "sym", "ук", "укр", "sa"}:
                names.append(spelling)
        return self._current_candidates_from_names(names)

    def current_candidates_for_sid(self, sid: str) -> set[CurrentIdentity]:
        return self._current_candidates_for_sid_without_registry_aliases(sid)

    @staticmethod
    def _choose(
        kind: str,
        pass_number: int,
        token: str,
        candidates: set[CurrentIdentity],
        *,
        legacy_sid8: str | None = None,
        rows: Iterable[HistoricalRow] = (),
        evidence: Iterable[str] = (),
    ) -> Resolution:
        ordered = sorted(candidates, key=lambda x: (x.width, x.bits, x.label))
        current = ordered[0] if len(ordered) == 1 else None
        row_list = list(rows)
        return Resolution(
            kind=kind,
            pass_number=pass_number,
            token=token,
            current=current,
            legacy_sid8=legacy_sid8,
            my_lisp="|".join(dict.fromkeys(r.my_lisp for r in row_list)) or None,
            historical="|".join(dict.fromkeys(r.historical for r in row_list)) or None,
            evidence=tuple(dict.fromkeys(evidence)),
            ambiguous=tuple(
                f"{x.domain}:{x.bits}:{x.label}" for x in ordered
            ) if len(ordered) > 1 else (),
        )

    def resolve_head(self, token: str) -> Resolution:
        # Already-current operation-domain source is not one of the historical
        # passes; preserve exact width and identity.
        if re.fullmatch(r"[01]{3,6}", token):
            identity = self.current_by_word.get((len(token), token))
            if identity is not None:
                return Resolution(
                    kind="current-exact",
                    pass_number=0,
                    token=token,
                    current=identity,
                    evidence=("owner-ratified exact-domain word",),
                )

        # PASS 1: legacy exact 8-bit SID8/Sens8.
        if re.fullmatch(r"[01]{8}", token):
            rows = self.hist_by_sid.get(token, [])
            candidates = self.current_candidates_for_sid(token)
            evidence = [f"legacy SID8/Sens8 {token}"]
            evidence += [f"historical:{r.historical}" for r in rows]
            evidence += [
                f"registry:{ns}:{spelling}"
                for ns, spelling in self.registry_sid_fields.get(token, [])
            ]
            return self._choose(
                "sid8-sens8",
                1,
                token,
                candidates,
                legacy_sid8=token,
                rows=rows,
                evidence=evidence,
            )

        # PASS 2: exact my-lisp / admitted surface spelling.  This is
        # intentionally case-sensitive; uppercase historical names are held
        # for Pass 3.
        if token not in self.hist_by_upper:
            rows = self.hist_by_my.get(token, [])
            candidates = set(self.current_surface.get(token, set()))
            if rows or token in self.registry_surface_sids or candidates:
                evidence = ["my-lisp/admitted surface spelling"]
                evidence += [f"legacy-sid:{sid}" for sid in sorted(self.registry_surface_sids.get(token, ()))]
                return self._choose(
                    "my-lisp-surface",
                    2,
                    token,
                    candidates,
                    rows=rows,
                    evidence=evidence,
                )

        # A current admitted surface spelling wins over a historical uppercase
        # interpretation when the current surface evidence is unique. This matters
        # for current D8/D9 names such as ROUND that also occur in historical maps.
        current_surface = set(self.current_surface.get(token, set()))
        if self.prefer_current_surface and len(current_surface) == 1:
            return self._choose(
                "current-admitted-surface",
                2,
                token,
                current_surface,
                evidence=("current admitted domain surface",),
            )

        # PASS 3: historical Lisp I / Lisp 1.5 UPPERCASE surface.
        rows = self.hist_by_upper.get(token)
        if rows is not None:
            candidates: set[CurrentIdentity] = set()
            for row in rows:
                candidates.update(self._current_candidates_from_names(
                    [row.historical, row.my_lisp]
                ))
                candidates.update(self.current_candidates_for_sid(row.sid8))
            return self._choose(
                "lisp1-1.5-uppercase",
                3,
                token,
                candidates,
                rows=rows,
                evidence=(
                    "historical Lisp I/1.5 uppercase spelling",
                    *[f"legacy-sid:{r.sid8}" for r in rows],
                ),
            )

        return Resolution(
            kind="dynamic-symbol-head",
            pass_number=0,
            token=token,
            current=None,
            evidence=("no proven static function identity",),
        )


def build_resolver(
    *,
    historical_map: Path,
    foundation: Path,
    registry: Path,
    domain_surfaces: Iterable[Path],
    prefer_current_surface: bool = False,
) -> SourceResolver:
    historical_rows = load_historical_rows(historical_map)
    current_by_label, current_by_word = load_current_foundation(foundation)
    surfaces = load_domain_surfaces(domain_surfaces, current_by_word)
    sid_fields, surface_sids = load_registry(registry)
    return SourceResolver(
        historical_rows,
        current_by_label,
        current_by_word,
        surfaces,
        sid_fields,
        surface_sids,
        prefer_current_surface=prefer_current_surface,
    )
