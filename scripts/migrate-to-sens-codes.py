#!/usr/bin/env python3
"""Manifest-driven migration of S-expression source to current SENS exact-width words.

Two outputs are deliberately different:

1. --mirror
   Conservative source migration: rewrite only admitted executable call heads.
2. --binary-mirror
   Produce visible-binary SENS source:
   - D2 owns list structure: 10=open, 01=close, 11=dot, 00=separator;
   - executable admitted heads use their exact D3-D6 words;
   - remaining source spelling is encoded as D7/Text7 cells;
   - line comments and nested #|...|# comments are removed completely;
   - output contains only 0, 1 and ASCII whitespace;
   - files with unencodable spelling or unbalanced structure are blocked.

The binary mirror is source-word serialization, NOT the generic SW/FASL byte wire.
"""
from __future__ import annotations

import argparse
import ast
from dataclasses import dataclass, asdict
from hashlib import sha256
import json
from pathlib import Path
import re
import sys

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from domain_tables import read_domain_table
from sens_source_resolver import SourceResolver, build_resolver

CALL_DOMAINS = ("D3", "D4", "D5", "D6")
CONTRACT_CALL_DOMAINS = CALL_DOMAINS
CONTRACT_SURFACE_DOMAINS = ("D3", "D4", "D5", "D6", "D8", "D9")
CONTRACT_DOMAINS = ("D1", "D2", "D3", "D4", "D5", "D6", "D7", "D8", "D9")
LISP_EXTS = {".lisp", ".lsp", ".cl", ".scm", ".rkt", ".sens"}
BINARY_MASTER_EXTS = {".lisp"}
SKIP_DIRS = {
    ".git", ".hg", ".svn", "target", "node_modules", ".venv", "venv",
    "dist", "build", "__pycache__",
}

D2_OPEN = "10"
D2_CLOSE = "01"
D2_DOT = "11"
D2_SEPARATOR = "00"


@dataclass(frozen=True)
class Entry:
    domain: str
    width: int
    bits: str
    label: str
    authority: str


@dataclass(frozen=True)
class Hit:
    line: int
    column: int
    label: str
    bits: str
    domain: str


class BinaryMigrationError(ValueError):
    pass


def load_foundation(path: Path):
    raw = path.read_bytes()
    data = json.loads(raw)
    if data.get("status") != "owner-ratified":
        raise SystemExit(f"{path}: foundation is not owner-ratified")
    return data, sha256(raw).hexdigest()


def build_map(data, domains):
    out = {}
    for domain in domains:
        desc = data["domains"][domain]
        width = int(desc["width"])
        authority = str(desc.get("authority", data.get("authority", "unknown")))
        for bits, label in desc["residents"].items():
            if len(bits) != width or set(bits) - {"0", "1"}:
                raise SystemExit(f"{domain}: invalid exact-width word {bits}")
            key = str(label).upper()
            if key in out:
                raise SystemExit(f"duplicate label across selected domains: {key}")
            out[key] = Entry(domain, width, bits, str(label), authority)
    return out


def build_binary_authority(data, domains=CONTRACT_DOMAINS):
    """Index every ratified exact-domain coordinate without human-name authority."""
    out = {}
    for domain in domains:
        desc = data["domains"].get(domain)
        if desc is None:
            continue
        width = int(desc["width"])
        authority = str(desc.get("authority", data.get("authority", "unknown")))
        for bits, label in desc["residents"].items():
            if len(bits) != width or set(bits) - {"0", "1"}:
                raise BinaryMigrationError(
                    f"{domain}: invalid exact-width word {bits}"
                )
            key = (width, bits)
            if key in out:
                raise BinaryMigrationError(
                    f"duplicate exact binary coordinate: {domain}:{bits}"
                )
            out[key] = Entry(
                domain=domain,
                width=width,
                bits=bits,
                label=str(label),
                authority=authority,
            )
    return out


def validate_contract_binary_output(
    rendered: str,
    authority: dict[tuple[int, str], Entry],
    *,
    d1_enabled: bool,
    d9_enabled: bool,
) -> None:
    """Fail closed unless every emitted word is an admitted exact coordinate."""
    for word in rendered.split():
        if not re.fullmatch(r"[01]+", word):
            raise BinaryMigrationError(
                f"contract-authority output contains non-binary token {word!r}"
            )
        width = len(word)
        if width == 1:
            if not d1_enabled:
                raise BinaryMigrationError(
                    f"D1 word {word!r} requires GREEN exact-W1 reader support"
                )
            if (width, word) not in authority:
                raise BinaryMigrationError(
                    f"unadmitted D1 exact binary word {word!r}"
                )
            continue
        if width == 2:
            # D2 is the only structural exception to ordinary semantic residents.
            if (width, word) not in authority:
                raise BinaryMigrationError(
                    f"D2 structural word {word!r} is outside current authority"
                )
            continue
        if width == 9 and not d9_enabled:
            raise BinaryMigrationError(
                f"W9 word {word!r} requires GREEN exact-W9 reader/carrier support"
            )
        if (width, word) not in authority:
            raise BinaryMigrationError(
                f"unadmitted exact binary word {word!r} (width={width})"
            )


