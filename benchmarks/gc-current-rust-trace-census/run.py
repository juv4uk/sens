#!/usr/bin/env python3
"""#2548 — executable census of the current Rust trace-relevant layout.

This is a representation witness, not a collector and not semantic authority.
It intentionally fails when the landed host representation drifts so GC work
cannot keep tracing an imagined SENS heap.
"""

from __future__ import annotations

from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def require(text: str, pattern: str, label: str) -> None:
    if re.search(pattern, text, re.MULTILINE | re.DOTALL) is None:
        raise AssertionError(f"missing representation fact: {label}")


def struct_block(text: str, start_pattern: str) -> str:
    m = re.search(start_pattern, text)
    if m is None:
        raise AssertionError(f"missing block start: {start_pattern}")
    start = m.start()
    brace = text.find("{", m.end() - 1)
    if brace < 0:
        raise AssertionError("missing opening brace")
    depth = 0
    for i in range(brace, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return text[start : i + 1]
    raise AssertionError("unterminated block")


def main() -> None:
    value = read("crates/sens/src/value.rs")
    env = read("crates/sens/src/environment.rs")
    text7 = read("crates/sens/src/text7.rs")
    bignum = read("crates/sens/src/bignum.rs")

    # Pair: exactly two direct Value references in the current host representation.
    require(value, r"Pair\(Rc<Value>,\s*Rc<Value>\)", "Pair has two Rc<Value> fields")

    # Vector: every element is a Value, behind host Rc/RefCell ownership.
    require(
        value,
        r"Vector\(std::rc::Rc<std::cell::RefCell<Vec<Value>>>\)",
        "Vector contains Vec<Value>",
    )

    # Closure: Environment is the trace-relevant semantic graph edge today.
    closure = struct_block(value, r"pub struct Closure\s*\{")
    require(closure, r"environment:\s*Environment", "Closure -> Environment")
    require(closure, r"body:\s*Rc<\[Expr\]>", "Closure body is host-owned Rc<[Expr]>")
    require(
        closure,
        r"resolved:\s*Option<\(Rc<\[Expr\]>,\s*u64\)>",
        "Closure resolved body is host-owned Rc<[Expr]>",
    )

    # Environment: frame graph owns Values and parent Environment edges.
    require(env, r"pub struct Environment\(\s*Rc<RefCell<Frame>>", "Environment frame handle")
    frame = struct_block(env, r"struct Frame\s*\{")
    require(frame, r"slots:\s*Vec<Value>", "Frame slots contain Value")
    require(frame, r"values:\s*HashMap<Rc<str>,\s*Value>", "Frame map contains Value")
    require(frame, r"parent:\s*Option<Environment>", "Frame parent environment edge")

    # Text7 is contiguous host byte storage, not a graph of managed child values.
    text_block = struct_block(text7, r"pub struct Text7\s*\{")
    require(text_block, r"cells:\s*Rc<\[u8\]>", "Text7 host byte backing")
    assert "Value" not in text_block, "Text7 unexpectedly gained a Value child edge"

    # Exact rational is currently owned host data over BigInt; BigInt limbs are Vec<u32>.
    rational = struct_block(value, r"pub struct Rational\s*\{")
    require(rational, r"numerator:\s*BigInt", "Rational numerator BigInt")
    require(rational, r"denominator:\s*BigInt", "Rational denominator BigInt")
    require(bignum, r"struct Magnitude\(Vec<u32>\);", "BigInt magnitude Vec<u32>")
    assert "Limb24" not in value + bignum, "future Limb24 layout leaked into current Rust census"

    # Numeric buffers contain scalars only.
    numeric = re.search(
        r"pub enum NumericBuffer\s*\{(?P<body>.*?)\n\}",
        value,
        re.MULTILINE | re.DOTALL,
    )
    assert numeric is not None
    nbody = numeric.group("body")
    require(nbody, r"I32\(std::sync::Arc<\[i32\]>\)", "I32 scalar buffer")
    require(nbody, r"F32\(std::sync::Arc<\[f32\]>\)", "F32 scalar buffer")
    assert "Value" not in nbody, "NumericBuffer unexpectedly gained Value edges"

    # Opaque host closure: a tracing heap cannot introspect captured Rust state.
    require(
        value,
        r"pub type BuiltinFunction\s*=\s*Rc<dyn Fn\(&\[Value\],\s*&crate::Environment",
        "BuiltinFunction opaque host closure",
    )

    # Host resources remain resource boundaries, not managed graph children.
    require(value, r"HostHandle\s*\{\s*kind:\s*Rc<str>,\s*token:\s*u64", "HostHandle scalar token")
    require(value, r"TcpConnection\(Rc<RefCell<TcpStream>>\)", "TCP connection host resource")
    require(value, r"TcpListener\(Rc<TcpListener>\)", "TCP listener host resource")

    print("GC-CURRENT-RUST-TRACE-CENSUS=PASS")
    print("PAIR=2-VALUE-EDGES")
    print("VECTOR=N-VALUE-EDGES")
    print("CLOSURE=ENVIRONMENT-EDGE;SYNTAX-HOST-OWNED")
    print("ENVIRONMENT=SLOTS+VALUES+PARENT")
    print("TEXT7=HOST-RC-BYTES;VALUE-EDGES=0")
    print("RATIONAL=HOST-BIGINT;VALUE-EDGES=0")
    print("BIGINT=VEC-U32;LIMB24=ABSENT")
    print("NUMERIC-BUFFER=HOST-SCALARS;VALUE-EDGES=0")
    print("BUILTIN=OPAQUE-HOST-CLOSURE;IMPLICIT-TRACE=FORBIDDEN")
    print("HOST-RESOURCES=EXPLICIT-BOUNDARY")
    print("SEMANTIC-AUTHORITY=NONE")
    print("RUNTIME-GC-IMPLEMENTATION=0")


if __name__ == "__main__":
    main()
