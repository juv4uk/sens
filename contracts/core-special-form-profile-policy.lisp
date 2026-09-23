; #1133/#1131 — Lisp-owned special-form profile policy.
;
; One shared COND SID keeps one semantic identity across all Core profiles.
; The selected Core chooses the admitted law/result domain BEFORE mechanism
; execution. This file is authority data; a host may transport the selected
; profile but must not invent or reinterpret the law recorded here.
;
; Flat rows keep the policy easy to audit and executable from ordinary Lisp:
;   (core-special-form-profile-policy/1 ROW ...)

(core-special-form-profile-policy/1
  (owner my-lisp)
  (cond-sid 00000111)
  (identity shared-across-profiles)
  (selection-order profile-before-special-form-mechanism)

  ; Core1 remains on its separately pinned historical evaluator mechanism.
  (core1
    clause-family historical-mccarthy
    law-source contracts/core1-bootstrap-contract.lisp
    activation historical-mechanism)

  ; Contract 6 compatibility: legacy truthiness and NIL exhaustion.
  (core2
    clause-family two-part
    selection-rule historical-truthiness
    exhaustion-result ()
    contract (6 0)
    law-source contracts/core2-profile-contract.lisp
    activation runtime-profile-hook-required)

  ; Contract 7 predates the Contract-8 explicit-result COND revolution.
  (core3
    clause-family two-part
    selection-rule historical-truthiness
    exhaustion-result ()
    contract (7 0)
    law-source contracts/core3-profile-contract.lisp
    activation experimental-profile)

  ; Contract 8: explicit domain-result matching and named exhaustion failure.
  (core4
    clause-family three-part
    selection-rule explicit-result-match
    exhaustion-result UnsatisfiedConditional
    contract (8 0)
    law-source language-contract.lisp
    activation current)

  (implicit-profile-selection forbidden)
  (global-two-part-bridge retirement-required)
  (host-profile-law-table forbidden)
  (runtime-profile-selector
    owner my-lisp
    state pending-mechanical-hook))