def _entry_index(code_map):
    out = {}
    for entry in code_map.values():
        out[(entry.domain, entry.bits)] = entry
    return out


def augment_code_map_with_domain_surfaces(code_map, paths):
    """Add exact human spellings from canonical per-domain tables."""
    by_identity = _entry_index(code_map)
    out = dict(code_map)
    for path in paths:
        for row in read_domain_table(path):
            entry = by_identity.get((row.domain, row.bits))
            if entry is None:
                continue
            for surface in (row.en, row.uk, row.ukr, row.san, row.lisp, row.sym):
                if not surface:
                    continue
                key = surface.upper()
                previous = out.get(key)
                if previous is not None and previous != entry:
                    raise BinaryMigrationError(
                        f"surface {surface!r} maps to both "
                        f"{previous.domain}:{previous.bits} and {entry.domain}:{entry.bits}"
                    )
                out[key] = entry
    return out


def _registry_rows(text):
    """Yield (sid8, fields) from one-row-per-line semantic-registry source."""
    field_re = re.compile(
        r'\((en|ук|укр|sa|sym)\s+("(?:\\.|[^"\\])*"|\(\)|[^()\s]+)\)'
    )
    for raw in text.splitlines():
        match = re.match(r'^\s*\(([01]{8})\s+(.*)\)\s*$', raw)
        if not match:
            continue
        sid = match.group(1)
        fields = []
        for namespace, raw_value in field_re.findall(match.group(2)):
            value = raw_value
            if value.startswith('"'):
                value = ast.literal_eval(value)
            fields.append((namespace, value))
        if fields:
            yield sid, fields


def augment_code_map_with_registry_aliases(code_map, registry_path):
    """Add UI aliases only after one exact-domain entry is independently known."""
    text = registry_path.read_text(encoding="utf-8")
    out = dict(code_map)

    normalized = {}
    for surface, entry in out.items():
        normalized.setdefault(normalize_legacy_surface(surface), set()).add(entry)

    for _sid, fields in _registry_rows(text):
        en_values = [value for ns, value in fields if ns == "en" and value != "()"]
        if len(en_values) != 1:
            continue
        candidates = normalized.get(normalize_legacy_surface(en_values[0]), set())
        if len(candidates) != 1:
            continue
        entry = next(iter(candidates))
        for _namespace, value in fields:
            if not value or value == "()":
                continue
            key = value.upper()
            previous = out.get(key)
            if previous is not None and previous != entry:
                continue
            out[key] = entry

    return out


def line_col(text, offset):
    line = text.count("\n", 0, offset) + 1
    last = text.rfind("\n", 0, offset)
    return line, offset + 1 if last < 0 else offset - last


def strip_comments(text: str) -> str:
    """Remove ; line comments and nested #|...|# comments, preserving strings."""
    out = []
    i = 0
    state = "normal"
    depth = 0
    while i < len(text):
        if state == "string":
            ch = text[i]
            out.append(ch)
            if ch == "\\" and i + 1 < len(text):
                out.append(text[i + 1])
                i += 2
            elif ch == '"':
                state = "normal"
                i += 1
            else:
                i += 1
            continue

        if state == "line":
            if text[i] == "\n":
                out.append("\n")
                state = "normal"
            i += 1
            continue

        if state == "block":
            if text.startswith("#|", i):
                depth += 1
                i += 2
            elif text.startswith("|#", i):
                depth -= 1
                i += 2
                if depth == 0:
                    state = "normal"
            else:
                if text[i] == "\n":
                    out.append("\n")
                i += 1
            continue

        if text[i] == '"':
            out.append(text[i])
            state = "string"
            i += 1
        elif text[i] == ";":
            state = "line"
            i += 1
        elif text.startswith("#|", i):
            state = "block"
            depth = 1
            i += 2
        else:
            out.append(text[i])
            i += 1

    if state == "block":
        raise BinaryMigrationError("unterminated block comment")
    if state == "string":
        raise BinaryMigrationError("unterminated string")
    return "".join(out)


