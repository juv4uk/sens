#!/usr/bin/env python3
"""Read-only audit of *possible executable Lisp call heads* for Ukrainian migration.

Unlike spelling equality, this audit does NOT require (ук X) == (укр Y): both
spellings refer to the same domain-qualified identity by their single table row.

The analysis is lexical/static, not an evaluator or proof of runtime admission.
Only unquoted list heads are counted; formals, quoted data, comments, strings and
registry/domain-table declarations do not count as executable call sites.
Unresolved/ambiguous aliases are reported and never mechanically rewritten.

Exit 1 with --require-full while any Latin head or unparsed source remains.
This keeps migration RED without treating valid compact/full names as defects.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LATIN = re.compile(r"[A-Za-z]")
UKRAINIAN = re.compile(r"[А-Яа-яІіЇїЄєҐґ]")
BIT_WORD = re.compile(r"[01]+\Z")
CELL = r'(\(\)|"(?:\\.|[^"\\])*"|[^()\s]+)'
ROW = re.compile(
    r"^\s*\(([01]+)\s+\(ук\s+" + CELL + r"\)\s+\(укр\s+" + CELL
    + r"\)\s+\(san\s+" + CELL + r"\)\s+\(en\s+" + CELL
    + r"\)\s+\(LISP\s+" + CELL + r"\)\s+\(sym\s+" + CELL + r"\)\)\s*$"
)


@dataclass(frozen=True)
class Token:
    text: str
    line: int
    column: int
    kind: str = 'atom'


@dataclass(frozen=True)
class Form:
    values: tuple
    pos: Token


@dataclass(frozen=True)
class Prefix:
    marker: str
    datum: object


class SourceError(ValueError):
    pass


def tokenize(source: str) -> list[Token]:
    """Lisp tokens with locations; discard ; and nested #|…|# comments."""
    result = []
    i, line, col, size = 0, 1, 1, len(source)

    def advance(n: int) -> None:
        nonlocal i, line, col
        for c in source[i:i+n]:
            if c == '\n':
                line += 1
                col = 1
            else:
                col += 1
        i += n

    while i < size:
        ch = source[i]
        if ch.isspace():
            advance(1)
            continue
        if ch == ';':
            advance((source.find('\n', i) if '\n' in source[i:] else size) - i)
            continue
        if source.startswith('#|', i):
            origin = (line, col)
            depth = 0
            while i < size:
                if source.startswith('#|', i):
                    depth += 1
                    advance(2)
                elif source.startswith('|#', i):
                    depth -= 1
                    advance(2)
                    if depth == 0:
                        break
                else:
                    advance(1)
            if depth:
                raise SourceError(f'{origin[0]}:{origin[1]}: unclosed block comment')
            continue
        start_line, start_col = line, col
        if ch == '"':
            advance(1)
            closed = False
            while i < size:
                if source[i] == '\\':
                    advance(min(2, size - i))
                elif source[i] == '"':
                    advance(1)
                    closed = True
                    break
                else:
                    advance(1)
            if not closed:
                raise SourceError(f'{start_line}:{start_col}: unclosed string')
            result.append(Token('', start_line, start_col, 'string'))
            continue
        if source.startswith(',@', i) or source.startswith('#;', i):
            marker = source[i:i+2]
            result.append(Token(marker, start_line, start_col, 'prefix'))
            advance(2)
            continue
        if ch in "()'\x60,":
            result.append(Token(ch, start_line, start_col,
                                'paren' if ch in '()' else 'prefix'))
            advance(1)
            continue
        end = i
        while end < size and not source[end].isspace() and source[end] not in "();'\x60\",":
            if source.startswith('#|', end):
                break
            end += 1
        if end == i:
            raise SourceError(f'{start_line}:{start_col}: unexpected {ch!r}')
        result.append(Token(source[i:end], start_line, start_col))
        advance(end - i)
    return result


