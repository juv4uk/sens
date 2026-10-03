# #2709 — LISP 1.5 arithmetic primary-source ingest

This sidecar records **attestation**, not placement.

Primary source: LISP 1.5 Programmer's Manual, Chapter IV §4.2 (printed pp. 25–27) and Appendix A arithmetic table (printed pp. 63–64).
The slice records 26 arithmetic/numeric/logical-word capabilities while leaving
every binary object `UNPLACED` and every current domain candidate unresolved.

The strongest negative control is historical `RECIP`:

```text
LISP 1.5 fixed-point RECIP(x) -> 0
Core-Math exact-Q RECIP(2)    -> 1/2
```

Therefore shared human spelling or broad mathematical intent is not evidence
for shared semantic law, domain, or binary identity.

This slice deliberately does not claim whether any row predates Lisp 1.5.
