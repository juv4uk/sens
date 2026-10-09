#!/usr/bin/env python3
"""#2019 H-NIL current-corpus kill test.

Research evidence only. This does not redefine Function8 00000000 and does not
ratify a 7-seed bīja3. It asks a narrower question:

    Does the current SENS corpus require NIL / empty ground as a callable
    operator, rather than as structural data?

The audit deliberately keeps three concepts separate:
- structural () / Value::Nil as ground data;
- the exact Function8 slot 00000000;
- historical Core1 NIL spellings.

A future independent function may occupy 00000000. That is not automatically
"NIL". Any such change merely invalidates this bounded snapshot and requires a
fresh classification.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]

# These are identity/projection metadata, not executable Lisp program bodies.
METADATA_LISP = {
    Path("lib/generated/function-table.lisp"),
    Path("lib/surface/semantic-registry.lisp"),
    Path("lib/surface/semantic-registry-experiment.lisp"),
}

ZERO8 = "00000000"


@dataclass(frozen=True)
class Token:
    text: str
    line: int


def tokenize_lisp(text: str) -> list[Token]:
    """Tiny lexer sufficient for call-head auditing.

    Strings and ';' comments are discarded so documentation/examples inside
    them cannot become false executable witnesses.
    """

    tokens: list[Token] = []
    i = 0
    line = 1
    n = len(text)

    while i < n:
        ch = text[i]

        if ch == "\n":
            line += 1
            i += 1
            continue

        if ch.isspace():
            i += 1
            continue

        if ch == ";":
            while i < n and text[i] != "\n":
                i += 1
            continue

        if ch == '"':
            i += 1
            while i < n:
                if text[i] == "\\":
                    i += 2
                    continue
                if text[i] == '"':
                    i += 1
                    break
                if text[i] == "\n":
                    line += 1
                i += 1
            continue

        if ch in "()'":
            tokens.append(Token(ch, line))
            i += 1
            continue

        start = i
        while i < n and (not text[i].isspace()) and text[i] not in "();'\"":
            i += 1
        tokens.append(Token(text[start:i], line))

    return tokens


def call_heads(tokens: list[Token]) -> list[Token]:
    heads: list[Token] = []
    for i, token in enumerate(tokens[:-1]):
        if token.text != "(":
            continue
        nxt = tokens[i + 1]
        if nxt.text not in {"(", ")"}:
            heads.append(nxt)
    return heads


def scan_active_lisp() -> tuple[list[tuple[Path, Token]], list[tuple[Path, Token]], list[tuple[Path, Token]], int]:
    nil_heads: list[tuple[Path, Token]] = []
    zero_heads: list[tuple[Path, Token]] = []
    zero_tokens: list[tuple[Path, Token]] = []
    nil_token_count = 0

    for path in sorted((ROOT / "lib").rglob("*.lisp")):
        rel = path.relative_to(ROOT)
        tokens = tokenize_lisp(path.read_text(encoding="utf-8"))
        heads = call_heads(tokens)

        for token in tokens:
            if token.text.casefold() == "nil":
                nil_token_count += 1
            if token.text == ZERO8 and rel not in METADATA_LISP:
                zero_tokens.append((rel, token))

        for head in heads:
            if head.text.casefold() == "nil":
                nil_heads.append((rel, head))
            if head.text == ZERO8 and rel not in METADATA_LISP:
                zero_heads.append((rel, head))

    return nil_heads, zero_heads, zero_tokens, nil_token_count



def contract_has_ground_separation(contract: str) -> bool:
    """Вимагає чинний закон D3, а не вилучене формулювання Function8.

    Шукаємо лише значення властивості structural-empty-non-alias: окремі
    згадки D3, D1 та історичного байта в інших реченнях не є доказом.
    Відсутність чи зміна нормативного поля завершується fail-closed.
    """
    match = re.search(
        r'(?m)^[ \\t]*\\(structural-empty-non-alias\\s*\\.\\s*"(?P<law>(?:\\\\.|[^"\\\\])*)"\\s*\\)',
        contract,
    )
    if match is None:
        return False
    law = match.group("law").casefold()
    return all(
        requirement in law
        for requirement in (
            "core.d3 000 structural empty",
            "not historical exact-eight-bit 00000000",
            "not predicatebit 0 or number zero",
            "equal packed numeric zero across domains never collapses those identities",
        )
    )


def route_evidence() -> tuple[bool, bool]:
    """Inspect the historical metadata and the language-owned separation law.

    The retired Rust SID_ROUTES table is neither a source of language meaning
    nor a required fixture. Its absence must not cause this archaeology audit
    to fail or be interpreted as proof about exact-domain execution.
    """
    mechanism = (ROOT / "lib/function-table-mechanisms.lisp").read_text(encoding="utf-8")
    contract = (ROOT / "language-contract.lisp").read_text(encoding="utf-8")

    mechanism_tokens = tokenize_lisp(mechanism)
    zero_in_mechanism_rows = any(
        token.text == ZERO8 for token in call_heads(mechanism_tokens)
    )

    contract_separates_ground = contract_has_ground_separation(contract)

    return zero_in_mechanism_rows, contract_separates_ground


def format_sites(sites: list[tuple[Path, Token]]) -> str:
    if not sites:
        return "-"
    return ",".join(f"{path}:{token.line}" for path, token in sites)


def main() -> int:
    nil_heads, zero_heads, zero_tokens, nil_token_count = scan_active_lisp()
    zero_mechanism, separated = route_evidence()

    # A ZERO8 token in executable lib source is not automatically NIL. We print
    # it as a review trigger rather than making the all-zero function slot
    # permanently unusable.
    print("metric\tvalue\tinterpretation")
    print(f"active_nil_tokens\t{nil_token_count}\tdata/history tokens allowed")
    print(f"callable_nil_heads\t{len(nil_heads)}\t{format_sites(nil_heads)}")
    print(f"zero8_call_heads_nonmetadata\t{len(zero_heads)}\t{format_sites(zero_heads)}")
    print(f"zero8_tokens_nonmetadata\t{len(zero_tokens)}\t{format_sites(zero_tokens)}")
    print(f"zero8_in_mechanism_rows\t{int(zero_mechanism)}\tcurrent function mechanism metadata")
    print(f"contract_ground_separated\t{int(separated)}\t() data is distinct from Function8 zero")

    failures: list[str] = []
    if nil_heads:
        failures.append("active Lisp contains callable (NIL ...) / (nil ...) head")
    if zero_mechanism:
        failures.append(
            "current zero Function8 has mechanism metadata; H-NIL snapshot needs semantic reclassification"
        )
    if not separated:
        failures.append("Contract 11.8 must explicitly separate D3:000 from D1:0 and historical Function8 zero")

    if failures:
        for failure in failures:
            print(f"FAIL\t{failure}", file=sys.stderr)
        return 1

    print(
        "PASS\tbounded current-corpus witness: structural empty is used as data, "
        "while callable/operator NIL is not required by active Lisp heads or historical mechanism metadata"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
