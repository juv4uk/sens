# #2000 unbounded-width scaling benchmark

Research-only. The carrier structs have no language-level maximum width.

Candidates:
- dynamic heap bytes;
- small-inline through 64 bits, dynamic spill above 64.

4096 is a test point only, not a carrier/type ceiling.

Every invocation checks before measurement:
- exact-width equality;
- equal numeric zero at adjacent widths remains different identity;
- append then parent restores the original word;
- original word is an exact prefix of its appended child.

Smoke:

    python3 benchmarks/unbounded-width/run.py --smoke

Full width/operation sweep:

    python3 benchmarks/unbounded-width/run.py

The first spilled append/parent implementation is intentionally simple and may be O(width).
That slope is mechanism evidence, not a semantic requirement; later chunked candidates may improve it.