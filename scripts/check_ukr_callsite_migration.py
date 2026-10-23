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
# Та сама стандартна українська розкладка, що і в головному звіті.
UKRAINIAN_KEYBOARD_OUTPUTS = set(
    "абвгґдеєжзиіїйклмнопрстуфхцчшщьюя"
    "АБВГҐДЕЄЖЗИІЇЙКЛМНОПРСТУФХЦЧШЩЬЮЯ"
    "0123456789"
    "'\\-=./!\"№;%:?*()_+,₴ "
)
BIT_WORD = re.compile(r"[01]+\Z")
ENCODED_HEAD = re.compile(r"#(?:[dD][0-9]+:[01]+|[bB][01]+|[xX][0-9A-Fa-f]+)\Z")
LIVE_SOURCE_DIRS = {'lib', 'examples', 'scripts'}
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
    """Yield possible executable heads without treating COND tests or data as calls."""
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
            # Старі SID8/Sens8 та сучасні exact-bit голови не є
            # українською людською проєкцією. Не відкидай їх з
            # аудиту лише тому, що вони складаються з 0/1.
            # Саму семантику старого W8 без provenance не вгадуємо.
            if (head not in syntax
                    and (BIT_WORD.fullmatch(head) or ENCODED_HEAD.fullmatch(head)
                         or LATIN.search(head) or UKRAINIAN.search(head))):
                yield node.values[0]
            # D3 COND clauses are (predicate result) pairs. A typed D1 value
            # such as #d1:1 in predicate position is a value, not a call head.
            if head in {'110', 'cond', 'за-умовою'}:
                for clause in node.values[1:]:
                    if isinstance(clause, Form) and len(clause.values) >= 2:
                        yield from walk(clause.values[0])
                        for result in clause.values[1:]:
                            yield from walk(result)
                    else:
                        yield from walk(clause)
                return
            # QUOTE / D3:001 is non-executable data; do not scan its contents.
            if head in {'quote', 'як-є', '001'}:
                return
            if head == 'quasiquote':
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
            if head in {'let', 'let*', 'звʼязати', "зв'язати", 'нехай', 'нехай-послідовно', '001000', '001001'} and len(node.values) > 1:
                bindings = node.values[1]
                if isinstance(bindings, Form):
                    for binding in bindings.values:
                        if isinstance(binding, Form):
                            for expr in binding.values[1:]:
                                yield from walk(expr)
                for child in node.values[2:]:
                    yield from walk(child)
                return
        # Обчислювана голова теж містить виконуваний код:
        # ((функція (x) (перше x)) аргумент) не можна пропускати.
        # Для quote/define/let ранні гілки вище вже зберігають
        # відмінність між даними, деклараціями та викликами.
        if isinstance(node.values[0], Form):
            yield from walk(node.values[0])
        for child in node.values[1:]:
            yield from walk(child)

    for form in forms:
        yield from walk(form)


def peer_index(root: Path) -> tuple[dict[str, list[str]], dict]:
    """Names in one row share an identity; different rows never get conflated."""
    names: dict[str, set[str]] = {}
    rows = missing = pair_differences = 0
    for number in range(1, 11):  # Д11: 43 записи НЕ ратифіковані як виклики
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


def peer_roles(root: Path) -> dict[str, set[str]]:
    """Classify exact compact/full spellings without equating them."""
    roles: dict[str, set[str]] = {}
    for number in range(1, 11):  # Д11: 43 записи НЕ ратифіковані як виклики
        path = root / 'lib' / 'domains' / f'd{number}.lisp'
        if not path.exists():
            continue
        for line in path.read_text(encoding='utf-8').splitlines():
            m = ROW.fullmatch(line)
            if m is None or len(m.group(1)) != number:
                continue
            for kind, spelling in [('ук', m.group(2)), ('укр', m.group(3))]:
                if spelling != '()':
                    roles.setdefault(spelling.casefold(), set()).add(kind)
    return roles