def mask_comments_and_strings(text):
    chars = list(text)
    i = 0
    state = "normal"
    depth = 0
    while i < len(text):
        if state == "string":
            if text[i] == "\\" and i + 1 < len(text):
                chars[i] = chars[i + 1] = " "
                i += 2
            elif text[i] == '"':
                chars[i] = " "
                state = "normal"
                i += 1
            else:
                if text[i] != "\n":
                    chars[i] = " "
                i += 1
            continue
        if state == "line":
            if text[i] == "\n":
                state = "normal"
            else:
                chars[i] = " "
            i += 1
            continue
        if state == "block":
            if text.startswith("#|", i):
                chars[i:i + 2] = [" ", " "]
                depth += 1
                i += 2
            elif text.startswith("|#", i):
                chars[i:i + 2] = [" ", " "]
                depth -= 1
                i += 2
                if depth == 0:
                    state = "normal"
            else:
                if text[i] != "\n":
                    chars[i] = " "
                i += 1
            continue
        if text[i] == '"':
            chars[i] = " "
            state = "string"
            i += 1
        elif text[i] == ";":
            chars[i] = " "
            state = "line"
            i += 1
        elif text.startswith("#|", i):
            chars[i:i + 2] = [" ", " "]
            state = "block"
            depth = 1
            i += 2
        else:
            i += 1
    return "".join(chars)


def shadowing(text, code_map):
    masked = mask_comments_and_strings(text)
    pattern = re.compile(r"(?i)\(\s*(defun|defmacro|defgeneric|defmethod)\s+([^\s()]+)")
    rows = []
    for match in pattern.finditer(masked):
        label = match.group(2).upper()
        if label in code_map:
            line, col = line_col(text, match.start(2))
            rows.append({
                "line": line,
                "column": col,
                "label": label,
                "kind": match.group(1).upper(),
            })
    return rows


def symbol_char(ch):
    return (not ch.isspace()) and ch not in "()\";',"


def rewrite(text, code_map):
    """Legacy conservative rewrite used by --mirror and audit mode."""
    blocked = shadowing(text, code_map)
    if blocked:
        return text, [], blocked

    frames = []
    out = []
    hits = []
    i = 0
    pending_quote = False

    while i < len(text):
        ch = text[i]
        if ch == '"':
            start = i
            i += 1
            while i < len(text):
                if text[i] == "\\" and i + 1 < len(text):
                    i += 2
                elif text[i] == '"':
                    i += 1
                    break
                else:
                    i += 1
            out.append(text[start:i])
            pending_quote = False
            continue
        if ch == ";":
            end = text.find("\n", i)
            if end < 0:
                out.append(text[i:])
                break
            out.append(text[i:end])
            i = end
            continue
        if text.startswith("#|", i):
            start = i
            i += 2
            depth = 1
            while i < len(text) and depth:
                if text.startswith("#|", i):
                    depth += 1
                    i += 2
                elif text.startswith("|#", i):
                    depth -= 1
                    i += 2
                else:
                    i += 1
            out.append(text[start:i])
            continue
        if text.startswith("#'", i):
            out.append("#'")
            i += 2
            pending_quote = True
            continue
        if ch == "'" or ord(ch) == 96:
            out.append(ch)
            i += 1
            pending_quote = True
            continue
        if ch == ",":
            out.append(ch)
            i += 1
            pending_quote = True
            if i < len(text) and text[i] == "@":
                out.append("@")
                i += 1
            continue
        if ch == "(":
            parent_quoted = bool(frames and (frames[-1]["quoted"] or frames[-1]["quote_children"]))
            if frames and frames[-1]["head"]:
                frames[-1]["head"] = False
            frames.append({
                "quoted": parent_quoted or pending_quote,
                "head": True,
                "quote_children": False,
            })
            out.append(ch)
            i += 1
            pending_quote = False
            continue
        if ch == ")":
            if frames:
                frames.pop()
            out.append(ch)
            i += 1
            pending_quote = False
            continue
        if ch.isspace():
            out.append(ch)
            i += 1
            continue

        start = i
        while i < len(text) and symbol_char(text[i]) and ord(text[i]) != 96:
            if text.startswith("#|", i):
                break
            i += 1
        token = text[start:i]
        if not token:
            out.append(text[i])
            i += 1
            continue

        frame = frames[-1] if frames else None
        is_head = bool(frame and frame["head"])
        quoted = pending_quote or bool(frame and (frame["quoted"] or frame["quote_children"]))
        upper = token.upper()
        entry = code_map.get(upper)
        replacement = token
        if is_head and not quoted and entry and ":" not in token:
            replacement = entry.bits
            line, col = line_col(text, start)
            hits.append(Hit(line, col, entry.label, entry.bits, entry.domain))
        out.append(replacement)
        if frame and frame["head"]:
            frame["head"] = False
            if upper == "QUOTE":
                frame["quote_children"] = True
        pending_quote = False

    return "".join(out), hits, blocked


