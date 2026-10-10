# 4455 bounded CAR/CDR/CONS migration canary

Two historical Core1 sources use proven legacy SID8 heads for CAR, CDR, CONS and QUOTE/EMPTY. The real three-pass migrator projects them to current exact D3/D2 words, then to physical T5 `.sens` bytes. The `.lisp` files remain provenance.

The existing 11-byte `pair-car-cdr.sens` and 10-byte `pair-cons.sens`
remain the **physical packed T5 sources**. Their same-stem files without an
extension are generated, byte-exact spaced-bit views of those bytes, each with
one ordinary ASCII space between exact-width words and one terminal LF. The
two views reuse the already tracked blobs from
`../migration-pair-cohort-main/`; no second encoder or semantic table exists.

The historical 8-bit `.lisp` heads are source-era evidence only. The bounded
migration test must explicitly use `source_era=legacy` and prove that the
ambiguous default `auto` rejects them. This cohort's T5/view parity does
**not** independently establish historical-to-current source oracle parity,
and is not release admission.