def excluded_metadata(path: Path) -> bool:
    parts = path.parts
    # Canonical maps, generated projections and compatibility/provenance tables
    # are read by their dedicated guards; they are not executable callsites.
    return ((len(parts) >= 3 and parts[:2] == ('lib', 'domains')
             and re.fullmatch(r'd(?:[1-9]|10|11)\.lisp', parts[-1]) is not None)
            or (len(parts) >= 3 and parts[:2] == ('lib', 'generated'))
            or path.as_posix() in {
                'lib/surface/semantic-registry.lisp',
                'lib/surface/semantic-registry-experiment.lisp',
                # Named policy and evidence documents; English keys are data,
                # not executable SENS call heads. Do not rewrite their ABI.
                'lib/island-math-evidence.lisp',
                'lib/machine/authority-boundary.lisp',
                # Документ сумісності, де старі SID8 є ключами рядків
                # машинного профілю, а не викликами SENS. Чинний
                # точнодоменний профіль — machine/profile/current-domain-x86-64.
                'lib/machine/intel-core-i5-6400.lisp',
            })


def measure(root: Path) -> dict:
    """Deterministic static evidence, separating live source from archive fixtures."""
    root = root.resolve()
    files = sorted(p for p in root.rglob('*.lisp') if '.git' not in p.parts)
    index, peers = peer_index(root)
    roles = peer_roles(root)
    latin, encoded, cyrillic, errors = [], [], 0, []
    full_ukr = compact_only = unknown_ukr = ambiguous_cyr = 0
    archive_latin = archive_encoded = archive_unclassified = 0
    active_latin = active_encoded = active_unclassified = 0
    active_cyrillic = active_ambiguous_cyr = 0
    active_full_ukr = active_compact_only = active_unknown_ukr = 0
    skipped = scanned = 0
    # Справжня файлова частка: лише активні .lisp зі здійснюваними головами.
    # Доменні таблиці, архіви, fixture і файли без викликів не в знаменнику.
    active_files_with_calls = active_files_full_ukr = 0
    active_files_mixed = active_files_no_ratified_ukr = 0
    for path in files:
        rel = path.relative_to(root)
        archival = (not rel.parts
                    or rel.parts[0] not in LIVE_SOURCE_DIRS
                    or 'tests' in rel.parts
                    or 'fixtures' in rel.parts
                    or (rel.parts[0] == 'examples' and 'history' in rel.parts))
        scope = 'archive/fixture' if archival else 'active'
        if excluded_metadata(rel):
            skipped += 1
            continue
        if path.is_symlink() or not path.resolve().is_relative_to(root):
            errors.append({'file': rel.as_posix(), 'reason': 'symlink/out-of-root source',
                           'scope': scope})
            archive_unclassified += int(archival)
            active_unclassified += int(not archival)
            if not archival:
                # Неможливий для читання активний файл — незавершений,
                # не викреслюємо його зі знаменника задля високого %.
                active_files_with_calls += 1
                active_files_no_ratified_ukr += 1
            continue
        scanned += 1
        try:
            forms = parse(path.read_text(encoding='utf-8'))
            file_heads = file_full = file_nonfull = 0
            for head in candidate_heads(forms):
                file_heads += 1
                if BIT_WORD.fullmatch(head.text) or ENCODED_HEAD.fullmatch(head.text):
                    file_nonfull += 1
                    encoded.append({'file': rel.as_posix(), 'line': head.line,
                                    'column': head.column, 'head': head.text,
                                    'scope': scope})
                    archive_encoded += int(archival)
                    active_encoded += int(not archival)
                elif LATIN.search(head.text):
                    file_nonfull += 1
                    candidates = index.get(head.text.casefold(), [])
                    latin.append({'file': rel.as_posix(), 'line': head.line,
                                  'column': head.column, 'head': head.text,
                                  'identities': candidates,
                                  'mapping': 'unique' if len(candidates) == 1
                                  else 'ambiguous' if candidates else 'unresolved',
                                  'scope': scope})
                    archive_latin += int(archival)
                    active_latin += int(not archival)
                elif UKRAINIAN.search(head.text):
                    if any(ch not in UKRAINIAN_KEYBOARD_OUTPUTS for ch in head.text):
                        file_nonfull += 1
                    cyrillic += 1
                    active_cyrillic += int(not archival)
                    spelling = head.text.casefold()
                    kinds = roles.get(spelling, set())
                    candidates = index.get(spelling, [])
                    if len(candidates) > 1:
                        file_nonfull += 1
                        ambiguous_cyr += 1
                        active_ambiguous_cyr += int(not archival)
                    elif 'укр' in kinds:
                        file_full += 1
                        full_ukr += 1
                        active_full_ukr += int(not archival)
                    elif 'ук' in kinds:
                        file_nonfull += 1
                        compact_only += 1
                        active_compact_only += int(not archival)
                    else:
                        # Локальні кириличні функції — окрема категорія, не
                        # прирівнюються без доказу до ратифікованої укр.
                        unknown_ukr += 1
                        active_unknown_ukr += int(not archival)
                else:
                    file_nonfull += 1
            if not archival and file_heads:
                active_files_with_calls += 1
                if not file_nonfull:
                    # Локальна кирилична функція допустима без власного
                    # ратифікованого domain-id, як і в головному звіті.
                    active_files_full_ukr += 1
                elif file_full:
                    active_files_mixed += 1
                else:
                    active_files_no_ratified_ukr += 1
        except (UnicodeError, OSError, SourceError, RecursionError) as exc:
            errors.append({'file': rel.as_posix(), 'reason': str(exc), 'scope': scope})
            archive_unclassified += int(archival)
            active_unclassified += int(not archival)
            if not archival:
                active_files_with_calls += 1
                active_files_no_ratified_ukr += 1
    total = len(latin) + cyrillic
    return {'files_total': len(files), 'files_scanned': scanned,
            'metadata_files_excluded': skipped,
            'ukr_call_heads': cyrillic, 'latin_call_heads': len(latin),
            'ukr_full_head_sites': full_ukr, 'uk_compact_only_head_sites': compact_only,
            'local_cyrillic_head_sites': unknown_ukr,
            'ambiguous_cyrillic_head_sites': ambiguous_cyr,
            'encoded_head_sites': encoded,
            'archival_latin_heads': archive_latin,
            'archival_encoded_head_sites': archive_encoded,
            'archival_unclassified_files': archive_unclassified,
            'active_latin_heads': active_latin,
            'active_encoded_head_sites': active_encoded,
            'active_unclassified_files': active_unclassified,
            'active_ukr_call_heads': active_cyrillic,
            'active_full_ukr_head_sites': active_full_ukr,
            'active_compact_only_head_sites': active_compact_only,
            'active_local_cyrillic_head_sites': active_unknown_ukr,
            'active_ambiguous_cyrillic_head_sites': active_ambiguous_cyr,
            'active_files_with_calls': active_files_with_calls,
            'active_files_full_ukr': active_files_full_ukr,
            'active_files_mixed': active_files_mixed,
            'active_files_no_ratified_ukr': active_files_no_ratified_ukr,
            'active_files_full_ukr_pct': (
                round(100 * active_files_full_ukr / active_files_with_calls, 1)
                if active_files_with_calls else 0.0
            ),
            'ukr_call_head_pct': round(100 * cyrillic / total, 1) if total else 0.0,
            'unclassified_files': errors, 'latin_sites': latin,
            'peer_index': peers,
            'authority_warning': 'lexical candidates only; no runtime F1-F4/peer-eq proof'}


