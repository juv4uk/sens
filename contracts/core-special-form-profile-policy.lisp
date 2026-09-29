; #1711/#1663 — current shared COND policy.
;
; The selected Core may choose mechanisms outside the shared foundation, but
; Function8 00000111 has one control law across Core1-Core4.

(core-special-form-profile-policy/2
  (owner sens)
  (cond-function 00000111)
  (identity shared-across-profiles)
  (law shared-across-profiles)

  (clause-family two-part)
  (clause-shape (test expression))
  (predicate-result exact-one-bit)
  (select-on exact-one)
  (skip-on exact-zero)
  (exhaustion-result ())
  (empty-is-predicate-answer no)

  (core1 same-foundation-law)
  (core2 same-foundation-law)
  (core3 same-foundation-law)
  (core4 same-foundation-law)

  (three-part-cond forbidden)
  (expected-result-field forbidden)
  (historical-truthiness forbidden)
  (graded-answer-match forbidden)
  (unsatisfied-conditional-as-exhaustion forbidden)

  (profile-selector role-mechanism-only)
  (host-profile-law-table forbidden)
  (semantic-witness issue-1709))