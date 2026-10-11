#!/usr/bin/env python3
"""Cheap semantic witness for #3945.

This compares two binding laws only:
- current SENS lexical capture;
- historical SPECIAL-style dynamic cell save/restore.

It does not implement SPECIAL in production and does not ratify D8.
"""

def lexical_model():
    captured_x = 1

    def f():
        return captured_x

    def caller():
        x = 2
        _ = x
        return f()

    return caller()


class SpecialCell:
    def __init__(self, value):
        self.value = value

    def bind(self, value, thunk):
        previous = self.value
        self.value = value
        try:
            return thunk()
        finally:
            self.value = previous


def dynamic_special_model():
    x = SpecialCell(1)

    def f():
        return x.value

    inside = x.bind(2, f)
    restored = f()
    return inside, restored


def main():
    assert lexical_model() == 1
    inside, restored = dynamic_special_model()
    assert inside == 2
    assert restored == 1
    print("SPECIAL binding witness: lexical=1 dynamic=2 restored=1 PASS")


if __name__ == "__main__":
    main()
