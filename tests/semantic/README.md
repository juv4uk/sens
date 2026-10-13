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

`filter-core4-d4-law.bits` is a binary SENS self-verdict for Core4's
Lisp-owned `filter`. D6 FILTER applies D3 ATOM to a quoted list containing
D3 identities `001`, nested `(010)`, and `011`. The program checks its
first result with D3 EQ, its second item through CAR/CDR, and the exact end
with D4 NULL. A failed membership, order, or length check calls the
deliberately unbound `filter-law-fail` head. It never calls the non-callable
D8 EQUAL identity, and no host language contains the expected list.