def _extract_projection(text: str, name: str) -> dict[str, tuple[int, ...]]:
    marker = f"pub(crate) const {name}"
    start = text.find(marker)
    if start < 0:
        raise BinaryMigrationError(f"missing Text7 projection {name}")
    end = text.find("];", start)
    if end < 0:
        raise BinaryMigrationError(f"unterminated Text7 projection {name}")
    section = text[start:end]
    result = {}
    row = re.compile(r'^\s*\(("(?:\\.|[^"\\])*"),\s*Some\(&\[([^\]]*)\]\)\)', re.M)
    for match in row.finditer(section):
        spelling = ast.literal_eval(match.group(1))
        values = tuple(int(x.strip(), 16) for x in match.group(2).split(",") if x.strip())
        result[spelling] = values
    if not result:
        raise BinaryMigrationError(f"empty Text7 projection {name}")
    return result


def normalize_legacy_surface(name: str) -> str:
    # Preserve * because LET and LET* are distinct. Drop only punctuation
    # that is surface decoration rather than semantic spelling.
    return name.strip().lower().rstrip("?").replace("-", "")


def build_legacy_sid_map(registry_path: Path, code_map):
    text = registry_path.read_text(encoding="utf-8")

    by_surface = {}
    for surface, entry in code_map.items():
        by_surface.setdefault(normalize_legacy_surface(surface), set()).add(entry)

    out = {}
    for sid, fields in _registry_rows(text):
        en_values = [value for ns, value in fields if ns == "en" and value != "()"]
        if len(en_values) != 1:
            continue
        candidates = by_surface.get(normalize_legacy_surface(en_values[0]), set())
        if len(candidates) == 1:
            out[sid] = next(iter(candidates))

    return out


def build_registry_surface_sid_map(registry_path: Path):
    """Map every admitted human/symbol surface spelling to its 8-bit function code."""
    text = registry_path.read_text(encoding="utf-8")
    out = {}
    for sid, fields in _registry_rows(text):
        for _namespace, value in fields:
            if not value or value == "()":
                continue
            key = value.upper()
            previous = out.get(key)
            if previous is not None and previous != sid:
                raise BinaryMigrationError(
                    f"registry surface {value!r} maps to both {previous} and {sid}"
                )
            out[key] = sid
    return out


def build_text7_encoder(foundation, generated_projection: Path):
    generated = generated_projection.read_text(encoding="utf-8")
    slp = _extract_projection(generated, "SA_SLP1_ENCODE")
    iast = _extract_projection(generated, "SA_IAST_ENCODE")
    deva = _extract_projection(generated, "SA_DEVA_ENCODE")
    uk = _extract_projection(generated, "UK_ENCODE")

    d7 = foundation["domains"]["D7"]["residents"]
    by_label = {label: bits for bits, label in d7.items()}

    digits = {
        str(n): by_label[f"text.digit.{n}"]
        for n in range(10)
    }
    punctuation_labels = {
        " ": "sign.space",
        "\n": "sign.newline",
        "\t": "sign.tab",
        "!": "sign.bang",
        '"': "sign.double-quote",
        "#": "sign.hash",
        "&": "sign.ampersand",
        "'": "sign.apostrophe",
        "(": "sign.left-paren",
        ")": "sign.right-paren",
        "*": "sign.star",
        "+": "sign.plus",
        ",": "sign.comma",
        "-": "sign.minus",
        ".": "sign.dot",
        "/": "sign.slash",
        ":": "sign.colon",
        ";": "sign.semicolon",
        "<": "sign.less",
        "=": "sign.equals",
        ">": "sign.greater",
        "?": "sign.question",
        "@": "sign.at",
        "\\": "sign.backslash",
        "_": "sign.underscore",
        "`": "sign.backquote",
        "|": "sign.pipe",
        "…": "text.punctuation.ellipsis",
        "«": "text.punctuation.left-guillemet",
        "»": "text.punctuation.right-guillemet",
        "—": "text.punctuation.em-dash",
        "–": "text.punctuation.en-dash",
        "“": "text.punctuation.left-double-quotation-mark",
        "”": "text.punctuation.right-double-quotation-mark",
    }
    punctuation = {ch: by_label[label] for ch, label in punctuation_labels.items()}

    # Latin letters use the pinned SLP1 projection. Cyrillic uses pinned UK.
    latin = {
        k: tuple(f"{v:07b}" for v in vals)
        for k, vals in slp.items()
        if k.isalpha() and all(ord(ch) < 128 for ch in k)
    }
    iast_unicode = {
        k: tuple(f"{v:07b}" for v in vals)
        for k, vals in iast.items()
        if any(ord(ch) >= 128 for ch in k)
    }
    deva_unicode = {
        k: tuple(f"{v:07b}" for v in vals)
        for k, vals in deva.items()
        if any(ord(ch) >= 128 for ch in k)
    }
    cyrillic = {
        k: tuple(f"{v:07b}" for v in vals)
        for k, vals in uk.items()
        if any(ord(ch) >= 128 for ch in k)
    }

    candidates = {}
    candidates.update({k: (bits,) for k, bits in digits.items()})
    candidates.update({k: (bits,) for k, bits in punctuation.items()})
    candidates.update(latin)
    candidates.update(iast_unicode)
    candidates.update(deva_unicode)
    candidates.update(cyrillic)

    # Longest spelling first: e.g. Ukrainian дж/дз must stay one Text7 cell.
    ordered = sorted(candidates.items(), key=lambda item: (-len(item[0]), item[0]))
    return ordered


