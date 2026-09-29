; #1711 — current four-Core architectural boundary.
;
; Core profiles share one Function8 identity space and one predicate/control
; foundation. A profile may experiment outside that foundation, but it may not
; redefine ATOM, EQ or COND.
;
; Historical profile-specific truth/result-domain contracts remain in git
; history/research only. They are not active authority.

(core-profile-contract/3

  ((identity . authority)
   (owner . sens)
   (function-identity-space . shared-function8)
   (semantic-registry . shared)
   (profile-may-mint-function . forbidden)
   (profile-may-renumber-function . forbidden)
   (backend-may-own-language-meaning . forbidden))

  ((identity . universal-foundation)
   (applies-to . (core1 core2 core3 core4))
   (predicate-result . exact-one-bit)
   (atom-function . 00000010)
   (atom-law . atomic-or-non-pair-question)
   (eq-function . 00000011)
   (eq-law . admitted-atom-identity-question)
   (cond-function . 00000111)
   (cond-clause . (test expression))
   (cond-select . exact-one)
   (cond-skip . exact-zero)
   (cond-exhaustion . structural-empty)
   (graded-predicate-answers . forbidden)
   (profile-specific-foundation-law . forbidden))

  ((identity . profile-freedom)
   (outside-universal-foundation . allowed)
   (core1-role . bootstrap-historical-root)
   (core2-role . compatibility-study)
   (core3-role . experimental-kernel-laboratory)
   (core4-role . creative-language)
   (native-observation-may-ratify-language-law . no)
   (mechanism-may-change-function-identity . no)
   (implicit-fallback-to-another-profile . forbidden))

  ((identity . migration)
   (lisp-semantic-witness . issue-1709)
   (universal-fixture . issue-1664)
   (old-profile-truth-contracts . historical-only)
   (old-core4-graded-logic . deferred-research)))