# Retired SI-quantity runtime gate in current exact-D1/D3 slice

**Reason:** `tests/fixtures/exact-quantity-arithmetic-witness.lisp` still contains
three-field historical COND clauses and cannot execute under ratified D3:110
`(test expression)` with exact D1 1/0 predicate values. Re-enabling implicit
truthiness or widening COND is explicitly forbidden.

**Action:** Only its **automatic execution in**
`scripts/test-current-semantic-slice.sh` has been retired. The original
quantity research file remains in the repository for the existing
`scripts/check-world-knowledge-authority.py` source audit and for a future
fully ratified scientific-law migration. This is *not* deletion of SI laws.

**Replacement (distinct claim):**
`examples/binary/d3-cond-program.sens` is a physical 31-byte T5 program.
It proves exact D2 word-boundary admission and D3:110 COND choosing between
exact D1:0 and D1:1 branches. This proves **no** scientific quantity arithmetic
and **no** equivalence with the legacy fixture. The accompanying checked binary
SHA-256 is
`b93b49223f5c845a4ae86392c463b59699470faeb4c8ac3cf06982bc2cb232df`.

**Admissible reinstatement of quantity evidence:** translate *each* quantity
row into ratified binary-domain operations, define exact D7 bindings without
textual executable names, establish independent SI value/unit oracle parity,
generate physical T5 `.sens` bytes, and check both CLIs plus the external SI
oracle on an immutable SHA. Until those proofs exist, scientific quantity
coverage is **BLOCKED_NOT_MIGRATED**, not PASS.

**CI invariant:** deletion of obsolete automatic benchmark workflows or a
legacy runtime probe may never delete malformed-T5 rejection, the canonical
D2 reader, ratified D1/D3 control checks, or the source authority audit.
