#!/usr/bin/env python3
"""#2630 — minimize explicit caller-environment access.

Research-only SENS-DERIVATION witness.

Separates:
A. ordinary call with no caller-environment channel;
B. ordinary call with explicitly supplied environment-shaped data;
C. automatic injection/reflection of the actual caller environment.

No width or coordinate is assigned.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CORE1 = ROOT / "lib" / "core1.lisp"
CLOSURES = ROOT / "crates" / "sens" / "src" / "eval" / "closures.rs"
D4_POLARITY = ROOT / "docs" / "research" / "2162-d4-polarity.md"
FEXPR_CUBE = ROOT / "scripts" / "research-2522-fexpr-protocol-cube.py"


@dataclass(frozen=True)
class Binding:
    name: str
    value: str


Env = tuple[Binding, ...]


def lookup(name: str, env: Env) -> str | None:
    for binding in env:
        if binding.name == name:
            return binding.value
    return None


def ordinary_no_env_channel(explicit_args: tuple[str, ...]) -> tuple[str, ...]:
    return explicit_args


def explicit_env_data_model(env_value: Env, name: str) -> str | None:
    return lookup(name, env_value)


def automatic_caller_env_model(actual_caller_env: Env, name: str) -> str | None:
    return lookup(name, actual_caller_env)


def assert_source_boundary() -> None:
    core1 = CORE1.read_text(encoding="utf-8")
    closures = CLOSURES.read_text(encoding="utf-8")
    d4 = D4_POLARITY.read_text(encoding="utf-8")
    cube = FEXPR_CUBE.read_text(encoding="utf-8")

    assert "(00001001 C1-LOOKUP\n  (00001000 (NAME ENV GLOBAL)" in core1
    assert "(00001001 C1-BIND\n  (10101010 C1-BIND\n    (00001000 (PARAMS ARGS ENV)" in core1
    assert "`C1-LOOKUP` searches existing frames" in d4
    assert "`C1-BIND` constructs new environment" in d4

    assert "slots.push(evaluate(argument, calling_environment)?);" in closures
    assert "let local_environment = call_frame(closure, slots);" in closures
    assert "closure\n        .environment\n        .child_with_slots" in closures

    ordinary_start = closures.index("Value::Closure(ref closure) => {")
    ordinary_end = closures.index("_ => Err(LanguageError::new(", ordinary_start)
    ordinary = closures[ordinary_start:ordinary_end]
    assert "slots.push(calling_environment" not in ordinary

    assert 'return ("ok", "42")' in cube
    assert 'return ("error", "caller-env-unavailable")' in cube


def main() -> None:
    assert_source_boundary()

    caller_42: Env = (Binding("x", "42"), Binding("outer", "A"))
    caller_99: Env = (Binding("x", "99"), Binding("outer", "B"))
    explicit_args: tuple[str, ...] = ("payload",)

    no_channel_a = ordinary_no_env_channel(explicit_args)
    no_channel_b = ordinary_no_env_channel(explicit_args)
    assert no_channel_a == no_channel_b

    actual_a = automatic_caller_env_model(caller_42, "x")
    actual_b = automatic_caller_env_model(caller_99, "x")
    assert actual_a == "42"
    assert actual_b == "99"
    assert actual_a != actual_b

    explicit_a = explicit_env_data_model(caller_42, "x")
    explicit_b = explicit_env_data_model(caller_99, "x")
    assert explicit_a == actual_a
    assert explicit_b == actual_b

    assert no_channel_a == no_channel_b
    assert caller_42 != caller_99

    assert explicit_env_data_model(caller_42, "missing") is None
    assert automatic_caller_env_model(caller_42, "missing") is None

    print("R3-EXPLICIT-CALLER-ENV=PASS")
    print("ordinary-no-env-channel=same-input-collision")
    print("caller-42-observation=42")
    print("caller-99-observation=99")
    print("explicit-env-data-plus-lookup=reproduces-body-observation")
    print("automatic-current-caller-env=requires-acquisition-channel")
    print("root-status=CARRIER-PREMISE")
    print("basis-dependencies=D4-LOOKUP,BIND+explicit-structure")
    print("hidden-capability-needed=current-caller-env-reification/injection")
    print("width=UNKNOWN")
    print("coordinate=UNPLACED")
    print("new-residents=0")
    print("NON-CONCLUSION=environment-carrier-is-not-a-D5-resident")
    print("NON-CONCLUSION=no-coordinate-allocation")


if __name__ == "__main__":
    main()
