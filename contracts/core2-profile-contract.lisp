; #1133 — authoritative Core2 legacy compatibility profile.
;
; Core2 freezes the last pre-structural/result-domain my-lisp behavior under
; Language Contract 6.0. This is a compatibility profile, not a rollback of
; current Core4 semantics.
;
; Identity direction remains:
;   shared SID -> selected Core2 law/result domain -> admitted mechanism.
;
; Exact historical source baseline:
;   35c88142548dad137689cd69ca91c430da148bea
; The child f5947ee5 activates structural ATOM/EQ result records and therefore
; marks the post-Core2 transition used by this profile.
;
; This file is Lisp-owned authority data.

(core2-profile-contract/1
  ((identity . authority)
   (owner . my-lisp)
   (profile . core2)
   (sid-identity-source . "lib/surface/semantic-registry.lisp")
   (sid-may-be-reminted . no)
   (core4-law-import . forbidden)
   (compatibility-projection . explicit)
   (semantic-authority-transfer . forbidden))

  ((identity . historical-pin)
   (language-contract . (6 0))
   (ratified-date . "2026-09-08")
   (baseline-sha . "35c88142548dad137689cd69ca91c430da148bea")
   (transition-child . "f5947ee5")
   (transition-message . "feat(#218): activate structural atom/eq results after explicit control")
   (status . frozen))

  ((identity . result-domain)
   (truth-value . t)
   (false-value . ())
   (atom-result . historical-t-nil)
   (eq-result . historical-t-nil)
   (equal-result . historical-t-nil)
   (truthiness . every-non-nil-value)
   (numeric-zero-truthiness . true))

  ((identity . conditional)
   (native-clause-shape . two-part)
   (clause-form . (test expression))
   (selection-rule . historical-truthiness)
   (nil-test-selects . no)
   (non-nil-test-selects . yes)
   (core4-three-part-cond . out-of-profile)
   (core4-unsatisfied-conditional . out-of-profile)
   (activation-boundary . session-shared-mechanical-cond-mode)
   (special-form-profile-policy . "contracts/core-special-form-profile-policy.lisp"))

  ((identity . projection)
   (source . "lib/core2.lisp")
   (atom-projection . core2-atom)
   (eq-projection . core2-eq)
   (equal-projection . core2-equal?)
   (truthy-projection . core2-truthy?)
   (two-part-cond-helper . core2-cond-test?)
   (projection-does-not-redefine-core4 . yes))

  ((identity . witnesses)
   (atom-symbol . ("(core2-atom (quote radio))" t))
   (atom-empty . ("(core2-atom (quote ()))" t))
   (atom-pair . ("(core2-atom (quote (radio antenna)))" ()))
   (eq-same . ("(core2-eq (quote radio) (quote radio))" t))
   (eq-distinct . ("(core2-eq (quote radio) (quote antenna))" ()))
   (zero-truthy . ("(core2-truthy? 0)" t))
   (nil-false . ("(core2-truthy? (quote ()))" ())))

  ((identity . acceptance-state)
   (exact-historical-pin-recorded . yes)
   (legacy-t-nil-witnesses . yes)
   (legacy-two-part-cond-law-recorded . yes)
   (core2-library-source . present)
   (special-form-profile-policy-recorded . yes)
   (native-two-part-cond-activation . yes)
   (full-profile-special-form-selection . active)
   (core4-differences-machine-readable . yes)))