#!/usr/bin/env python3
"""#4430 — conservative Ukrainian <-> typed words <-> physical T5M/legacy-T5 triplet proof.

Deliberately bounded: ratified D1 predicates, exact D3 call-head syntax
QUOTE/ATOM/CDR/CAR/EQ/COND/CONS and literal D3 EMPTY, plus D2 grammar.
QUOTE accepts only proven atomic D1 or literal-empty data, never unproven
quoted list/Text7/Number/binder payloads. This read-only canonical source
proof does NOT establish evaluation semantics or release admission.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from domain_tables import read_domain_table
from sens_t5_codec import (SensT5Error, decode_bytes, encode_words,
                           decode_t5m_bytes, encode_t5m_projection, typed_sha256)

CONVERTER = SCRIPTS / "migrate-three-pass.py"
SPEC = importlib.util.spec_from_file_location("uk_t5_canonical_three_pass", CONVERTER)
assert SPEC and SPEC.loader
three_pass = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = three_pass
SPEC.loader.exec_module(three_pass)

SCHEMA = "sens-uk-t5-view-bounded-proof/v1"


class ProjectionBlocked(ValueError):
    pass


def uk_surface(width: int) -> dict[str, str]:
    """Read full 'укр' names from ratified domain table, never compact or English aliases."""
    if width not in (1, 3, 4):
        raise ProjectionBlocked("no ratified Ukrainian renderer for this width")
    # Parse structural () through the canonical table reader. Regex token
    # matching excluded D3:000 and wrongly blocked the whole D3 authority.
    rows = [(row.bits, row.ukr) for row in read_domain_table(
        ROOT / f"lib/domains/d{width}.lisp"
    )]
    if (len(rows) != 2 ** width or
            any(name is None for _, name in rows) or
            len({bits for bits, _ in rows}) != len(rows) or
            len({name for _, name in rows}) != len(rows)):
        raise ProjectionBlocked(f"D{width}: nonunique or incomplete ук authority")
    return dict(rows)


class WordParser:
    def __init__(self, words: list[str]):
        self.words = words
        self.index = 0

    def take(self) -> str:
        if self.index >= len(self.words):
            raise ProjectionBlocked("unterminated D2 list")
        result = self.words[self.index]
        self.index += 1
        return result

    def term(self, depth: int = 0):
        # Чинний SENS reader обмежує фізичні D2-вкладення 128.
        # Статичний доказ не має допускати програму, яку SENS відхилить.
        if depth > 128:
            raise ProjectionBlocked("D2 nesting exceeds current SENS reader limit (128)")
        token = self.take()
        if token == "10":
            if self.index == len(self.words) or self.words[self.index] == "01":
                raise ProjectionBlocked("D2 empty list must use D3 000")
            children = [self.term(depth + 1)]
            while True:
                nxt = self.take()
                if nxt == "01":
                    break
                if nxt != "00":
                    raise ProjectionBlocked("D2 list requires one separator between items")
                children.append(self.term(depth + 1))
            return ("list", tuple(children))
        if token == "000":
            return ("empty",)
        if token in ("0", "1"):
            return ("predicate", token)
        if token in ("001", "010", "011", "100", "101", "110", "111",
                     "0110", "0111", "1000", "1001"):
            return ("head", token)
        # Точне D24+ числове слово: ширина кратна 24 (доповнення до двох).
        if len(token) >= 24 and len(token) % 24 == 0:
            return ("number", token)
        raise ProjectionBlocked(f"outside bounded D1/D3 callable or data law: {token!r}")

    def parse(self):
        if not self.words:
            raise ProjectionBlocked("empty exact-word program")
        # D2: кілька верхніх форм — одна програма, а не помилка.
        # Канонічний друк між формами має рівно одне слово D2:00:
        # зайві, початкові чи кінцеві роздільники не є оберненою укр-проєкцією.
        forms = [self.term()]
        while self.index < len(self.words):
            if self.take() != "00" or self.index >= len(self.words):
                raise ProjectionBlocked("noncanonical D2 separator between top-level forms")
            forms.append(self.term())
        return forms


def proved_nil_pair_tree(node) -> bool:
    """Bounded shape proof: QUOTE(EMPTY) or recursively nested D3 CONS.

    Not a general typed pair theorem and not approval of D7/number/lexical
    quotation. CAAR needs a CONS whose CAR is itself a proved CONS pair.
    """
    if node[0] != "list":
        return False
    items = node[1]
    if len(items) == 2 and items[0] == ("head", "001"):
        return items[1] == ("empty",)
    if len(items) == 3 and items[0] == ("head", "111"):
        return proved_nil_pair_tree(items[1]) and proved_nil_pair_tree(items[2])
    return False


def proved_selector_input(node, opcode: str) -> bool:
    """Bounded D3 CONS tree proves the intermediate pair exists for a D4 selector.

    This is structural identity, not a universal runtime or Lisp-eval oracle.
    """
    if (node[0] != "list" or len(node[1]) != 3
            or node[1][0] != ("head", "111")
            or not proved_nil_pair_tree(node)):
        return False
    _head, car, cdr = node[1]
    required = car if opcode in ("1000", "0110") else cdr
    return (required[0] == "list" and len(required[1]) == 3
            and required[1][0] == ("head", "111")
            and proved_nil_pair_tree(required))


def proved_caar_input(node) -> bool:
    return proved_selector_input(node, "1000")


def render_uk(node, d1: dict[str, str], d3: dict[str, str],
              d4: dict[str, str]) -> str:
    kind = node[0]
    if kind == "empty":
        return "()"
    if kind == "number":
        width = len(node[1]); value = int(node[1], 2)
        if value >= (1 << (width - 1)):
            value -= (1 << width)
        return str(value)
    if kind == "predicate":
        return d1[node[1]]
    if kind != "list":
        raise ProjectionBlocked("callable head outside executable list")
    items = node[1]
    if not items or items[0][0] != "head":
        raise ProjectionBlocked("unknown callable head or COND clause context")
    opcode = items[0][1]
    if opcode in ("0110", "0111", "1000", "1001"):
        if len(items) != 2 or not proved_selector_input(items[1], opcode):
            raise ProjectionBlocked(
                f"D4 {d4[opcode]} requires a proved nested CONS pair"
            )
        return "(" + d4[opcode] + " " + render_uk(items[1], d1, d3, d4) + ")"
    # Each admitted spelling comes from the owner's D3 domain table. A
    # callable D3 slot is not permission to invent unproved datum grammar.
    if opcode == "001":
        if len(items) != 2:
            raise ProjectionBlocked("D3 QUOTE requires exactly one datum")
        if items[1][0] not in ("predicate", "empty"):
            raise ProjectionBlocked("D3 QUOTE structured/Text7 data not proven")
        return "(" + d3[opcode] + " " + render_uk(items[1], d1, d3, d4) + ")"
    if opcode in ("010", "011", "100"):
        if len(items) != 2:
            raise ProjectionBlocked("D3 unary ATOM/CDR/CAR requires one argument")
        return "(" + d3[opcode] + " " + render_uk(items[1], d1, d3, d4) + ")"
    if opcode in ("101", "111"):
        if len(items) != 3:
            raise ProjectionBlocked("D3 binary EQ/CONS requires two arguments")
        return ("(" + d3[opcode] + " " + render_uk(items[1], d1, d3, d4)
                + " " + render_uk(items[2], d1, d3, d4) + ")")
    if opcode == "110":
        if len(items) < 2:
            raise ProjectionBlocked("D3 COND requires at least one paired clause")
        clauses = []
        for item in items[1:]:
            if item[0] != "list" or len(item[1]) != 2:
                raise ProjectionBlocked("D3 COND requires two-part D2 clause records")
            clauses.append("(" + " ".join(render_uk(x, d1, d3, d4)
                                          for x in item[1]) + ")")
        return "(" + d3[opcode] + " " + " ".join(clauses) + ")"
    raise ProjectionBlocked("unratified callable in bounded renderer")


def canonical_uk_from_words(words: list[str]) -> str:
    d1, d3, d4 = uk_surface(1), uk_surface(3), uk_surface(4)
    # Лише відновлення точних назв і меж D2; результат виконує сам SENS.
    return "\n".join(
        render_uk(form, d1, d3, d4) for form in WordParser(words).parse()
    ) + "\n"


def project_current_uk(source: str) -> list[str]:
    # Коментарі/пробіли не є програмними бітами, але виконувані
    # англомовні T/NIL/CAR/COND — НЕ українські назви навіть коли
    # legacy resolver міг би відобразити їх у той самий машинний код.
    without_comments = three_pass.strip_comments(source)
    tokens = three_pass.tokenize(without_comments, source_surface="укр")
    # Латинь заборонена як ВИКОНУВАНА голова, але лише коли ім'я справді є
    # англійським аліасом доменного виклику. Ключі даних ISA/інвентарів
    # (id/role/path/…) лишаються латиницею за політикою репо — це не виклики.
    if str(SCRIPTS) not in sys.path:
        sys.path.insert(0, str(SCRIPTS))
    from domain_tables import read_domain_table
    _english_heads = {"T", "NIL", "TRUE", "FALSE"}
    for _w in (1, 3, 4, 5, 6, 7, 8, 9, 10, 11):
        _tbl = ROOT / "lib" / "domains" / f"d{_w}.lisp"
        if not _tbl.is_file():
            continue
        try:
            _rows = read_domain_table(_tbl)
        except Exception:
            continue
        for _row in _rows:
            if _row.en:
                _english_heads.add(_row.en.upper())
    # Перевіряти лише виконувані голови AST. Після D3 QUOTE або '
    # навіть (CAR ...) є даними, а не спробою виклику англійського CAR.
    # Це reader-класифікація, не Python-імітація SENS-eval.
    forms = three_pass.Parser(tokens).parse_program()

    def reject_english_executable_heads(node, *, quoted=False):
        if quoted or isinstance(node, three_pass.Quote):
            return
        if not isinstance(node, three_pass.ListNode) or not node.items:
            return
        head = node.items[0]
        if isinstance(head, three_pass.Atom):
            name = head.tok.text
            if re.search(r"[A-Za-z]", name) and name.upper() in _english_heads:
                raise ProjectionBlocked(
                    "noncanonical Ukrainian source: Latin executable head"
                )
            if name == "як-є":
                # Цитований payload, у тому числі його внутрішні LP,
                # не може набути викличності від текстового збігу.
                return
        for item in node.items:
            reject_english_executable_heads(item)
        if node.tail is not None:
            reject_english_executable_heads(node.tail)

    for form in forms:
        reject_english_executable_heads(form)
    data = three_pass.load_foundation(ROOT / "knowledge/d1-d11-foundation.json")
    my, upper, _retired_bridge = three_pass.build_three_pass_maps(
        data,
        ROOT / "crates/sens/src/domain_surface_registry_generated.rs",
        ROOT / "crates/sens/src/semantic_registry_generated.rs",
        ROOT / "crates/sens/src/semantic_registry.rs",
        ROOT / "crates/sens/src/eval/necessary_forms_generated.rs",
    )
    # Ratified D7 keyboard/v2 (width 7, capacity 128, occupancy 128/128) is the
    # single current Text7 authority. The historical
    # crates/sens/src/text7_projection_generated.rs donor carries no executable
    # SA_SLP1_ENCODE/UK_ENCODE mapping and stays fail-closed: it is never
    # silently substituted for the ratified table.
    text7 = three_pass.build_text7(
        data, ROOT / "knowledge/d7-keyboard-v2-ratified.json"
    )
    # The current resolver accepts exact-domain surface maps, not historical
    # SID8/source-era dispatch. A canonical Ukrainian source is explicit.
    d9_residents = set(data["domains"].get("D9", {}).get("residents", {}))
    resolver = three_pass.Resolver(my, upper, d9_residents=d9_residents)
    visible = three_pass.migrate_file(
        source, resolver, text7, source_surface="укр"
    )
    # passthrough-head — це НЕ виклик, а запис даних (ключ ISA/інвентаря):
    # його латиниця лишається за політикою репо. Відкидаємо лише справді
    # історичні великолітерні Lisp-імена (pass3-lisp15) та сирі двійкові
    # голови (already-exact).
    if (resolver.counts["pass3-lisp15"]
            or resolver.counts["already-exact"]):
        raise ProjectionBlocked("non-ukrainian, historical or unknown source head")
    return visible.split()


def checked_file(path: Path) -> bytes:
    if not path.is_file():
        raise ProjectionBlocked(f"missing triplet file: {path}")
    if any(p.is_symlink() for p in (path, *path.parents)):
        raise ProjectionBlocked(f"symlink not admitted for triplet: {path}")
    return path.read_bytes()


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def verify(lisp: Path, sens: Path, view: Path, *, codec: str = "t5m") -> dict:
    """Read-only proof of *program identity*, not original .lisp byte restoration."""
    if lisp.suffix != ".lisp" or sens != lisp.with_suffix(".sens") or view != lisp.with_suffix(""):
        raise ProjectionBlocked("all three inputs must be exact same-stem paths")
    src = checked_file(lisp)
    binary = checked_file(sens)
    readable = checked_file(view)
    try:
        source = src.decode("utf-8")
    except UnicodeError as exc:
        raise ProjectionBlocked("invalid source UTF-8") from exc
    if codec not in ("auto", "t5m", "t5"):
        raise ProjectionBlocked("unknown physical codec: " + codec)
    # Use byte-exact physical roundtrip and same-stem view. Never guess old
    # T5 word boundaries from a T5M prefix (or silently accept stale views).
    candidates = []
    for name, decoder, encoder in (
        ("t5m", decode_t5m_bytes, lambda ws: encode_t5m_projection(" ".join(ws))),
        ("t5", decode_bytes, encode_words),
    ):
        if codec not in ("auto", name):
            continue
        try:
            decoded = decoder(binary)
            encoded = encoder(decoded)
        except SensT5Error:
            continue
        if encoded == binary and (" ".join(decoded) + "\n").encode("ascii") == readable:
            candidates.append((name, decoded))
    if not candidates:
        raise ProjectionBlocked("physical T5M/T5 bytes or canonical view mismatch")
    if len({tuple(candidate_words) for _, candidate_words in candidates}) != 1:
        raise ProjectionBlocked("ambiguous T5M/T5 words: explicit codec required")
    physical_codec, words = candidates[0]
    # Canonical output is a *rendering* of the decoded program, not a copy of
    # the original file. Comments, spaces and line endings carry no SENS law.
    # Compare its exact typed words with those of the actual Ukrainian source.
    canonical_source = canonical_uk_from_words(words)
    canonical_view = (" ".join(words) + "\n").encode("ascii")
    if readable != canonical_view:
        raise ProjectionBlocked("missing, stale or noncanonical ASCII 0/1 view")
    # Обидві гілки повертають саме байти, а не посилання на функцію.
    # Для explicit legacy t5 виклик encode_words(ws) є необхідним:
    # інакше реальний перевірений T5 помилково стає червоним.
    encode_current = (lambda ws: encode_t5m_projection(" ".join(ws))
                      if physical_codec == "t5m" else encode_words(ws))
    if encode_current(words) != binary:
        raise ProjectionBlocked("physical carrier not byte-canonical")
    try:
        projected = project_current_uk(source)
        reconstructed = project_current_uk(canonical_source)
    except (three_pass.MigrationError, SensT5Error, OSError, ValueError) as exc:
        raise ProjectionBlocked("Ukrainian program could not be projected to exact words") from exc
    if projected != words or reconstructed != words or encode_current(projected) != binary:
        raise ProjectionBlocked("program identity changed across Ukrainian Lisp ↔ exact words ↔ physical T5")
    return {
        "schema": SCHEMA,
        "status": "BOUNDED_TRIPLE_PARITY_ONLY_NOT_RELEASE_ADMISSION",
        "scope": "D1 predicates / D2 frames / D3 exact-call syntax / four D4 selectors of proven nested CONS",
        "source": str(lisp),
        "sens": str(sens),
        "view": str(view),
        "source_sha256": sha256(src),
        "physical_sha256": sha256(binary),
        "view_sha256": sha256(readable),
        "typed_word_sha256": typed_sha256(words),
        "typed_word_count": len(words),
        "physical_bytes": len(binary),
        "physical_codec": physical_codec,
        "physical_T5_roundtrip": physical_codec == "t5",
        "physical_T5M_roundtrip": physical_codec == "t5m",
        "canonical_uk_roundtrip": True,
        "program_identity_roundtrip": True,
        "canonical_view_roundtrip": True,
        "runtime_oracle_admitted_by_this_audit": False,
        "old_originals_migrated_by_this_audit": 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lisp", type=Path, required=True)
    parser.add_argument("--sens", type=Path, required=True)
    parser.add_argument("--view", type=Path, required=True)
    parser.add_argument("--codec", choices=("auto", "t5m", "t5"), default="t5m",
                        help="T5M за замовчуванням; t5 і auto — явний історичний аудит")
    args = parser.parse_args()
    try:
        result = verify(args.lisp, args.sens, args.view, codec=args.codec)
    except (ProjectionBlocked, OSError, ValueError) as exc:
        print("BLOCKED: " + str(exc), file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
