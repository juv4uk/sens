# SENS-owned semantic tests

These are executable language-owned semantic witnesses, not host-language
semantic oracles.

`d1-d3-control-law.bits` contains only exact-width 0/1 domain words plus D2
framing. Correct D1/D3 semantics reaches exact D1 `1`. A wrong ATOM, EQ, or
COND decision routes into an intentionally non-callable D1 head so SENS itself
rejects the witness.

`d1-d3-control-law.sens` is the canonical physical T5 form of exactly those
words.

Rust, Python and shell are allowed to transport bytes, invoke SENS, and retain
evidence. They do not define the expected logic of this witness.

`result-status-d1-law.bits` extends the same rule into the reasoning outcome
layer. Its executable heads include exact D9 `RESULT-TAGGED?` and
`MAKE-PROVED`, while D3 `COND/EQ/QUOTE` and D1 `0/1` carry the verdict.
If either the true or false result law is wrong, SENS takes an intentionally
non-callable D1 branch and rejects its own witness. The host runner therefore
does not need an expected semantic value.

`narrate-d3-atom-eq-law.bits` is a short binary SENS structural premise for
`narrate-fact`: D4 CDDR ends a proper two-cell list; a three-cell list
has non-atomic CDDR and empty D5 CDDDR; the dotted non-NIL tail must fail
an exact D3 EQ with NIL. Unexpected branches call non-callable D1:0.
`narrate-d3-atom-eq-mutant.bits` changes exactly one bit in D4 selector
0111→0110. These fixtures are SENS programs, not host-language oracles.
They do **not** assert that D9 NARRATE-FACT is physically callable.
A physical .sens is not fabricated here: only the existing canonical T5
encoder can produce it, and quarantined Actions must not run.