def parse(source: str) -> tuple:
    tokens = tokenize(source)
    pos = 0

    def read():
        nonlocal pos
        if pos >= len(tokens):
            raise SourceError('unexpected end of source')
        token = tokens[pos]
        pos += 1
        if token.kind == 'prefix':
            return Prefix(token.text, read())
        if token.text == '(' and token.kind == 'paren':
            children = []
            while pos < len(tokens) and tokens[pos].text != ')':
                children.append(read())
            if pos >= len(tokens):
                raise SourceError(f'{token.line}:{token.column}: unclosed list')
            pos += 1
            return Form(tuple(children), token)
        if token.text == ')' and token.kind == 'paren':
            raise SourceError(f'{token.line}:{token.column}: unexpected close')
        return token

    forms = []
    while pos < len(tokens):
        forms.append(read())
    return tuple(forms)


def atom(node: object) -> str | None:
    return node.text if isinstance(node, Token) and node.kind == 'atom' else None


def candidate_heads(forms: tuple):
    """Yield possible executable heads; do not confuse formals/data with calls."""
    def walk(node, quasi: int = 0):
        if isinstance(node, Prefix):
            if node.marker in ("'", '#;'):
                return
            if node.marker == chr(96):
                yield from walk(node.datum, quasi + 1)
                return
            if node.marker in (',', ',@'):
                yield from walk(node.datum, max(0, quasi - 1))
                return
            return
        if not isinstance(node, Form) or not node.values:
            return
        head = atom(node.values[0])
        if quasi:
            for child in node.values:
                yield from walk(child, quasi)
            return
        if head is not None:
            # Special reader/definition syntax is not a function invocation.
            syntax = {'quote', 'quasiquote', 'lambda', 'define', 'defmacro',
                      'let', 'let*', '001', '0010', '0011'}
            if (head not in syntax and not BIT_WORD.fullmatch(head)
                    and (LATIN.search(head) or UKRAINIAN.search(head))):
                yield node.values[0]
            # QUOTE / D3:001 is non-executable data; no scanning its contents.
            if head in {'quote', 'як-є', '001'}:
                return
            if head in {'quasiquote'}:
                for child in node.values[1:]:
                    yield from walk(child, quasi + 1)
                return
            if head in {'lambda', 'функція', '0010'}:
                # First argument is parameter declaration, not a call.
                for child in node.values[2:]:
                    yield from walk(child)
                return
            if head in {'define', 'defmacro', 'визначити', 'визначити-макрос', '0011'}:
                # Name and any formal parameter list are binding syntax.
                for child in node.values[2:]:
                    yield from walk(child)
                return
            if head in {'let', 'let*', 'звʼязати'} and len(node.values) > 1:
                bindings = node.values[1]
                if isinstance(bindings, Form):
                    for binding in bindings.values:
                        if isinstance(binding, Form):
                            for expr in binding.values[1:]:
                                yield from walk(expr)
                for child in node.values[2:]:
                    yield from walk(child)
                return
        for child in node.values[1:]:
            yield from walk(child)

    for form in forms:
        yield from walk(form)


def peer_index(root: Path) -> tuple[dict[str, list[str]], dict]:
    """Names in one row share an identity; different rows never get conflated."""
    names: dict[str, set[str]] = {}
    rows = missing = pair_differences = 0
    for number in range(1, 12):
        path = root / 'lib' / 'domains' / f'd{number}.lisp'
        if not path.exists():
            continue
        for line in path.read_text(encoding='utf-8').splitlines():
            m = ROW.fullmatch(line)
            if m is None or len(m.group(1)) != number:
                continue
            rows += 1
            bits, uk, ukr, san, en, lisp, sym = m.groups()
            if uk == '()' or ukr == '()':
                missing += 1
            elif uk != ukr:
                pair_differences += 1   # information, NOT migration failure
            identity = f'D{number}:{bits}'
            for spelling in (uk, ukr, en, lisp):
                if spelling != '()':
                    names.setdefault(spelling.casefold(), set()).add(identity)
    resolved = {name: sorted(identities) for name, identities in names.items()}
    return resolved, {'domain_rows': rows, 'missing_peer_spelling': missing,
                      'valid_distinct_peer_spellings': pair_differences,
                      'ambiguous_names': sum(len(v) > 1 for v in resolved.values())}


def excluded_metadata(path: Path) -> bool:
    parts = path.parts
    return (len(parts) >= 3 and parts[:2] == ('lib', 'domains')
            and re.fullmatch(r'd(?:[1-9]|10|11)\.lisp', parts[-1]) is not None
            or path.as_posix() == 'lib/surface/semantic-registry.lisp')


