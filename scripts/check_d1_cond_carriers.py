#!/usr/bin/env python3
"""Read-only, conservative SENS Lisp source audit for exact D1 COND carriers.

A three-argument COND clause with an 00100010 (exact EQUAL) query must
compare against the exact D1 PredicateBit domain, NOT a historical list or
numeric carrier, even if both print '1' or '0'. This checker reports only
syntactically obvious mismatches; it is NOT an interpreter or proof of safety.

It never modifies input. Default mode is advisory, so known legacy source
cannot be accidentally certified or silently rewritten.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
from pathlib import Path
import sys


@dataclass(frozen=True)
class Node:
    value: str | tuple['Node', ...]
    line: int

    @property
    def is_list(self) -> bool:
        return isinstance(self.value, tuple)


def lex(source: str) -> list[tuple[str, int]]:
    """Tokenize Lisp lists, strings, and ; comments (keeping source lines)."""
    result: list[tuple[str, int]] = []
    i, line = 0, 1
    while i < len(source):
        c = source[i]
        if c.isspace():
            if c == '\n':
                line += 1
            i += 1
            continue
        # Reader character tokens like #\( and #\; are data, not delimiters.
        if source.startswith('#\\', i) and i + 2 < len(source):
            result.append((source[i:i + 3], line))
            i += 3
            continue
        # Non-program block comments can contain arbitrary parentheses.
        if source.startswith('#|', i):
            startline, depth = line, 1
            i += 2
            while i < len(source) and depth:
                if source.startswith('#|', i):
                    depth += 1
                    i += 2
                elif source.startswith('|#', i):
                    depth -= 1
                    i += 2
                else:
                    if source[i] == '\n':
                        line += 1
                    i += 1
            if depth:
                raise ValueError(f'unterminated block comment at line {startline}')
            continue
        if c == ';':
            end = source.find('\n', i)
            i = len(source) if end == -1 else end
            continue
        if c in '()':
            result.append((c, line))
            i += 1
            continue
        start, at = i, line
        if c == '"':
            i += 1
            while i < len(source):
                if source[i] == '\\':
                    i += 2
                    continue
                if source[i] == '"':
                    i += 1
                    break
                if source[i] == '\n':
                    line += 1
                i += 1
            else:
                raise ValueError(f'unterminated string at line {at}')
        else:
            while (i < len(source) and not source[i].isspace()
                   and source[i] not in '();'):
                i += 1
        result.append((source[start:i], at))
    return result


def read_forms(source: str) -> tuple[Node, ...]:
    tokens = lex(source)
    pos = 0

    def form() -> Node:
        nonlocal pos
        if pos >= len(tokens):
            raise ValueError('unexpected EOF')
        token, line = tokens[pos]
        pos += 1
        if token == ')':
            raise ValueError(f'unexpected close at line {line}')
        if token != '(':
            return Node(token, line)
        children = []
        while pos < len(tokens) and tokens[pos][0] != ')':
            children.append(form())
        if pos == len(tokens):
            raise ValueError(f'unclosed list at line {line}')
        pos += 1
        return Node(tuple(children), line)

    forms = []
    while pos < len(tokens):
        forms.append(form())
    return tuple(forms)


def elems(node: Node) -> tuple[Node, ...]:
    return node.value if node.is_list else ()


def head(node: Node, name: str) -> bool:
    items = elems(node)
    return bool(items) and not items[0].is_list and items[0].value == name


def legacy_carrier(node: Node) -> str | None:
    if not node.is_list:
        if node.value in ('0', '1'):
            return 'numeric-literal'
        if node.value == 't':
            return 'historical-t'
        return None
    items = elems(node)
    if not items:
        return 'structural-empty'
    if len(items) == 1 and not items[0].is_list and items[0].value in ('0', '1'):
        return 'singleton-list'
    return None


def audit(source: str, path: str) -> list[dict[str, object]]:
    findings = []
    for root in read_forms(source):
        stack = [root]
        while stack:
            node = stack.pop()
            items = elems(node)
            if head(node, '00000111') or head(node, 'cond'):
                for clause in items[1:]:
                    parts = elems(clause)
                    if not parts:
                        continue
                    query = parts[0]
                    # Exact D1 EQUAL returns PredicateBit. No scalar coercion.
                    if len(parts) == 3 and head(query, '00100010'):
                        kind = legacy_carrier(parts[1])
                        if kind:
                            findings.append({'path': path, 'line': clause.line,
                                             'kind': 'EQUAL_EXPECTED_' + kind.upper().replace('-', '_'),
                                             'severity': 'error',
                                             'message': 'EQUAL returns exact D1 PredicateBit; expected is ' + kind})
                    # Historical NOT may not invert an exact D1 bit. Advisory
                    # until this call site's mechanism is verified by a test.
                    if head(query, '00100001') and len(elems(query)) == 2 and head(elems(query)[1], '00100010'):
                        findings.append({'path': path, 'line': clause.line,
                                         'kind': 'NOT_OF_EXACT_EQUAL', 'severity': 'review',
                                         'message': 'Legacy NOT of exact D1 EQUAL requires runtime verification'})
            stack.extend(reversed(items))
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('paths', nargs='+', type=Path, help='Lisp files or directories')
    parser.add_argument('--format', choices=('text', 'json'), default='text')
    parser.add_argument('--fail-on-findings', action='store_true',
                        help='Opt-in: nonzero exit on an ERROR finding, for explicitly cleaned paths')
    args = parser.parse_args(argv)
    found: list[dict[str, object]] = []
    errors: list[str] = []
    files = sorted({f for path in args.paths for f in (
        path.rglob('*.lisp') if path.is_dir() else [path])})
    for path in files:
        try:
            found.extend(audit(path.read_text(encoding='utf-8'), str(path)))
        except (OSError, UnicodeError, ValueError, RecursionError) as exc:
            errors.append(f'{path}: {exc}')
    if args.format == 'json':
        print(json.dumps({'findings': found, 'parse_errors': errors}, ensure_ascii=False, indent=2))
    else:
        for issue in found:
            print(f"{issue['path']}:{issue['line']}: {issue['severity']} {issue['kind']}: {issue['message']}")
        for err in errors:
            print('AUDIT ERROR:', err, file=sys.stderr)
        print(f'Findings: {len(found)}; parse errors: {len(errors)}')
    if errors or args.fail_on_findings and any(i['severity'] == 'error' for i in found):
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