def encode_text7_spelling(text: str, candidates):
    words = []
    i = 0
    while i < len(text):
        for spelling, cells in candidates:
            if text.startswith(spelling, i):
                words.extend(cells)
                i += len(spelling)
                break
        else:
            ch = text[i]
            raise BinaryMigrationError(
                f"Text7 has no admitted spelling for {ch!r} U+{ord(ch):04X}"
            )
    return words


def _emit_item(out, words, need_separator):
    if need_separator and out and out[-1] not in (D2_OPEN, D2_SEPARATOR):
        out.append(D2_SEPARATOR)
    out.extend(words)


def resolve_contract_binary_token(
    token: str,
    *,
    binary_authority: dict[tuple[int, str], Entry],
    d1_enabled: bool,
    d9_enabled: bool,
) -> str:
    """Resolve one already-binary data token under Contract 11.8 authority."""
    width = len(token)
    if width == 1:
        if not d1_enabled:
            raise BinaryMigrationError(
                f"D1 word {token!r} requires GREEN exact-W1 reader support"
            )
        if (width, token) not in binary_authority:
            raise BinaryMigrationError(
                f"unadmitted D1 exact binary word {token!r}"
            )
    if width == 9 and not d9_enabled:
        raise BinaryMigrationError(
            f"W9 word {token!r} requires GREEN exact-W9 reader/carrier support"
        )

    exact = binary_authority.get((width, token))
    if exact is not None:
        if width == 2:
            raise BinaryMigrationError(
                f"D2 word {token!r} is structural control only"
            )

        # In Contract-authority mode a bare exact binary word is already canonical.
        # Historical SID8 evidence is never allowed to reinterpret it here.
        return token

    raise BinaryMigrationError(
        f"unadmitted exact binary word {token!r}"
    )


def resolve_binary_executable_head(
    token: str,
    *,
    contract_authority: bool,
    resolver: SourceResolver | None,
    binary_authority: dict[tuple[int, str], Entry],
) -> Entry:
    """Resolve a callable head without allowing width to mint callability."""
    if contract_authority and re.fullmatch(r"[01]+", token):
        identity = binary_authority.get((len(token), token))
        if identity is None:
            raise BinaryMigrationError(
                f"unadmitted exact binary executable head {token!r}"
            )
        return identity

    if resolver is None:
        raise BinaryMigrationError(
            "history-aware SourceResolver is required for binary migration"
        )

    resolution = resolver.resolve_head(token)
    if not resolution.resolved:
        detail = (
            ", ".join(resolution.ambiguous)
            if resolution.ambiguous
            else "no proven current exact-domain identity"
        )
        raise BinaryMigrationError(
            f"unresolved executable head {token!r}: "
            f"{resolution.kind}; {detail}"
        )

    identity = resolution.current
    assert identity is not None
    return identity


