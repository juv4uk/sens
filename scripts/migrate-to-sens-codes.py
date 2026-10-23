#!/usr/bin/env python3
"""Manifest-driven migration of S-expression source to current SENS exact-width words.

Two outputs are deliberately different:

1. --mirror
   Conservative source migration: rewrite only admitted executable call heads.
2. --sens-mirror (NEW canonical migration destination)
   Preserve the input name, replacing .lisp with .sens, and write real
   physically packed T5M bytes via pinned Zig; block non-binary leftovers; no overwrite.
3. --binary-mirror (legacy staging ONLY, NEVER a .sens deliverable)
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
import os
import tempfile
from sens_t5_codec import (
    SensT5Error, encode_t5m_projection, decode_t5m_bytes,
    parse_t5m_words, typed_sha256,
)

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from domain_tables import read_domain_table
import zig_codec_bridge
from sens_source_resolver import SourceResolver, build_resolver

CALL_DOMAINS = ("D3", "D4", "D5", "D6")
LISP_EXTS = {".lisp", ".lsp", ".cl", ".scm", ".rkt"}  # .sens is packed BYTES, NEVER text
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
    # No old phonetic SLP1/IAST .rs tables, no v1 resident imports.
    if generated_projection.suffix != ".json":
        raise BinaryMigrationError(
            "HISTORICAL_D7_DISABLED: only ratified keyboard/v2 JSON is admitted"
        )
    authority = json.loads(generated_projection.read_text(encoding="utf-8"))
    if (authority.get("schema"), authority.get("status"),
            authority.get("width"), authority.get("capacity"),
            authority.get("occupancy")) != (
            "sens.d7.keyboard/v2", "owner-ratified", 7, 128, 128):
        raise BinaryMigrationError("D7 keyboard/v2 owner authority invalid")
    rows = authority.get("table", [])
    if len(rows) != 128:
        raise BinaryMigrationError("D7 keyboard/v2 requires 128 W7 cells")
    maps = {mode: {} for mode in ("en", "uk", "san")}
    for number, item in enumerate(rows):
        bits = f"{number:07b}"
        if item.get("bits") != bits or item.get("ascii") != chr(number):
            raise BinaryMigrationError(f"D7 keyboard/v2 coordinate drift: {bits}")
        for mode, field in (("en", "ascii"), ("uk", "uk"), ("san", "san")):
            glyph = item.get(field)
            if not isinstance(glyph, str) or len(glyph) != 1 or glyph in maps[mode]:
                raise BinaryMigrationError(f"D7 keyboard/v2 ambiguous {mode} glyph: {bits}")
            maps[mode][glyph] = bits
    return {"d7-keyboard/v2": maps}


def encode_text7_spelling(text: str, candidates):
    if isinstance(candidates, dict) and "d7-keyboard/v2" in candidates:
        if not text:
            raise BinaryMigrationError("D7 keyboard/v2 empty identifier")
        modes = set()
        for ch in text:
            number = ord(ch)
            if ("a" <= ch <= "z") or ("A" <= ch <= "Z"):
                modes.add("en")
            elif 0x0400 <= number <= 0x052F:
                modes.add("uk")
            elif 0x0900 <= number <= 0x097F:
                modes.add("san")
            elif ch.isalpha():
                raise BinaryMigrationError(f"D7 keyboard/v2 unsupported script {ch!r}")
        if len(modes) > 1:
            raise BinaryMigrationError("D7 keyboard/v2 mixed-script identifier")
        view = next(iter(modes), "en")
        index = candidates["d7-keyboard/v2"][view]
        cells = []
        for glyph in text:
            word = index.get(glyph)
            if word is None:
                raise BinaryMigrationError(
                    f"D7 keyboard/v2 cannot encode {glyph!r} U+{ord(glyph):04X} in {view}"
                )
            cells.append(word)
        return cells
    raise BinaryMigrationError("HISTORICAL_D7_DISABLED: expected keyboard/v2 projection")


def _emit_item(out, words, need_separator):
    if need_separator and out and out[-1] not in (D2_OPEN, D2_SEPARATOR):
        out.append(D2_SEPARATOR)
    out.extend(words)


def seed_forward_definitions(source: str, code_map: dict[str, Entry]) -> set[str]:
    """Seed known D4 DEFINE binders through the ratified exact-width surfaces.

    In particular, full Ukrainian `визначити` must resolve mutual/forward
    references just like the historic DEFINE spelling. Source spelling does
    not invent a new identity: every admitted spelling belongs to D4:0011.
    """
    definitions = sorted(
        (surface for surface, entry in code_map.items()
         if entry.domain == "D4" and entry.bits == "0011"),
        key=len, reverse=True,
    )
    if not definitions:
        raise BinaryMigrationError("D4:0011 DEFINE missing from ratified domain projection")
    pattern = r"\(\s*(?:" + "|".join(re.escape(x) for x in definitions) + r")\s+([^\s()]+)"
    return set(re.findall(pattern, source, flags=re.IGNORECASE))


def binary_rewrite(
    text,
    code_map,
    text7_candidates,
    legacy_sid_map=None,
    registry_surface_sid_map=None,
    resolver: SourceResolver | None = None,
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

    out = []
    hits = []
    frames = []
    i = 0
    pending_quote = False
    top_has_item = False
    # Only names introduced by an admitted DEFINE or D4 LAMBDA parameter
    # become contextual D2-framed D7 identifiers. Never guess that an
    # arbitrary quoted/data D7 list is a source symbol or String.
    #
    # Forward references (mutual recursion): a symbol that the source itself
    # introduces with an admitted DEFINE is a legal call head even before its
    # defining form is reached. Seed the binding set from the source so only
    # those names are admitted; every other unbound head stays fail-closed.
    global_bindings: set[str] = seed_forward_definitions(source, code_map)

    def require_resolved_identity(resolution, token: str, offset: int):
        """A resolver's positive verdict MUST carry a current exact identity.

        A Python assert is not an admission gate: -O removes it entirely.
        This is an infrastructure consistency check, not a SENS semantic law.
        """
        identity = resolution.current
        if identity is None:
            line, column = line_col(source, offset)
            raise BinaryMigrationError(
                f"INCONSISTENT_DOMAIN_RESOLUTION {token!r} at {line}:{column}: "
                "resolver says resolved without a current exact-domain identity"
            )
        return identity

    def is_bound(name: str) -> bool:
        return name in global_bindings or any(
            name in entry["bindings"] for entry in frames
        )

    def current_quoted():
        if pending_quote:
            return True
        return bool(frames and (frames[-1]["quoted"] or frames[-1]["quote_children"]))

    def emit_text7_atom(token: str, *, role: str):
        # Rust canonical_reader::text7_binding_key now owns this exact
        # D2/W7 form in binder, variable-reference and executable call-head
        # contexts. No global D7->symbol reinterpretation is permitted.
        if role not in {"binder", "reference", "call-head", "quoted-datum"}:
            raise BinaryMigrationError(f"UNADMITTED_TEXT7_ROLE {role}: {token!r}")
        cells = encode_text7_spelling(token, text7_candidates)
        if not cells:
            raise BinaryMigrationError(f"EMPTY_TEXT7_BINDING {token!r}")
        out.append(D2_OPEN)
        for n, word in enumerate(cells):
            if n:
                out.append(D2_SEPARATOR)
            out.append(word)
        out.append(D2_CLOSE)

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
                if frames and frames[-1]["head"]:
                    frames[-1]["head"] = False
                out.append("000")
                i = j + 1
                pending_quote = False
                continue

            begin_item()
            parent = frames[-1] if frames else None
            parent_quoted = bool(parent and (parent["quoted"] or parent["quote_children"]))
            parent_data_slot = bool(parent and parent["data_slots"] > 0)
            if parent is not None and parent["head"]:
                parent["head"] = False
            # A lambda's parameter *list* is structural D2 data, but
            # individual names are bound via exact D2/W7 contextual keys.
            # The parameter frame records its owner (the active LAMBDA), so
            # its names remain visible in the lambda body after it closes.
            parameter_owner = (
                parent if parent is not None
                and parent.get("resolved_head") == "LAMBDA"
                and parent["data_slots"] > 0 else None
            )
            frames.append({
                "quoted": parent_quoted or pending_quote or parent_data_slot,
                "head": True,
                "quote_children": False,
                "items": 0,
                "data_slots": 0,
                "parent_data_slot": parent_data_slot,
                "parameter_owner": parameter_owner,
                "resolved_head": None,
                "bindings": set(),
            })
            out.append(D2_OPEN)
            i += 1
            pending_quote = False
            continue

        if ch == ")":
            if not frames:
                raise BinaryMigrationError("unexpected closing parenthesis")
            closing = frames.pop()
            out.append(D2_CLOSE)
            i += 1
            pending_quote = False
            if frames and closing["parent_data_slot"] and frames[-1]["data_slots"] > 0:
                frames[-1]["data_slots"] -= 1
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
            raise BinaryMigrationError(
                f"UNADMITTED_STRING_VALUE {token!r}: D7 binding words are not "
                "an executable String Value or a source-string codec"
            )
            if frames and frames[-1]["head"]:
                frames[-1]["head"] = False
            elif frames and frames[-1]["data_slots"] > 0:
                frames[-1]["data_slots"] -= 1
            pending_quote = False
            continue

        # Reader abbreviations stay spelling, but are now D7 cells.
        if source.startswith("#'", i):
            begin_item()
            raise BinaryMigrationError("UNADMITTED_READER_QUOTE: #' is not a D2/D7 binder")
            i += 2
            pending_quote = True
            continue
        if ch in ("'", "`"):
            begin_item()
            raise BinaryMigrationError("UNADMITTED_READER_QUOTE: bare quote/backquote needs a proven D3 QUOTE rewrite")
            i += 1
            pending_quote = True
            continue
        if ch == ",":
            begin_item()
            token = ",@" if i + 1 < len(source) and source[i + 1] == "@" else ","
            raise BinaryMigrationError("UNADMITTED_READER_QUOTE: splice needs canonical executable semantics")
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

        begin_item()
        frame = frames[-1] if frames else None
        is_head = bool(frame and frame["head"])
        is_data_slot = bool(frame and frame["data_slots"] > 0 and not frame["head"])
        quoted = current_quoted() or is_data_slot
        resolved_label = None

        if is_head and not quoted:
            if resolver is None:
                raise BinaryMigrationError(
                    "history-aware SourceResolver is required for binary migration"
                )
            # An explicit D4 DEFINE or lexical LAMBDA binding takes priority
            # over a similarly spelled human surface for a built-in operation.
            # Only names actually introduced by the source get this treatment;
            # unresolved/unbound heads remain fail-closed. Exact binary words
            # cannot be registered as Text7 binders and still go to the resolver.
            if is_bound(token) and not re.fullmatch(r"[01]{3,9}", token):
                emit_text7_atom(token, role="call-head")
            else:
                try:
                    resolution = resolver.resolve_head(token)
                except BinaryMigrationError:
                    raise
                except ValueError as error:
                    # NEW REALITY: an eight-bit head is a retired сід8-era head;
                    # the resolver rejects it with a plain ValueError, but the
                    # migration must fail closed with its own uniform error.
                    raise BinaryMigrationError(
                        f"unresolved executable head {token!r}: {error}"
                    ) from error
                if resolution.resolved:
                    identity = require_resolved_identity(resolution, token, start)
                    if identity.label == "EMPTY":
                        raise BinaryMigrationError(
                            "structural EMPTY/000 cannot be used as a callable head"
                        )
                    out.append(identity.bits)
                    resolved_label = identity.label
                    line, col = line_col(source, start)
                    hits.append(Hit(
                        line, col, identity.label, identity.bits, identity.domain,
                    ))
                else:
                    detail = (
                        ", ".join(resolution.ambiguous)
                        if resolution.ambiguous
                        else "no proven current exact-domain identity or bound D2/D7 name"
                    )
                    raise BinaryMigrationError(
                        f"unresolved executable head {token!r}: "
                        f"{resolution.kind}; {detail}"
                    )
        else:
            # Explicit legacy SID values are semantic identities even outside a
            # call head; migrate them by named historical evidence rather than
            # spelling their eight digits as Text7.
            if re.fullmatch(r"[01]{8}", token):
                if resolver is None:
                    raise BinaryMigrationError(
                        "history-aware SourceResolver is required for SID data migration"
                    )
                resolution = resolver.resolve_head(token)
                if not resolution.resolved:
                    raise BinaryMigrationError(
                        f"unresolved legacy SID value {token!r}"
                    )
                identity = require_resolved_identity(resolution, token, start)
                out.append(identity.bits)
            elif token in {"0", "1"}:
                # Canonical source spelling for the exact D1 PredicateBit.
                # Do not treat these as Number-domain values.
                out.append(token)
            elif re.fullmatch(r"[01]{3,9}", token):
                # An exact domain coordinate (D3-D9, D8 handled above) is a
                # first-class identity used as a value, not a Number. It keeps
                # its exact-width word and is never re-spelled as Text7.
                if resolver is None:
                    raise BinaryMigrationError(
                        "history-aware SourceResolver is required "
                        "for domain coordinates"
                    )
                resolution = resolver.resolve_head(token)
                if not resolution.resolved:
                    raise BinaryMigrationError(
                        f"unresolved domain coordinate {token!r} at "
                        f"{line_col(source, start)[0]}:{line_col(source, start)[1]}"
                    )
                identity = require_resolved_identity(resolution, token, start)
                out.append(identity.bits)
            elif (re.fullmatch(
                r"[+-]?(?:[0-9]+(?:[.,][0-9]*)?|[.,][0-9]+)"
                r"(?:[eE][+-]?[0-9]+)?(?:/[0-9]+)?",
                token,
            ) or re.fullmatch(
                r"(?i)#(?:d[+-]?[0-9]+(?:/[0-9]+)?|b[01]+|q2:[+-]?[01]+/[01]+)",
                token,
            ) or (len(token) >= 24 and len(token) % 24 == 0
                  and set(token) <= {"0", "1"}
                  and (len(token) // 24 & (len(token) // 24 - 1)) == 0)):
                # Domain D24+ requires an explicit admitted domain-bearing
                # physical envelope. The full-width bits alone never authorize
                # silent Number inference or replacement with D7 text glyphs.
                raise BinaryMigrationError(
                    f"numeric literal {token!r} at "
                    f"{line_col(source, start)[0]}:{line_col(source, start)[1]} "
                    "belongs to Number, not Text7; "
                    "ratified Number widths are 24 -> 48 -> 96 -> ...; "
                    "numeric lowering is not yet supplied by this migration"
                )
            else:
                defining = bool(
                    frame and is_data_slot
                    and frame.get("resolved_head") == "DEFINE"
                )
                parameter_owner = frame.get("parameter_owner") if frame else None
                if defining:
                    emit_text7_atom(token, role="binder")
                    global_bindings.add(token)
                elif parameter_owner is not None:
                    emit_text7_atom(token, role="binder")
                    parameter_owner["bindings"].add(token)
                elif not quoted and is_bound(token):
                    emit_text7_atom(token, role="reference")
                elif quoted:
                    # Owner law 2026-10-13: quoted data is checked against the
                    # function ladder (EVAL/APPLY principle). An exact ladder
                    # coordinate keeps its exact-width identity (handled above);
                    # anything with no place in the ladder is D7 spelling,
                    # which preserves every source bit (case included).
                    emit_text7_atom(token, role="quoted-datum")
                else:
                    source_line, source_col = line_col(source, start)
                    context = "quoted-data" if quoted else "unbound-reference"
                    raise BinaryMigrationError(
                        f"UNADMITTED_TEXT7_CONTEXT {token!r} "
                        f"at {source_line}:{source_col} ({context}): source atom is "
                        "neither an admitted D4 DEFINE/LAMBDA binder nor a "
                        "previously bound executable reference; quoted data "
                        "and String values require distinct exact runtime law"
                    )

        if frame and frame["head"]:
            frame["head"] = False
            frame["resolved_head"] = resolved_label
            if resolved_label == "QUOTE":
                frame["quote_children"] = True
            elif resolved_label in {"LAMBDA", "DEFINE"}:
                frame["data_slots"] = 1
        elif frame and is_data_slot and frame["data_slots"] > 0:
            frame["data_slots"] -= 1
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
    parser.add_argument("--apply", action="store_true", help="rewrite supported source in place")
    parser.add_argument(
        "--sens-mirror", type=Path,
        help="write NEW packed Zig/T5M .sens files with same stem as .lisp; no overwrite",
    )
    parser.add_argument("--mirror", type=Path, help="write conservative migrated mirror")
    parser.add_argument(
        "--binary-mirror",
        type=Path,
        help="write comment-free exact-width visible-binary SENS source mirror",
    )
    parser.add_argument(
        "--text7-projection",
        type=Path,
        default=Path("knowledge/d7-keyboard-v2-ratified.json"),
        help="owner-ratified D7 v2 keyboard table (old .rs only for explicit historical replay)",
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

    selected_modes = sum(bool(x) for x in (
        args.apply, args.mirror, args.binary_mirror, args.sens_mirror
    ))
    if selected_modes > 1:
        parser.error("--apply, --mirror, --binary-mirror and --sens-mirror are mutually exclusive")

    foundation, digest = load_foundation(args.foundation)
    code_map = build_map(foundation, args.domains)
    code_map = augment_code_map_with_domain_surfaces(code_map, args.domain_surfaces)
    code_map = augment_code_map_with_registry_aliases(code_map, args.semantic_registry)
    resolver = build_resolver(
        historical_map=args.historical_map,
        foundation=args.foundation,
        registry=args.semantic_registry,
        domain_surfaces=args.domain_surfaces,
    )
    text7_candidates = (
        build_text7_encoder(foundation, args.text7_projection)
        if (args.binary_mirror or args.sens_mirror)
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
    # Validate every member of the batch before publishing any source.
    pending_outputs: list[tuple[Path, bytes]] = []
    zig_temp = tempfile.TemporaryDirectory(prefix="sens-code-zig-") if args.sens_mirror else None
    zig_binary = None
    if zig_temp is not None:
        try:
            zig_binary = zig_codec_bridge.build_transport(Path(zig_temp.name))
        except (OSError, zig_codec_bridge.ZigCodecError) as error:
            zig_temp.cleanup()
            raise SystemExit(f"ZIG_CARRY_REQUIRED_FOR_PUBLICATION: {error}") from error

    for path in sorted(source_files(root, binary_master=bool(args.binary_mirror or args.sens_mirror))):
        text = path.read_text(encoding="utf-8")
        rel = path.relative_to(root)

        if args.binary_mirror or args.sens_mirror:
            try:
                converted, hits, shadowed = binary_rewrite(
                    text,
                    code_map,
                    text7_candidates,
                    legacy_sid_map,
                    registry_surface_sid_map,
                    resolver,
                )
                if not converted.strip():
                    raise BinaryMigrationError("EMPTY_BINARY_SOURCE: an empty source is not an admitted executable program")
                else:
                    if args.sens_mirror:
                        target = args.sens_mirror / rel.with_suffix(".sens")
                        source_words = parse_t5m_words(converted)
                        reference = encode_t5m_projection(converted)
                        if decode_t5m_bytes(reference) != source_words:
                            raise SensT5Error("physical T5M roundtrip changed exact typed words")
                        expected_sha = sha256(reference).hexdigest()
                        physical = zig_codec_bridge.carry_t5(
                            zig_binary, converted, codec="t5m",
                            trusted_source_sha256=expected_sha,
                        )
                        if physical != reference:
                            first = next((i for i, (x, y) in enumerate(zip(reference, physical))
                                          if x != y), min(len(reference), len(physical)))
                            raise BinaryMigrationError(
                                f"ZIG_CARRY_REFERENCE_MISMATCH expected_sha256={expected_sha} "
                                f"actual_sha256={sha256(physical).hexdigest()} first_byte={first}"
                            )
                        receipt = zig_codec_bridge.verify_t5(
                            zig_binary, physical, codec="t5m",
                            trusted_source_sha256=expected_sha,
                        )
                        if (receipt.get("physical_sha256") != expected_sha
                                or receipt.get("source_pin_status") != "MATCHED_CALLER_SUPPLIED_SHA256"
                                or not receipt.get("zig_binary_sha256")):
                            raise BinaryMigrationError("ZIG_CARRY_UNATTESTED_RECEIPT")
                        pending_outputs.append((target, physical))
                        status = "sens-written"
                        extra = {
                            "output": str(rel.with_suffix(".sens")),
                            "physical_bytes": len(physical),
                            "physical_sha256": sha256(physical).hexdigest(),
                            "typed_word_sha256": typed_sha256(source_words),
                            "physical_producer": "PINNED_ZIG_T5M_CARRY",
                            "semantic_admitted": False,
                        }
                    else:
                        target = args.binary_mirror / rel
                        pending_outputs.append((target, converted.encode("ascii")))
                        status = "binary-mirrored"
                        extra = {}
                total_hits += len(hits)
                blocked = []
            except (BinaryMigrationError, SensT5Error, OSError, zig_codec_bridge.ZigCodecError) as error:
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
            "empties": blocked,
            **(extra if (args.binary_mirror or args.sens_mirror) and status == "sens-written" else {}),
        })

    if zig_temp is not None:
        zig_temp.cleanup()

    if args.binary_mirror or args.sens_mirror:
        # Full-batch semantic admission is required, not "some files passed".
        # A failing source must leave zero newly published outputs.
        if not blocked_files and rows and len(pending_outputs) == len(rows):
            created: list[Path] = []
            try:
                for target, payload in pending_outputs:
                    target.parent.mkdir(parents=True, exist_ok=True)
                    staged_path = None
                    try:
                        with tempfile.NamedTemporaryFile(
                            mode="wb", prefix=".sens-stage-", suffix=".tmp",
                            dir=target.parent, delete=False,
                        ) as staged:
                            staged_path = Path(staged.name)
                            staged.write(payload)
                            staged.flush()
                            os.fsync(staged.fileno())
                        os.link(staged_path, target)  # fail on existing target
                        created.append(target)
                    finally:
                        if staged_path is not None:
                            staged_path.unlink(missing_ok=True)
                rewritten_files = len(created)
            except OSError as error:
                for target in reversed(created):
                    target.unlink(missing_ok=True)
                blocked_files += 1
                rows[0]["empties"].append({
                    "reason": f"BATCH_PUBLICATION_BLOCKED: {error}"
                })
                rows[0]["status"] = "blocked"

        if rewritten_files != len(rows):
            rewritten_files = 0
            for row in rows:
                if row["status"] in ("sens-written", "binary-mirrored"):
                    row["status"] = "not-written"
                    for field in ("output", "physical_bytes", "physical_sha256", "typed_word_sha256"):
                        row.pop(field, None)

    mode = (
        "apply" if args.apply
        else "mirror" if args.mirror
        else "sens-mirror" if args.sens_mirror
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
            "D2 structure + exact D3-D6 callable heads + D7/Text7 spelling; comments absent"
            if args.binary_mirror or args.sens_mirror else None
        ),
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

    if args.binary_mirror or args.sens_mirror:
        return 0 if (rows and blocked_files == 0 and rewritten_files == len(rows)) else 2
    return 2 if blocked_files else (1 if total_hits and not (args.apply or args.mirror) else 0)


if __name__ == "__main__":
    raise SystemExit(main())