def measure(root: Path) -> dict:
    """Deterministic static evidence; does not alter a single source file."""
    root = root.resolve()
    files = sorted(p for p in root.rglob('*.lisp') if '.git' not in p.parts)
    index, peers = peer_index(root)
    latin, cyrillic, unknown, errors = [], 0, 0, []
    skipped = scanned = 0
    for path in files:
        rel = path.relative_to(root)
        if excluded_metadata(rel):
            skipped += 1
            continue
        if path.is_symlink() or not path.resolve().is_relative_to(root):
            errors.append({'file': rel.as_posix(), 'reason': 'symlink/out-of-root source'})
            continue
        scanned += 1
        try:
            forms = parse(path.read_text(encoding='utf-8'))
            for head in candidate_heads(forms):
                if LATIN.search(head.text):
                    candidates = index.get(head.text.casefold(), [])
                    latin.append({'file': rel.as_posix(), 'line': head.line,
                                  'column': head.column, 'head': head.text,
                                  'identities': candidates,
                                  'mapping': 'unique' if len(candidates) == 1
                                  else 'ambiguous' if candidates else 'unresolved'})
                elif UKRAINIAN.search(head.text):
                    cyrillic += 1
                else:
                    unknown += 1
        except (UnicodeError, OSError, SourceError, RecursionError) as exc:
            errors.append({'file': rel.as_posix(), 'reason': str(exc)})
    total = len(latin) + cyrillic
    return {'files_total': len(files), 'files_scanned': scanned,
            'metadata_files_excluded': skipped,
            'ukr_call_heads': cyrillic, 'latin_call_heads': len(latin),
            'ukr_call_head_pct': round(100 * cyrillic / total, 1) if total else 0.0,
            'unclassified_files': errors, 'latin_sites': latin,
            'peer_index': peers,
            'authority_warning': 'lexical candidates only; no runtime F1-F4/peer-eq proof'}


def render(m: dict, *, limit: int = 15) -> str:
    lines = [
        f"УКР-ВИКЛИКИ: кириличних голів {m['ukr_call_heads']}, латинських "
        f"{m['latin_call_heads']} ({m['ukr_call_head_pct']}% укр); "
        f"оглянуто .lisp {m['files_scanned']}/{m['files_total']}",
        f"PEER-ІМЕНА: рядків {m['peer_index']['domain_rows']}; "
        f"законних відмінностей ук/укр "
        f"{m['peer_index']['valid_distinct_peer_spellings']} "
        f"(НЕ помилки міграції); неоднозначних spelling "
        f"{m['peer_index']['ambiguous_names']}",
    ]
    for site in m['latin_sites'][:limit]:
        found = ','.join(site['identities']) or '-'
        lines.append(f"LATIN {site['file']}:{site['line']}:{site['column']} "
                     f"{site['head']} mapping={site['mapping']} identity={found}")
    if len(m['latin_sites']) > limit:
        lines.append(f"... додаткових латинських голів {len(m['latin_sites']) - limit}; "
                     "повний список доступний через --json")
    for error in m['unclassified_files'][:limit]:
        lines.append(f"UNCLASSIFIED {error['file']}: {error['reason']}")
    return '\n'.join(lines)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--json', type=Path, help='write full deterministic JSON diagnostics')
    parser.add_argument('--limit', type=int, default=15)
    parser.add_argument('--require-full', action='store_true',
                        help='fail while Latin source heads or unclassified files remain')
    args = parser.parse_args(argv)
    if args.limit < 0:
        parser.error('--limit cannot be negative')
    m = measure(args.root)
    print(render(m, limit=args.limit))
    if args.json:
        args.json.write_text(json.dumps(m, ensure_ascii=False, indent=2) + '\n',
                             encoding='utf-8')
    red = bool(m['latin_call_heads'] or m['unclassified_files']
               or m['ukr_call_heads'] == 0)
    if args.require_full and red:
        print(f"::error::УКР-ВИКЛИКИ НЕ ЗАВЕРШЕНІ: "
              f"{m['latin_call_heads']} Latin call heads, "
              f"{len(m['unclassified_files'])} unclassified .lisp files; "
              'не прирівнюйте ук до укр', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
