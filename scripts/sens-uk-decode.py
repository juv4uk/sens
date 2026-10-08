#!/usr/bin/env python3
"""Packed exact-width SENS source bytes -> canonical Ukrainian source."""

from __future__ import annotations

import sys

from domain_word_carrier import CarrierError
from sens_source_pair_codec import decode_ukrainian


def main() -> int:
    try:
        sys.stdout.buffer.write(decode_ukrainian(sys.stdin.buffer.read()))
    except (CarrierError, OSError, UnicodeError, ValueError, KeyError) as exc:
        print(f"sens-uk-decode: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
