#!/usr/bin/env python3
"""D10 finite binary codebook uniquely decodable: research-only independent witnesses.

Sardinas-Patterson closure proves YES/NO; finite brute force supplies only
one-sided falsification. Does not authorize D2/.sens/physical codec or D10 bits.
"""
from itertools import combinations, product


def require(value, message):
    if not value:
        raise RuntimeError(message)


def validate(book):
    if not isinstance(book, (list, tuple)):
        raise ValueError("finite ordered codebook required")
    identities, words = set(), []
    for pair in book:
        if not isinstance(pair, (list, tuple)) or len(pair) != 2:
            raise ValueError("entry must be identity/word pair")
        identity, word = pair
        if not isinstance(identity, str) or not identity or identity in identities:
            raise ValueError("nonempty unique identities required")
        identities.add(identity)
        if not isinstance(word, str) or not word or any(ch not in "01" for ch in word):
            raise ValueError("nonempty binary codeword required")
        words.append(word)
    return words


def sardinas_patterson(book):
    words = validate(book)
    if len(words) != len(set(words)):
        return False
    residuals = {b[len(a):] for i, a in enumerate(words)
                 for j, b in enumerate(words)
                 if i != j and b.startswith(a) and len(b) > len(a)}
    visited = set()
    while residuals:
        if any(s in words for s in residuals):
            return False
        pending = residuals - visited
        if not pending:
            return True
        visited.update(pending)
        new = set()
        for suffix in pending:
            for word in words:
                if suffix.startswith(word):
                    if len(suffix) == len(word):
                        return False
                    new.add(suffix[len(word):])
                if word.startswith(suffix):
                    if len(word) == len(suffix):
                        return False
                    new.add(word[len(suffix):])
        residuals = new - visited
    return True


def bounded_collision(book, depth=6):
    """Direct independent enumeration; absence of collision proves nothing."""
    words = validate(book)
    encodings = {}
    for size in range(1, depth + 1):
        for indices in product(range(len(words)), repeat=size):
            encoded = "".join(words[i] for i in indices)
            prev = encodings.get(encoded)
            if prev is not None and prev != indices:
                return prev, indices, encoded
            encodings[encoded] = indices
    return None


def check():
    examples = [
        ([], True),
        ([("a", "0"), ("b", "11")], True),
        ([("a", "0"), ("b", "01")], True),
        ([("a", "0"), ("b", "01"), ("c", "10")], False),
        ([("a", "0"), ("b", "0")], False),
        ([("a", "0"), ("b", "1"), ("c", "000000")], False),
        ([("a", "0")], True),
    ]
    for book, expected in examples:
        require(sardinas_patterson(book) is expected, "witness mismatch: " + repr(book))
    require(bounded_collision(examples[3][0], 4) is not None, "known collision missing")
    require(bounded_collision(examples[2][0], 6) is None, "false collision")
    invalid = [[("a", "")], [("a", "2")], [("a", "0"), ("a", "1")],
               [("", "0")], [("a", None)], [("a", "0", 3)], "01", None]
    for book in invalid:
        try:
            sardinas_patterson(book)
        except ValueError:
            continue
        raise RuntimeError("invalid input accepted: " + repr(book))
    words = ["".join(p) for n in (1, 2, 3) for p in product("01", repeat=n)]
    count = 0
    for size in range(4):
        for chosen in combinations(words, size):
            book = [(str(i), w) for i, w in enumerate(chosen)]
            decision = sardinas_patterson(book)
            counterexample = bounded_collision(book, 6)
            require(not (counterexample is not None and decision),
                    "spurious YES: " + repr((book, counterexample)))
            count += 1
    print(f"D10-UNIQUE-DECIPHERABILITY: PASS {count} bounded cross-checks, "
          f"{len(examples)} witnesses, {len(invalid)} rejects; research only")


if __name__ == "__main__":
    check()
