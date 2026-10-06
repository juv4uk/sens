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

CALL_DOMAINS = ("D3", "D4", "D5", "D6")
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


def _entry_index(code_map):
    out = {}
    for entry in code_map.values():
        out[(entry.domain, entry.bits)] = entry
    return out


def augment_code_map_with_domain_surfaces(code_map, paths):
    """Add exact human spellings from domain surface projection files.

    These files are projection-only, but each row names an exact (domain,bits)
    identity. We use them only to recognize source spelling; semantic identity
    still comes from the ratified foundation entry.
    """
    by_identity = _entry_index(code_map)
    out = dict(code_map)
    row = re.compile(
        r'^\s*\(row\s+(D[1-8])\s+"([01]+)"\s+\S+\s+'
        r'"([^"]*)"\s+"([^"]*)"\s+"([^"]*)"',
        re.M,
    )
    for path in paths:
        text = path.read_text(encoding="utf-8")
        for match in row.finditer(text):
            domain, bits = match.group(1), match.group(2)
            entry = by_identity.get((domain, bits))
            if entry is None:
                continue
            for surface in match.groups()[2:]:
                surface = surface.strip()
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


def binary_rewrite(text, code_map, text7_candidates, legacy_sid_map=None):
    """Encode one source file as exact-width visible binary SENS words."""
    source = strip_comments(text)
    shadowed = {row["label"] for row in shadowing(source, code_map)}
    legacy_sid_map = legacy_sid_map or {}
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

        begin_item()
        frame = frames[-1] if frames else None
        is_head = bool(frame and frame["head"])
        quoted = current_quoted()
        upper = token.upper()
        entry = code_map.get(upper)
        binary_head = (
            is_head
            and not quoted
            and 1 <= len(token) <= 8
            and set(token) <= {"0", "1"}
        )

        if (
            is_head
            and not quoted
            and entry
            and upper not in shadowed
            and ":" not in token
        ):
            out.append(entry.bits)
            line, col = line_col(source, start)
            hits.append(Hit(line, col, entry.label, entry.bits, entry.domain))
        elif binary_head:
            if len(token) == 8:
                migrated = legacy_sid_map.get(token)
                if migrated is None:
                    raise BinaryMigrationError(
                        f"legacy 8-bit call head {token} has no admitted D3-D6 migration"
                    )
                out.append(migrated.bits)
                line, col = line_col(source, start)
                hits.append(Hit(
                    line,
                    col,
                    migrated.label,
                    migrated.bits,
                    migrated.domain,
                ))
            elif (len(token), token) in current_words:
                out.append(token)
            else:
                raise BinaryMigrationError(
                    f"binary call head {token} is not a current D3-D6 resident"
                )
        else:
            out.extend(encode_text7_spelling(token, text7_candidates))

        if frame and frame["head"]:
            frame["head"] = False
            if upper == "QUOTE":
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
        "--semantic-registry",
        type=Path,
        default=Path("lib/surface/semantic-registry.lisp"),
        help="pinned legacy SID8 surface registry used only for exact D3-D6 migration",
    )
    parser.add_argument(
        "--domain-surfaces",
        type=Path,
        nargs="*",
        default=[
            Path("lib/surface/domain-surfaces-d1-d4.lisp"),
            Path("lib/surface/domain-surfaces-d5.lisp"),
        ],
        help="exact-domain surface projection files used to recognize function spellings",
    )
    parser.add_argument("--report", type=Path, default=Path("sens-code-migration-report.json"))
    args = parser.parse_args()

    selected_modes = sum(bool(x) for x in (args.apply, args.mirror, args.binary_mirror))
    if selected_modes > 1:
        parser.error("--apply, --mirror and --binary-mirror are mutually exclusive")

    foundation, digest = load_foundation(args.foundation)
    code_map = build_map(foundation, args.domains)
    code_map = augment_code_map_with_domain_surfaces(code_map, args.domain_surfaces)
    code_map = augment_code_map_with_registry_aliases(code_map, args.semantic_registry)
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
            "D2 structure + exact D3-D6 callable heads + D7/Text7 spelling; comments absent"
            if args.binary_mirror else None
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

    if args.binary_mirror:
        return 0 if rewritten_files else 2
    return 2 if blocked_files else (1 if total_hits and not (args.apply or args.mirror) else 0)


if __name__ == "__main__":
    raise SystemExit(main())
