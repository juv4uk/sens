"""Bounded, RESEARCH-ONLY Framed-3 bijection for one D2 outer list.

Not the canonical .sens T5 codec. A file boundary supplies *byte count*;
variable-width code buckets supply the precise trit count. There is no
redundant opening/closing separator and no transport tail padding.

Constraint is deliberately weaker than D2 grammar, hence a conservative
capacity bound: anchored 10 2 ... 2 01 with no adjacent 22. This is not a
semantic parser or a proposed ratification of another domain.
"""

from functools import lru_cache

MAX_TRITS = 128   # finite proof-of-concept; long streaming is a separate issue
OPEN = (1, 0, 2)
CLOSE = (2, 0, 1)


class FrameError(ValueError):
    """Input is not in this experimental codec's exact bounded domain."""


def _allowed(n: int, pos: int) -> tuple[int, ...]:
    if pos < 3:
        return (OPEN[pos],)
    if pos >= n - 3:
        return (CLOSE[pos - (n - 3)],)
    return (0, 1, 2)


@lru_cache(maxsize=None)
def _ways(n: int, pos: int, previous: int) -> int:
    if pos == n:
        return 1
    return sum(
        _ways(n, pos + 1, digit)
        for digit in _allowed(n, pos)
        if not (previous == 2 and digit == 2)
    )


@lru_cache(maxsize=None)
def capacity(n: int) -> int:
    """Upper bound on the number of transport sequences of length n.

    Excludes the *overlapping* 6-trit prefix/suffix and handles the empty D2
    form '10 2 01' at n=5. For n>=7 this counts all strings with anchored
    ends and no adjacent 22, including some D2-invalid and >9-bit words;
    therefore it can never UNDER-count admissible programs.
    """
    if n == 5:
        return 1
    if n < 7 or n > MAX_TRITS:
        return 0
    return _ways(n, 0, -1)


def _rank(trits: tuple[int, ...]) -> int:
    n = len(trits)
    if n == 5:
        if trits != (1, 0, 2, 0, 1):
            raise FrameError("invalid empty outer list")
        return 0
    if not 7 <= n <= MAX_TRITS:
        raise FrameError("trit length outside bounded research profile")
    index, previous = 0, -1
    for pos, digit in enumerate(trits):
        if digit not in _allowed(n, pos) or previous == digit == 2:
            raise FrameError("invalid anchored/no-22 transport")
        for smaller in _allowed(n, pos):
            if previous == smaller == 2:
                continue
            if smaller == digit:
                break
            index += _ways(n, pos + 1, smaller)
        previous = digit
    assert index < capacity(n)
    return index


def _unrank(n: int, index: int) -> tuple[int, ...]:
    if not 0 <= index < capacity(n):
        raise FrameError("index outside valid length class")
    if n == 5:
        return (1, 0, 2, 0, 1)
    previous = -1
    out = []
    for pos in range(n):
        for digit in _allowed(n, pos):
            if previous == digit == 2:
                continue
            possible = _ways(n, pos + 1, digit)
            if index < possible:
                out.append(digit)
                previous = digit
                break
            index -= possible
        else:
            raise AssertionError("mathematically unreachable rank failure")
    return tuple(out)


@lru_cache(maxsize=None)
def _buckets() -> tuple[tuple[int, int, int], ...]:
    """Minimal exact byte-count buckets: (bytes, first_n, last_n)."""
    result = []
    n = 5
    byte_count = 1
    while n <= MAX_TRITS:
        start, capacity_left = n, 1 << (8 * byte_count)
        while n <= MAX_TRITS and capacity(n) <= capacity_left:
            capacity_left -= capacity(n)
            n += 1
        if start == n:
            raise AssertionError("byte-bucket cannot hold even one length")
        result.append((byte_count, start, n - 1))
        byte_count += 1
    return tuple(result)


def _check_words(words: tuple[str, ...]) -> None:
    if len(words) < 2 or words[0] != "10" or words[-1] != "01":
        raise FrameError("one outer 10 ... 01 list is required")
    nesting = 0
    for pos, word in enumerate(words):
        if not 1 <= len(word) <= 9 or any(bit not in "01" for bit in word):
            raise FrameError("word must have exact D1..D9 width and binary bits")
        if word == "10":
            nesting += 1
        elif word == "01":
            nesting -= 1
            if nesting < 0 or (nesting == 0 and pos < len(words) - 1):
                raise FrameError("unbalanced D2 / extra top-level expression")
    if nesting:
        raise FrameError("unclosed outer D2 frame")


def transport(words: tuple[str, ...] | list[str]) -> tuple[int, ...]:
    words = tuple(words)
    _check_words(words)
    trits = tuple(map(int, "2".join(words)))
    if len(trits) > MAX_TRITS:
        raise FrameError("long frame needs a separately proven streaming codec")
    _rank(trits)
    return trits


def encode(words: tuple[str, ...] | list[str]) -> bytes:
    trits = transport(words)
    n = len(trits)
    for width, lo, hi in _buckets():
        if lo <= n <= hi:
            offset = sum(capacity(length) for length in range(lo, n))
            return (offset + _rank(trits)).to_bytes(width, "big")
    raise FrameError("no physical bucket")


def decode(data: bytes) -> tuple[str, ...]:
    for width, lo, hi in _buckets():
        if len(data) == width:
            code = int.from_bytes(data, "big")
            for n in range(lo, hi + 1):
                count = capacity(n)
                if code < count:
                    trits = _unrank(n, code)
                    words = tuple("".join(map(str, trits)).split("2"))
                    # Strict decoding must NOT admit invalid D2-shaped words,
                    # overly wide words, extra roots, or noncanonical aliases.
                    if transport(words) != trits or encode(words) != data:
                        raise FrameError("decoded sequence is not canonical")
                    return words
                code -= count
            raise FrameError("unused byte codepoint (no hidden padding)")
    raise FrameError("unsupported physical byte count")


def reference_t5(words: tuple[str, ...] | list[str]) -> bytes:
    """Independent, simple T5 size/byte witness; NOT a runtime decoder."""
    trits = transport(words)
    padded = trits + (2,) * (-len(trits) % 5)
    return bytes(
        sum(padded[pos + i] * (3 ** (4 - i)) for i in range(5))
        for pos in range(0, len(padded), 5)
    )


def main() -> None:
    print("Experimental framed 10 ... 01; T5 stays canonical")
    for width, lo, hi in _buckets():
        used = sum(capacity(n) for n in range(lo, hi + 1))
        print(f"  {width} bytes: trit lengths {lo}..{hi}; {used}/{1 << (8 * width)} values")
    fixtures = {
        "empty D2 list": ("10", "01"),
        "QUOTE": ("10", "001", "00", "000", "01"),
        "CAR(CONS(1,0))": "10 100 00 10 111 00 1 00 0 01 01".split(),
    }
    for name, words in fixtures.items():
        raw = reference_t5(words)
        experimental = encode(words)
        assert decode(experimental) == tuple(words)
        print(f"  {name}: {len(transport(words))} trits; T5={len(raw)} bytes; Framed-3={len(experimental)} bytes; hex={experimental.hex()}")


if __name__ == "__main__":
    main()
