; #1131 / #1703 / #2367 — historical Core roles under one active SENS Core.
;
; lib/core.lisp is the one active language bootstrap. Numbered Core sources
; remain provenance, compatibility study or laboratory evidence. A historical
; profile may select a research/mechanism viewpoint; it does not select a
; different language identity or foundation law.

(core-profile-contract/2
  ((identity . authority)
   (owner . sens)
   (semantic-identity-space . shared-binary-domains)
   (semantic-registry . shared)
   (foundation-law . shared)
   (profile-may-mint-domain-resident . forbidden)
   (profile-may-renumber-domain-resident . forbidden)
   (profile-may-override-foundation . forbidden)
   (backend-may-own-language-meaning . forbidden))

  ((identity . shared-foundation)
   (predicate-result . exact-one-bit)
   (atom-object . (Core.D3 "010"))
   (eq-object . (Core.D3 "111"))
   (cond-object . (Core.D3 "011"))
   (cond-clause . (test expression))
   (cond-select . exact-one)
   (cond-skip . exact-zero)
   (cond-exhaustion . structural-empty)
   (generic-truthiness . forbidden)
   (graded-predicate-answer . forbidden)
   (profile-specific-foundation-law . forbidden))

  ((identity . core1)
   (role . bootstrap-historical-root)
   (execution-source . "lib/core1.lisp")
   (historical-mechanism-map . "contracts/core1-historical-sid-map.lisp")
   (historical-semantics . provenance-only)
   (status . admitted))

  ((identity . core2)
   (role . compatibility-study)
   (execution-source . "lib/core2.lisp")
   (historical-semantics . provenance-only)
   (semantic-wrapper-layer . absent)
   (status . admitted))

  ((identity . core3)
   (role . experimental-kernel-laboratory)
   (execution-source . "lib/core3.lisp")
   (mechanism-families . (common-lisp prolog clips datalog))
   (native-observation-preserved . yes)
   (native-observation-is-language-law . no)
   (selector-owner . sens)
   (lowering-owner . sens)
   (status . experimental))

  ((identity . core4)
   (role . historical-creative-profile)
   (execution-source . "lib/core4.lisp")
   (historical-semantics . provenance-only)
   (status . historical))

  ((identity . active-core)
   (role . current-language-bootstrap)
   (execution-source . "lib/core.lisp")
   (fasl-source . "lib/core.lisp.fasl")
   (numbered-core-authority . forbidden)
   (status . active))

  ((identity . public-api-discovery)
   (current-profile-source . "lib/core.lisp")
   (public-api-excluded-source . "lib/core1.lisp")
   (public-api-excluded-source . "lib/core1-compiler-sid-resolver.lisp")
   (public-api-excluded-source . "lib/core1-sid8-bootstrap-overlay.lisp")
   (public-api-excluded-source . "lib/core2.lisp")
   (public-api-excluded-source . "lib/core3.lisp")
   (public-api-excluded-source . "lib/core4.lisp"))

  ((identity . profile-selection)
   (role . mechanism-selection-only)
   (same-domain-qualified-identity-law . required)
   (foundation-law-remains-shared . required)
   (profile-selection-may-change-foundation-law . no)
   (mechanism-selection-may-ratify-language-law . no)
   (implicit-fallback-to-another-profile . forbidden)))