def binary_rewrite(
    text,
    code_map,
    text7_candidates,
    legacy_sid_map=None,
    registry_surface_sid_map=None,
    resolver: SourceResolver | None = None,
    *,
    contract_authority: bool = False,
    binary_authority: dict[tuple[int, str], Entry] | None = None,
    d1_enabled: bool = False,
    d9_enabled: bool = False,
):
    """Encode one source file as exact-width visible binary SENS words."""
    source = strip_comments(text)
    shadowed = {row["label"] for row in shadowing(source, code_map)}
    legacy_sid_map = legacy_sid_map or {}
    registry_surface_sid_map = registry_surface_sid_map or {}
    current_words = {
        (entry.width, entry.bits): entry
        for entry in code_map.values()
    }
    binary_authority = binary_authority or {}

    out = []
    hits = []
    frames = []
    i = 0
    pending_quote = False
    top_has_item = False

    def current_quoted():
        if pending_quote:
            return True
        return bool(frames and (frames[-1]["quoted"] or frames[-1]["quote_children"]))

    def begin_item():
        nonlocal top_has_item
        if frames:
            frame = frames[-1]
            need = frame["items"] > 0
            if need and (not out or out[-1] != D2_SEPARATOR):
                out.append(D2_SEPARATOR)
            frame["items"] += 1
            return
        if top_has_item and (not out or out[-1] != D2_SEPARATOR):
            out.append(D2_SEPARATOR)
        top_has_item = True

    while i < len(source):
        ch = source[i]

        if ch.isspace():
            i += 1
            continue

        if ch == "(":
            # Canonical empty list is D3 EMPTY=000, not OPEN+CLOSE.
            j = i + 1
            while j < len(source) and source[j].isspace():
                j += 1
            if j < len(source) and source[j] == ")":
                begin_item()
                out.append("000")
                i = j + 1
                pending_quote = False
                continue

            begin_item()
            parent_quoted = bool(frames and (frames[-1]["quoted"] or frames[-1]["quote_children"]))
            frames.append({
                "quoted": parent_quoted or pending_quote,
                "head": True,
                "quote_children": False,
                "items": 0,
            })
            out.append(D2_OPEN)
            i += 1
            pending_quote = False
            continue

        if ch == ")":
            if not frames:
                raise BinaryMigrationError("unexpected closing parenthesis")
            frames.pop()
            out.append(D2_CLOSE)
            i += 1
            pending_quote = False
            continue

        if ch == '"':
            begin_item()
            start = i
            i += 1
            while i < len(source):
                if source[i] == "\\" and i + 1 < len(source):
                    i += 2
                elif source[i] == '"':
                    i += 1
                    break
                else:
                    i += 1
            else:
                raise BinaryMigrationError("unterminated string")
            token = source[start:i]
            # Quoted digits are ordinary Text7 string data.  Only an unquoted
            # binary source word may carry exact domain identity.
            out.extend(encode_text7_spelling(token, text7_candidates))
            if frames and frames[-1]["head"]:
                frames[-1]["head"] = False
            pending_quote = False
            continue

        # Reader abbreviations stay spelling, but are now D7 cells.
        if source.startswith("#'", i):
            begin_item()
            out.extend(encode_text7_spelling("#'", text7_candidates))
            i += 2
            pending_quote = True
            continue
        if ch in ("'", "`"):
            begin_item()
            out.extend(encode_text7_spelling(ch, text7_candidates))
            i += 1
            pending_quote = True
            continue
        if ch == ",":
            begin_item()
            token = ",@" if i + 1 < len(source) and source[i + 1] == "@" else ","
            out.extend(encode_text7_spelling(token, text7_candidates))
            i += len(token)
            pending_quote = True
            continue

        # Standalone dotted-pair marker belongs to D2, not Text7.
        if ch == ".":
            before_ok = i == 0 or source[i - 1].isspace() or source[i - 1] == "("
            after_ok = i + 1 == len(source) or source[i + 1].isspace() or source[i + 1] == ")"
            if before_ok and after_ok:
                begin_item()
                out.append(D2_DOT)
                i += 1
                pending_quote = False
                continue

        start = i
        while i < len(source):
            if source[i].isspace() or source[i] in "()\";',":
                break
            if source.startswith("#|", i):
                break
            i += 1
        token = source[start:i]
        if not token:
            raise BinaryMigrationError(f"cannot tokenize character {source[i]!r} at offset {i}")

        if contract_authority and re.fullmatch(r"(?i)#b[01]+", token):
            raise BinaryMigrationError(
                f"legacy #b binary wrapper {token!r} is not canonical source"
            )

        begin_item()
        frame = frames[-1] if frames else None
        is_head = bool(frame and frame["head"])
        quoted = current_quoted()
        resolved_label = None

        if is_head and not quoted:
            identity = resolve_binary_executable_head(
                token,
                contract_authority=contract_authority,
                resolver=resolver,
                binary_authority=binary_authority,
            )
            if contract_authority and identity.domain not in CONTRACT_CALL_DOMAINS:
                raise BinaryMigrationError(
                    f"non-callable authority resident used as executable head: "
                    f"{identity.domain}:{identity.bits}"
                )
            if identity.label == "EMPTY":
                raise BinaryMigrationError(
                    "structural EMPTY/000 cannot be used as a callable head"
                )

            out.append(identity.bits)
            resolved_label = identity.label
            line, col = line_col(source, start)
            hits.append(Hit(
                line,
                col,
                identity.label,
                identity.bits,
                identity.domain,
            ))
        else:
            # In contract-authority mode, a bare binary word is already canonical
            # source.  Keep its exact width instead of spelling its digits as D7.
            if contract_authority and re.fullmatch(r"[01]+", token):
                out.append(
                    resolve_contract_binary_token(
                        token,
                        binary_authority=binary_authority,
                        d1_enabled=d1_enabled,
                        d9_enabled=d9_enabled,
                    )
                )
            # Explicit legacy SID values are semantic identities even outside a
            # call head; migrate them by named historical evidence rather than
            # spelling their eight digits as Text7.
            elif re.fullmatch(r"[01]{8}", token):
                if resolver is None:
                    raise BinaryMigrationError(
                        "history-aware SourceResolver is required for SID data migration"
                    )
                resolution = resolver.resolve_head(token)
                if not resolution.resolved:
                    raise BinaryMigrationError(
                        f"unresolved legacy SID value {token!r}"
                    )
                identity = resolution.current
                assert identity is not None
                out.append(identity.bits)
            elif re.fullmatch(
                r"[+-]?(?:[0-9]+(?:[.,][0-9]*)?|[.,][0-9]+)"
                r"(?:[eE][+-]?[0-9]+)?(?:/[0-9]+)?",
                token,
            ):
                raise BinaryMigrationError(
                    f"numeric literal {token!r} belongs to Number, not Text7; "
                    "ratified Number widths are 24 -> 48 -> 96 -> ...; "
                    "numeric lowering is not yet supplied by this migration"
                )
            else:
                out.extend(encode_text7_spelling(token, text7_candidates))

        if frame and frame["head"]:
            frame["head"] = False
            if resolved_label == "QUOTE":
                frame["quote_children"] = True
        pending_quote = False

    if frames:
        raise BinaryMigrationError("unterminated list")

    # Collapse accidental duplicate separators and never leave edge separators.
    compact = []
    for word in out:
        if word == D2_SEPARATOR and (not compact or compact[-1] in (D2_OPEN, D2_SEPARATOR)):
            continue
        if word == D2_CLOSE and compact and compact[-1] == D2_SEPARATOR:
            compact.pop()
        compact.append(word)
    while compact and compact[-1] == D2_SEPARATOR:
        compact.pop()

    rendered = " ".join(compact)
    if rendered:
        rendered += "\n"
    if rendered and (set(rendered) - {"0", "1", " ", "\n", "\t", "\r"}):
        raise AssertionError("binary migration emitted a non-binary source character")
    if contract_authority:
        validate_contract_binary_output(
            rendered,
            binary_authority,
            d1_enabled=d1_enabled,
            d9_enabled=d9_enabled,
        )
    return rendered, hits, sorted(shadowed)