def render(m: dict, *, limit: int = 15) -> str:
    lines = [
        f"УКР-ВИКЛИКИ: кириличних голів {m['ukr_call_heads']}, латинських "
        f"{m['latin_call_heads']} ({m['ukr_call_head_pct']}% укр); "
        f"оглянуто .lisp {m['files_scanned']}/{m['files_total']}",
        f"АКТИВНІ ФАЙЛИ на повній укр-проєкції: "
        f"{m['active_files_full_ukr']}/{m['active_files_with_calls']} "
        f"({m['active_files_full_ukr_pct']}%); "
        f"змішані={m['active_files_mixed']}, "
        f"без ратифікованої укр={m['active_files_no_ratified_ukr']}. "
        "Статична проєкція, не SENS-eval.",
        f"ACTIVE-SCOPE: Latin={m['active_latin_heads']}, encoded={m['active_encoded_head_sites']}, "
        f"ambiguous-укр={m['active_ambiguous_cyrillic_head_sites']}, "
        f"unclassified={m['active_unclassified_files']}, укр={m['active_ukr_call_heads']}",
        f"PEER-ІМЕНА: рядків {m['peer_index']['domain_rows']}; "
        f"законних відмінностей ук/укр "
        f"{m['peer_index']['valid_distinct_peer_spellings']} "
        f"(НЕ помилки міграції); неоднозначних spelling "
        f"{m['peer_index']['ambiguous_names']}",
        f"УКР-ВИДИ: full={m['ukr_full_head_sites']} "
        f"compact-only={m['uk_compact_only_head_sites']} "
        f"local={m['local_cyrillic_head_sites']} "
        f"ambiguous={m['ambiguous_cyrillic_head_sites']}; "
        f"архівних Latin={m['archival_latin_heads']}, "
        f"архівних encoded={m['archival_encoded_head_sites']}, "
        f"архівних syntax={m['archival_unclassified_files']}",
    ]
    ordered_latin = sorted(m['latin_sites'],
                           key=lambda site: (site['scope'] != 'active', site['file'],
                                             site['line'], site['column']))
    for site in ordered_latin[:limit]:
        found = ','.join(site['identities']) or '-'
        lines.append(f"LATIN {site['file']}:{site['line']}:{site['column']} "
                     f"{site['head']} mapping={site['mapping']} identity={found} scope={site['scope']}")
    if len(m['latin_sites']) > limit:
        lines.append(f"... додаткових латинських голів {len(m['latin_sites']) - limit}; "
                     "повний список доступний через --json")
    ordered_encoded = sorted(m['encoded_head_sites'],
                             key=lambda site: (site['scope'] != 'active', site['file'],
                                               site['line'], site['column']))
    for encoded in ordered_encoded[:limit]:
        lines.append(f"ENCODED {encoded['file']}:{encoded['line']}:"
                     f"{encoded['column']} {encoded['head']}: не українська назва scope={encoded['scope']}")
    ordered_errors = sorted(m['unclassified_files'],
                            key=lambda error: (error['scope'] != 'active', error['file']))
    for error in ordered_errors[:limit]:
        lines.append(f"UNCLASSIFIED {error['file']} "
                     f"scope={error['scope']}: {error['reason']}")
    return '\n'.join(lines)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--json', type=Path, help='write full deterministic JSON diagnostics')
    parser.add_argument('--limit', type=int, default=15)
    parser.add_argument('--require-full', action='store_true',
                        help='fail on active source call-head migration debt; archive findings remain visible')
    args = parser.parse_args(argv)
    if args.limit < 0:
        parser.error('--limit cannot be negative')
    m = measure(args.root)
    print(render(m, limit=args.limit))
    if args.json:
        args.json.write_text(json.dumps(m, ensure_ascii=False, indent=2) + '\n',
                             encoding='utf-8')
    # Strict checks apply to live source. Historical contracts, research,
    # benchmarks and tests stay fully indexed but do not become live entrypoints.
    # A compact ук peer is a valid projection, not a migration defect.
    red = bool(m['active_latin_heads'] or m['active_unclassified_files']
               or m['active_encoded_head_sites']
               or m['active_ambiguous_cyrillic_head_sites']
               or m['active_ukr_call_heads'] == 0)
    if args.require_full and red:
        print(f"::error::УКР-ВИКЛИКИ НЕ ЗАВЕРШЕНІ: "
              f"{m['active_latin_heads']} active Latin call heads, "
              f"{m['active_encoded_head_sites']} active encoded heads, "
              f"{m['active_ambiguous_cyrillic_head_sites']} ambiguous active Cyrillic heads, "
              f"{m['active_unclassified_files']} active unclassified .lisp files; "
              f"archive telemetry: Latin={m['archival_latin_heads']}, "
              f"syntax={m['archival_unclassified_files']}; "
              'valid compact ук peers are not errors', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
