#!/usr/bin/env python3
"""Розпізнавач джерельних голів SENS із розмежуванням епох.

Чинні D3–D6 identity беруться лише з ратифікованої таблиці та її
проєкцій. Історичні рядки SID8/Lisp I залишаються походженням
(діагностикою), не семантичною владою. Восьмибітний голів без
явного доменного контексту відхиляється; це не новий D8.
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


# Маркер виведення файла з ужитку (стаб замість реєстру).
RETIRED_MARKER = "ВИВЕДЕНО З УЖИТКУ"


def load_historical_rows(path: Path) -> list[HistoricalRow]:
    raw = path.read_text(encoding="utf-8")
    text = _strip_semicolon_comments(raw)
    rows = [HistoricalRow(*m.groups()) for m in HISTORICAL_ROW_RE.finditer(text)]
    if not rows:
        # Першопричина: історичний реєстр плоских W8/SID виведено з ужитку
        # (стаб із маркером), а резолвер усе ще ВИМАГАВ рядки й падав — тож
        # валив усіх споживачів. Виведений реєстр дає порожній історичний
        # індекс (живий шлях його не потребує), а справжня втрата рядків у
        # НЕвиведеному файлі лишається помилкою.
        if RETIRED_MARKER in raw:
            return []
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
    ambiguous_labels: set[str] = set()
    # D7 carries keyboard/text DATA, never callable heads. D1/D2 are
    # predicate/structure, not interchangeable with function identities.
    # Older pinned foundations may lack D8–D10; the current full foundation
    # includes them and is selected by the command-line inventory.
    for domain in ("D3", "D4", "D5", "D6", "D8", "D9", "D10"):
        if domain not in data["domains"]:
            continue
        desc = data["domains"][domain]
        width = int(desc["width"])
        if width != int(domain[1:]):
            raise ValueError(f"invalid exact domain width: {domain}")
        for bits, label in desc["residents"].items():
            if len(bits) != width or set(bits) - {"0", "1"}:
                raise ValueError(f"invalid exact domain word: {domain}:{bits}")
            identity = CurrentIdentity(domain, width, bits, str(label))
            key = str(label).upper()
            # Same historical spelling can occur in distinct domains
            # (e.g. D6 MAP != D8 MAP). Never pick one by insertion order.
            if key not in ambiguous_labels:
                previous = by_label.get(key)
                if previous is not None and previous != identity:
                    by_label.pop(key)
                    ambiguous_labels.add(key)
                else:
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
    ):
        self.current_by_label = current_by_label
        self.current_by_word = current_by_word
        self.domain_surfaces = domain_surfaces
        self.registry_sid_fields = registry_sid_fields
        self.registry_surface_sids = registry_surface_sids

        # Першопричина (#5997 → тут): порожній історичний індекс — це НЕ те
        # саме, що «історичних даних немає». Після виведення SID-реєстру
        # індекс порожній, і прохід 1/2/3 усе одно «виконувався», повертаючи
        # впевнений результат без жодного знання. Тепер спроможність названа
        # явно й падає закрито, а не вдає роботу.
        self.historical_retired = not historical_rows
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

        # Жодні історичні сід8, мітки чи registry-аліаси не додають
        # поточних резидентів. Лише канонічні доменні проєкції є authority.

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

    def resolve_head(self, token: str, *, source_era: str = "current") -> Resolution:
        if source_era not in {"current", "legacy"}:
            raise ValueError(f"невідома епоха джерела: {source_era}")
        # Першопричина: якщо історичну спроможність виведено, жоден
        # «історичний» прохід виконати НЕ МОЖНА. Порожній результат тут
        # недопустимий: він не відрізняється від «перевірено й не історичне».
        # Тож — fail-closed із прямою причиною; живий шлях (current) не зачеплено.
        if source_era == "legacy" and self.historical_retired:
            raise ValueError(
                "historical capability retired: core1-historical-sid-map is a "
                "stub, so no historical (legacy) head can be resolved. Refusing "
                "to return a silently-empty historical pass. Use source_era="
                "'current' for the live ratified surface, or restore a dated "
                "historical register with explicit provenance."
            )
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

        # D8 was owner-ratified only on 2026-10-06 (#3960).
        # Earlier eight-bit executable heads belong to historical W8/сід8/сенс8,
        # NOT to D8 merely because the payload has eight bits. A modern raw W8
        # token is likewise ambiguous without an explicit source-era proof.
        if re.fullmatch(r"[01]{8}", token):
            if source_era == "legacy":
                rows = self.hist_by_sid.get(token, [])
                # Лише явно історичний корпус: роль із джерела минулої
                # епохи зіставляємо з чинною доменною поверхнею.
                # Це КАНДИДАТ адреси, не доказ еквівалентності чи виконання.
                candidates: set[CurrentIdentity] = set()
                for row in rows:
                    for spelling in (row.my_lisp, row.historical):
                        # A historic SID8 role is only a D3–D6 candidate here.
                        # Modern D8–D10 spelling alone is no provenance bridge.
                        candidates.update(
                            candidate
                            for candidate in self.current_surface.get(spelling, set())
                            if candidate.domain in {"D3", "D4", "D5", "D6"}
                        )
                return self._choose(
                    "sid8-sens8", 1, token, candidates,
                    legacy_sid8=token, rows=rows,
                    evidence=(
                        "explicit legacy provenance, not modern D8",
                        "ratified surface candidate; execution not certified",
                    ),
                )
            raise ValueError(
                f"retired SID8-era head {token}: ambiguous eight-bit source; "
                "modern D8 residency does not prove historical function identity "
                "or runtime callability. Resolve the original function role by "
                "historical provenance, then use its ratified full укр surface"
            )

        # PASS 2: exact my-lisp / admitted surface spelling.  This is
        # intentionally case-sensitive; uppercase historical names are held
        # for Pass 3.
        if token not in self.hist_by_upper:
            rows = self.hist_by_my.get(token, [])
            candidates = set(self.current_surface.get(token, set()))
            # Сам по собі історичний восьмибітний реєстр не робить
            # символ ні відомою функцією, ні міграційним блокером.
            # Лише чинна проєкція або окремий датований рядок походження.
            if rows or candidates:
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

        # PASS 3: historical Lisp I / Lisp 1.5 UPPERCASE surface.
        rows = self.hist_by_upper.get(token)
        if rows is not None:
            # Поточна identity походить лише з поточної таблиці назв,
            # навіть якщо старе написання присутнє в історичних рядках.
            candidates = set(self.current_surface.get(token, set()))
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
    )