def source_files(root, binary_master=False):
    exts = BINARY_MASTER_EXTS if binary_master else LISP_EXTS
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.suffix.lower() in exts:
            yield path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path, help="repository or source tree")
    parser.add_argument("--foundation", type=Path, required=True)
    parser.add_argument("--domains", nargs="+", default=list(CALL_DOMAINS))
    parser.add_argument(
        "--contract-authority",
        action="store_true",
        help="strict current Contract 11.8 binary-source authority mode",
    )
    parser.add_argument("--apply", action="store_true", help="rewrite supported source in place")
    parser.add_argument("--mirror", type=Path, help="write conservative migrated mirror")
    parser.add_argument(
        "--binary-mirror",
        type=Path,
        help="write comment-free exact-width visible-binary SENS source mirror",
    )
    parser.add_argument(
        "--text7-projection",
        type=Path,
        default=Path("crates/sens/src/text7_projection_generated.rs"),
        help="generated pinned Text7 projection used by --binary-mirror",
    )
    parser.add_argument(
        "--historical-map",
        type=Path,
        default=Path("contracts/core1-historical-sid-map.lisp"),
        help="historical SID8/my-lisp/Lisp-I/1.5 transition evidence",
    )
    parser.add_argument(
        "--semantic-registry",
        type=Path,
        default=Path("lib/surface/semantic-registry.lisp"),
        help="pinned legacy SID8 surface registry used only for exact D3-D6 migration",
    )
    parser.add_argument(
        "--domain-surfaces",
        type=Path,
        nargs="*",
        default=[Path(f"lib/domains/d{width}.lisp") for width in range(1, 7)],
        help="exact-domain surface projection files used to recognize function spellings",
    )
    parser.add_argument("--report", type=Path, default=Path("sens-code-migration-report.json"))
    args = parser.parse_args()

    selected_modes = sum(bool(x) for x in (args.apply, args.mirror, args.binary_mirror))
    if selected_modes > 1:
        parser.error("--apply, --mirror and --binary-mirror are mutually exclusive")
    if args.contract_authority and (args.apply or args.mirror):
        parser.error("--contract-authority is only valid with --binary-mirror")
    if args.contract_authority and not args.binary_mirror:
        parser.error("--contract-authority requires --binary-mirror")

    foundation, digest = load_foundation(args.foundation)
    # Contract-authority mode is intentionally stacked on tested W1/W9 reader
    # ancestry (#4292 on the merged #4258 W9 main cut).  Capability is a release
    # prerequisite, never inferred from grep-able implementation text.
    d1_enabled = bool(args.contract_authority)
    d9_enabled = bool(args.contract_authority)
    selected_domains = list(args.domains)
    selected_surfaces = list(args.domain_surfaces)
    current_resolver_domains = tuple(dict.fromkeys(selected_domains))
    if args.contract_authority:
        # Only already-callable domains may enter the human/source-head map.
        # D8/D9 remain resolver evidence so attempted executable use can fail
        # named/non-callable, while semantic membership itself is owned by the
        # exact (width,bits) binary_authority below.
        selected_domains = list(CONTRACT_CALL_DOMAINS)
        selected_surfaces.extend(
            path
            for path in (
                Path("lib/domains/d8.lisp"),
                Path("lib/domains/d9.lisp"),
            )
            if path not in selected_surfaces and path.exists()
        )
        current_resolver_domains = tuple(CONTRACT_SURFACE_DOMAINS)
    code_map = build_map(foundation, selected_domains)
    code_map = augment_code_map_with_domain_surfaces(code_map, selected_surfaces)
    if not args.contract_authority:
        code_map = augment_code_map_with_registry_aliases(
            code_map,
            args.semantic_registry,
        )
    resolver = build_resolver(
        historical_map=args.historical_map,
        foundation=args.foundation,
        registry=args.semantic_registry,
        domain_surfaces=selected_surfaces,
        current_domains=current_resolver_domains,
        prefer_current_surface=args.contract_authority,
    )
    binary_authority = (
        build_binary_authority(
            foundation,
            CONTRACT_DOMAINS if d9_enabled else tuple(
                domain for domain in CONTRACT_DOMAINS if domain != "D9"
            ),
        )
        if args.contract_authority
        else {}
    )
    text7_candidates = (
        build_text7_encoder(foundation, args.text7_projection)
        if args.binary_mirror
        else None
    )
    legacy_sid_map = (
        build_legacy_sid_map(args.semantic_registry, code_map)
        if args.binary_mirror
        else None
    )
    registry_surface_sid_map = (
        build_registry_surface_sid_map(args.semantic_registry)
        if args.binary_mirror
        else None
    )

    root = args.root.resolve()
    rows = []
    rewritten_files = 0
    blocked_files = 0
    total_hits = 0

    for path in source_files(root, binary_master=bool(args.binary_mirror)):
        text = path.read_text(encoding="utf-8")
        rel = path.relative_to(root)

        if args.binary_mirror:
            try:
                converted, hits, shadowed = binary_rewrite(
                    text,
                    code_map,
                    text7_candidates,
                    legacy_sid_map,
                    registry_surface_sid_map,
                    resolver,
                    contract_authority=args.contract_authority,
                    binary_authority=binary_authority,
                    d1_enabled=d1_enabled,
                    d9_enabled=d9_enabled,
                )
                if not converted.strip():
                    status = "empty"
                else:
                    target = args.binary_mirror / rel
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_text(converted, encoding="ascii")
                    status = "binary-mirrored"
                    rewritten_files += 1
                total_hits += len(hits)
                blocked = []
            except BinaryMigrationError as error:
                converted = ""
                hits = []
                shadowed = []
                blocked = [{"reason": str(error)}]
                status = "blocked"
                blocked_files += 1
        else:
            converted, hits, blocked = rewrite(text, code_map)
            shadowed = [row["label"] for row in blocked]
            status = "clean"
            if blocked:
                status = "blocked"
                blocked_files += 1
            elif hits:
                status = "would-rewrite"
                total_hits += len(hits)
                if args.apply:
                    path.write_text(converted, encoding="utf-8")
                    status = "rewritten"
                    rewritten_files += 1
                elif args.mirror:
                    target = args.mirror / rel
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_text(converted, encoding="utf-8")
                    status = "mirrored"
                    rewritten_files += 1

        rows.append({
            "path": str(rel),
            "status": status,
            "hits": [asdict(x) for x in hits],
            "shadowed_labels": shadowed,
            "blockers": blocked,
        })

    mode = (
        "apply" if args.apply
        else "mirror" if args.mirror
        else "binary-mirror" if args.binary_mirror
        else "audit"
    )
    report = {
        "foundation_schema": foundation.get("schema"),
        "foundation_authority": foundation.get("authority"),
        "foundation_date": foundation.get("date"),
        "foundation_sha256": digest,
        "identity_rule": foundation.get("identity_rule"),
        "domains": args.domains,
        "root": str(root),
        "mode": mode,
        "binary_source_rule": (
            "D2 + exact current-domain words + D7/Text7; "
            "D1 waits for W1 reader support; comments absent"
            if args.binary_mirror and args.contract_authority
            else (
                "D2 structure + exact D3-D6 callable heads + D7/Text7 spelling; "
                "comments absent"
            )
            if args.binary_mirror else None
        ),
        "contract_authority": args.contract_authority,
        "w9_enabled": d9_enabled,
        "summary": {
            "files_seen": len(rows),
            "files_written": rewritten_files,
            "files_blocked": blocked_files,
            "rewritable_call_heads": total_hits,
        },
        "files": rows,
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report["summary"], ensure_ascii=False))

    if args.binary_mirror:
        return 0 if rewritten_files else 2
    return 2 if blocked_files else (1 if total_hits and not (args.apply or args.mirror) else 0)


if __name__ == "__main__":
    raise SystemExit(main())
