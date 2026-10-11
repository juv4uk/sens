"""Exact-word D2 grammar rank, bounded single-root research (NOT .sens codec).

Unlike historical grammar_rank_research, every 2-bit word is structural:
00 separator, 01 close, 10 open, 11 dot. Payload is D1 or D3..D9.
The input/output is the ORIGINAL typed word sequence, including every 00.
No assumption of syntactic AST alias elimination or executable admission.
An external bit length is essential: bytes here exclude file overhead/CRC.
"""
from __future__ import annotations

from functools import lru_cache

MAX_INNER_BITS = 20
OPEN, CLOSE, SEP, DOT = "10", "01", "00", "11"
EMPTY, ITEMS, DOT_TAIL, DOT_CLOSE = range(4)
INITIAL = (EMPTY,)


class D2RankError(ValueError):
    """Invalid D2 sequence, unknown length, rank or unproved profile."""


def _word_valid(word: str) -> bool:
    return isinstance(word, str) and 1 <= len(word) <= 9 and all(
        c in "01" for c in word
    )


def _complete(stack: tuple[int, ...]) -> tuple[int, ...] | None:
    """Completing nested expression updates its parent's list phase."""
    parent = stack[-2]
    if parent in (EMPTY, ITEMS):
        return stack[:-2] + (ITEMS,)
    if parent == DOT_TAIL:
        return stack[:-2] + (DOT_CLOSE,)
    return None


def advance(stack: tuple[int, ...], word: str) -> tuple[int, ...] | None:
    """Reader-equivalent transitions for ONE fixed exterior D2 list."""
    if not _word_valid(word) or not stack:
        return None
    state = stack[-1]
    if word == SEP:
        return stack  # Rust skip_separators permits repeated 00.
    if word == DOT:
        return stack[:-1] + (DOT_TAIL,) if state == ITEMS else None
    if word == OPEN:
        return stack + (EMPTY,) if state != DOT_CLOSE else None
    if word == CLOSE:
        if len(stack) == 1 or state == DOT_TAIL:
            return None  # Exterior 01 is fixed, never in the inner stream.
        return _complete(stack)
    # Every W1 and W3..W9 is an expression; W3 000 is empty value.
    if state in (EMPTY, ITEMS):
        return stack[:-1] + (ITEMS,)
    if state == DOT_TAIL:
        return stack[:-1] + (DOT_CLOSE,)
    return None


def _accepts(stack: tuple[int, ...]) -> bool:
    return stack in ((EMPTY,), (ITEMS,), (DOT_CLOSE,))


@lru_cache(maxsize=None)
def _completions(bits: int, stack: tuple[int, ...]) -> int:
    if bits == 0:
        return int(_accepts(stack))
    if bits < 0:
        return 0
    count = 0
    # Non-D2 payloads have identical structural transitions; count their
    # numeric choices in bulk without accidentally calling 00/11 atoms.
    for width in range(1, min(9, bits) + 1):
        if width == 2:
            for word in (SEP, CLOSE, OPEN, DOT):
                next_state = advance(stack, word)
                if next_state is not None:
                    count += _completions(bits - 2, next_state)
        else:
            next_state = advance(stack, "0" * width)
            if next_state is not None:
                count += (1 << width) * _completions(bits - width, next_state)
    return count


def count_inner(inner_bits: int) -> int:
    """Number of exact-word bodies of this bit length inside fixed 10/01."""
    if not isinstance(inner_bits, int) or isinstance(inner_bits, bool) or not (
        0 <= inner_bits <= MAX_INNER_BITS
    ):
        raise D2RankError("unsupported inner bit length")
    return _completions(inner_bits, INITIAL)


def _choices(remaining: int, stack: tuple[int, ...]):
    """Rank order: width, then unsigned value, with exact leading zeroes."""
    for width in range(1, min(9, remaining) + 1):
        for value in range(1 << width):
            word = format(value, f"0{width}b")
            next_state = advance(stack, word)
            if next_state is None:
                continue
            suffixes = _completions(remaining - width, next_state)
            if suffixes:
                yield word, next_state, suffixes


def rank(words: tuple[str, ...] | list[str]) -> tuple[int, int]:
    """Return (exact inner bit length, 0-based rank); reject wrong D2 trees."""
    words = tuple(words)
    if len(words) < 2 or words[0] != OPEN or words[-1] != CLOSE:
        raise D2RankError("single fixed exterior D2 10 ... 01 required")
    inner = words[1:-1]
    if not all(_word_valid(word) for word in inner):
        raise D2RankError("bad exact domain word")
    total_bits = sum(map(len, inner))
    count_inner(total_bits)  # enforce research bound
    rank_value, stack, remaining = 0, INITIAL, total_bits
    for word in inner:
        found = False
        for candidate, next_state, suffixes in _choices(remaining, stack):
            if candidate == word:
                stack = next_state
                remaining -= len(word)
                found = True
                break
            rank_value += suffixes
        if not found:
            raise D2RankError("invalid D2 structure or unavailable rank")
    if remaining != 0 or not _accepts(stack) or rank_value >= count_inner(total_bits):
        raise D2RankError("invalid exact D2 list")
    return total_bits, rank_value


def unrank(inner_bits: int, value: int) -> tuple[str, ...]:
    """Inverse of rank; physical framing must supply exact inner_bits."""
    count = count_inner(inner_bits)
    if not isinstance(value, int) or isinstance(value, bool) or not 0 <= value < count:
        raise D2RankError("rank not in admissible exact D2 set")
    stack, remaining, inner = INITIAL, inner_bits, []
    while remaining:
        for word, next_state, suffixes in _choices(remaining, stack):
            if value < suffixes:
                inner.append(word)
                stack = next_state
                remaining -= len(word)
                break
            value -= suffixes
        else:
            raise D2RankError("corrupt rank")
    if not _accepts(stack) or value != 0:
        raise D2RankError("rank decoded to incomplete D2")
    return (OPEN, *inner, CLOSE)


def rank_bytes_at_known_length(words: tuple[str, ...] | list[str]) -> bytes:
    """Research-only body bytes: no header, no bit-length metadata, no CRC."""
    bits, value = rank(words)
    size = (count_inner(bits) - 1).bit_length()  # bit width
    return value.to_bytes((size + 7) // 8, "big")


def unrank_bytes_at_known_length(inner_bits: int, body: bytes) -> tuple[str, ...]:
    """Reject unused codes and non-minimal physical aliases."""
    count = count_inner(inner_bits)
    size = ((count - 1).bit_length() + 7) // 8
    if not isinstance(body, bytes) or len(body) != size:
        raise D2RankError("noncanonical body length")
    return unrank(inner_bits, int.from_bytes(body, "big"))


if __name__ == "__main__":
    for bits in range(MAX_INNER_BITS + 1):
        print(f"inner_bits={bits} admitted_exact_d2={count_inner(bits)}")
