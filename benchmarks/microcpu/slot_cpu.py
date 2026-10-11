#!/usr/bin/env python3
"""Experimental CPU slot tape for a bounded, exact D1–D3 subset of physical T5.

Not a language-law authority or a replacement for SENS: a falsifiable substrate
prototype. D2 framing and D1/D3 identities come from existing ratified tables.
No human/Lisp executable names, eight-bit compatibility IDs or text execution.

The tape is compiled ONCE. Every later run dispatches integer slot operations,
not the T5 decoder, D2 parser, symbol resolver or tree evaluator. The initial
subset is deliberately closed: literals, quoted bounded data, D3 primitives
and strict, lazily evaluated two-field COND; no D4+, dotted pair, bindings,
side-effects or recursive functions. The real SENS oracle has final authority.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sys
from typing import TypeAlias

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from sens_t5_codec import decode_bytes, encode_words  # noqa: E402

MAX_DEPTH = 128
MAX_SLOTS = 100_000

# These numbers denote INTERNAL machine slots, not new SENS domain words.
PUSH, UNARY, BINARY, SKIP_ZERO, JUMP = range(5)


class Blocked(ValueError):
    """Outside proved research subset. Never fall back to a legacy evaluator."""


@dataclass(frozen=True)
class Predicate:
    bit: int

    def __post_init__(self):
        if self.bit not in (0, 1):
            raise Blocked("D1 predicates require exactly one bit")


@dataclass(frozen=True)
class DomainWord:
    width: int
    bits: int


@dataclass(frozen=True)
class Pair:
    head: "Value"
    tail: "Value"


@dataclass(frozen=True)
class Empty:
    pass


EMPTY = Empty()
Value: TypeAlias = Predicate | DomainWord | Pair | Empty
Node: TypeAlias = tuple
Slot: TypeAlias = tuple[int, object]


@dataclass(frozen=True)
class Program:
    forms: tuple[tuple[Slot, ...], ...]
    word_count: int
    physical_bytes: int

    @property
    def slot_count(self) -> int:
        return sum(len(form) for form in self.forms)


class Reader:
    def __init__(self, words: list[str]):
        if not words:
            raise Blocked("no exact source words")
        self.words = words
        self.index = 0

    def take(self) -> str:
        if self.index >= len(self.words):
            raise Blocked("incomplete D2 record")
        token = self.words[self.index]
        self.index += 1
        return token

    def term(self, depth: int = 0) -> Node:
        if depth >= MAX_DEPTH:
            raise Blocked("structure exceeds bounded D2 depth")
        first = self.take()
        if first == "10":  # ratified D2 OPEN
            if self.index == len(self.words) or self.words[self.index] == "01":
                raise Blocked("D2 empty list is not canonical D3:000")
            children = [self.term(depth + 1)]
            while True:
                delim = self.take()
                if delim == "01":  # ratified D2 CLOSE
                    break
                if delim != "00":  # ratified D2 SEP; dotted pairs not in this slice
                    raise Blocked("D2 separator/close expected; dot is unsupported")
                children.append(self.term(depth + 1))
            return ("list", tuple(children))
        if len(first) in (1, 3):
            return ("word", len(first), int(first, 2))
        raise Blocked("unproved D2/D4+ token in µCPU executable or datum position")

    def program(self) -> tuple[Node, ...]:
        forms = []
        while self.index < len(self.words):
            forms.append(self.term())
        return tuple(forms)


def datum(node: Node, depth: int = 0) -> Value:
    """QUOTE is data, never an evaluation or an invocation of its head."""
    if depth >= MAX_DEPTH:
        raise Blocked("quoted structure is too deep")
    if node[0] == "word":
        _, width, bits = node
        if width == 1:
            return Predicate(bits)
        if (width, bits) == (3, 0):
            return EMPTY
        return DomainWord(width, bits)
    if node[0] == "list":
        value: Value = EMPTY
        for child in reversed(node[1]):
            value = Pair(datum(child, depth + 1), value)
        return value
    raise Blocked("unsupported quoted datum")


class Assembler:
    def __init__(self):
        self.code: list[Slot] = []

    def emit(self, opcode: int, arg: object) -> int:
        if len(self.code) >= MAX_SLOTS:
            raise Blocked("slot budget exceeded")
        at = len(self.code)
        self.code.append((opcode, arg))
        return at

    def patch(self, at: int, target: int) -> None:
        kind, _ = self.code[at]
        if kind not in (SKIP_ZERO, JUMP) or not (at < target <= len(self.code)):
            raise Blocked("invalid forward-only slot branch")
        self.code[at] = (kind, target)

    def expression(self, node: Node, depth: int = 0) -> None:
        if depth >= MAX_DEPTH:
            raise Blocked("expression exceeds bounded depth")
        if node[0] == "word":
            _, width, bits = node
            if width == 1:
                self.emit(PUSH, Predicate(bits))
            elif (width, bits) == (3, 0):
                self.emit(PUSH, EMPTY)
            else:
                raise Blocked("callable domain word without D2 invocation")
            return
        if node[0] != "list" or not node[1]:
            raise Blocked("call requires nonempty D2 list")
        head, *args = node[1]
        if head[0] != "word" or head[1] != 3 or head[2] == 0:
            raise Blocked("only current D3 invocation heads are admitted")
        op = head[2]  # 001 QUOTE ... 111 CONS
        if op == 1:
            if len(args) != 1:
                raise Blocked("D3:001 requires one datum")
            self.emit(PUSH, datum(args[0]))
        elif op in (2, 3, 4):
            if len(args) != 1:
                raise Blocked("D3 unary operation requires one argument")
            self.expression(args[0], depth + 1)
            self.emit(UNARY, op)
        elif op in (5, 7):
            if len(args) != 2:
                raise Blocked("D3 binary operation requires two arguments")
            self.expression(args[0], depth + 1)
            self.expression(args[1], depth + 1)
            self.emit(BINARY, op)
        elif op == 6:
            # Validate ALL clauses before assembling/executing ANY of them.
            for clause in args:
                if clause[0] != "list" or len(clause[1]) != 2:
                    raise Blocked("D3:110 requires exact two-field D2 clauses")
            ends = []
            for clause in args:
                test, selected = clause[1]
                self.expression(test, depth + 1)
                skip = self.emit(SKIP_ZERO, -1)
                self.expression(selected, depth + 1)
                ends.append(self.emit(JUMP, -1))
                self.patch(skip, len(self.code))
            self.emit(PUSH, EMPTY)  # exhausted D3 COND -> structural ()
            for end in ends:
                self.patch(end, len(self.code))
        else:
            raise Blocked("unratified D3 operation")

    def finish(self) -> tuple[Slot, ...]:
        return tuple(self.code)


def compile_words(words: list[str], *, physical_bytes: int) -> Program:
    # The transport codec checks exact widths; this entrypoint also validates
    # hand-supplied words, avoiding a bypass around that same contract.
    if not words or any(not w or len(w) > 9 or set(w) - {"0", "1"} for w in words):
        raise Blocked("noncanonical exact binary source word")
    forms = Reader(words).program()
    tapes = []
    for form in forms:
        assembler = Assembler()
        assembler.expression(form)
        tapes.append(assembler.finish())
    return Program(tuple(tapes), len(words), physical_bytes)


def compile_t5(physical: bytes) -> Program:
    return compile_words(decode_bytes(physical), physical_bytes=len(physical))


def run(program: Program) -> Value:
    result: Value = EMPTY
    for code in program.forms:
        stack: list[Value] = []
        pc = 0
        while pc < len(code):
            kind, arg = code[pc]
            if kind == PUSH:
                stack.append(arg)
            elif kind == UNARY:
                if not stack:
                    raise Blocked("slot stack underflow")
                value = stack.pop()
                if arg == 2:
                    stack.append(Predicate(0 if isinstance(value, Pair) else 1))
                elif arg in (3, 4) and isinstance(value, Pair):
                    stack.append(value.tail if arg == 3 else value.head)
                else:
                    raise Blocked("D3 CAR/CDR expects a pair")
            elif kind == BINARY:
                if len(stack) < 2:
                    raise Blocked("slot stack underflow")
                right = stack.pop()
                left = stack.pop()
                if arg == 7:
                    stack.append(Pair(left, right))
                elif arg == 5:
                    if isinstance(left, Pair) or isinstance(right, Pair):
                        raise Blocked("D3 EQ accepts only atoms")
                    stack.append(Predicate(int(left == right)))
                else:
                    raise Blocked("invalid D3 binary operation")
            elif kind == SKIP_ZERO:
                if not stack:
                    raise Blocked("slot stack underflow")
                test = stack.pop()
                if not isinstance(test, Predicate):
                    raise Blocked("D3 COND requires exact D1; () is not false")
                if test.bit == 0:
                    pc = int(arg)
                    continue
            elif kind == JUMP:
                pc = int(arg)
                continue
            else:
                raise Blocked("invalid internal machine slot")
            pc += 1
        if len(stack) != 1:
            raise Blocked("slot expression did not yield exactly one value")
        result = stack[0]
    return result


def visible(value: Value) -> str:
    if isinstance(value, Empty):
        return "()"
    if isinstance(value, Predicate):
        return str(value.bit)
    if isinstance(value, DomainWord):
        return format(value.bits, f"0{value.width}b")
    if isinstance(value, Pair):
        chunks = []
        tail: Value = value
        while isinstance(tail, Pair):
            chunks.append(visible(tail.head))
            tail = tail.tail
        return "(" + " ".join(chunks) + ("" if isinstance(tail, Empty) else " . " + visible(tail)) + ")"
    raise Blocked("unknown slot result type")


def main(argv: list[str] | None = None) -> int:
    import argparse
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("physical", type=Path, help="real packed T5 .sens program")
    ap.add_argument("--slots", action="store_true", help="show mechanism tape, never semantic source")
    args = ap.parse_args(argv)
    if args.physical.suffix != ".sens":
        ap.error("source must be a physical .sens file")
    try:
        program = compile_t5(args.physical.read_bytes())
        if args.slots:
            print(program.forms)
        else:
            print(visible(run(program)))
    except (Blocked, ValueError) as exc:
        print(f"MICROCPU BLOCKED: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
