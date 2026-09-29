; #1711 — DEFERRED RESEARCH OUTPUT BOUNDARY.
;
; The previous Core4 graded predicate-output boundary is not active authority.
; Current predicate output is exactly one contextual bit: 0 NO / 1 YES.
; Rich observations/classifiers, if retained, are separate operations and are
; never the result domain of ATOM/EQ.

(core4-predicate-output-boundary/deferred
  (status research-only)
  (active-authority forbidden)
  (current-output exact-one-bit)
  (structural-kind-as-atom-result forbidden)
  (identity-relation-as-eq-result forbidden)
  (graded-output forbidden)
  (runtime-gate forbidden))