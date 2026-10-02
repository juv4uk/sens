; #2367 — one active SENS core.
;
; Active language execution has one core source: lib/core.lisp.
; Historical Core1 evidence, retired Core2 compatibility, and Core3 mechanism
; experiments may remain as provenance/labs, but they are not peer language
; cores and may not select a different semantic law.

(core-profile-contract/3
  ((identity . authority)
   (owner . sens)
   (active-core-count . 1)
   (active-core-source . "lib/core.lisp")
   (active-core-fasl . "lib/core.lisp.fasl")
   (semantic-registry . shared)
   (foundation-law . shared)
   (backend-may-own-language-meaning . forbidden)
   (historical-profile-may-govern-active-language . forbidden))

  ((identity . shared-foundation)
   (predicate-result . exact-one-bit)
   (atom-function . 00000010)
   (eq-function . 00000011)
   (cond-function . 00000111)
   (cond-clause . (test expression))
   (cond-select . exact-one)
   (cond-skip . exact-zero)
   (cond-exhaustion . structural-empty)
   (generic-truthiness . forbidden)
   (graded-predicate-answer . forbidden))

  ((identity . core1)
   (role . bootstrap-historical-witness)
   (execution-source . "lib/core1.lisp")
   (historical-mechanism-map . "contracts/core1-historical-sid-map.lisp")
   (active-runtime-core . no)
   (status . provenance))

  ((identity . core2)
   (role . retired-compatibility-history)
   (execution-source . "lib/core2.lisp")
   (active-runtime-core . no)
   (status . retired))

  ((identity . mechanism-lab)
   (role . mechanism-laboratory)
   (historical-name . core3)
   (execution-source . "lib/mechanism-lab.lisp")
   (mechanism-families . (common-lisp prolog clips datalog))
   (active-runtime-core . no)
   (native-observation-is-language-law . no)
   (status . laboratory))

  ((identity . core4)
   (role . folded-former-name)
   (folded-into . "lib/core.lisp")
   (former-source . "lib/core4.lisp")
   (active-runtime-core . no)
   (status . historical-alias))

  ((identity . public-api-discovery)
   (current-source . "lib/core.lisp")
   (historical-source . "lib/core1.lisp")
   (historical-source . "lib/core1-compiler-sid-resolver.lisp")
   (historical-source . "lib/core1-sid8-bootstrap-overlay.lisp")
   (historical-source . "lib/core2.lisp")
   (laboratory-source . "lib/mechanism-lab.lisp")
   (former-source . "lib/core4.lisp"))

  ((identity . selection-law)
   (language-core-selection . unnecessary)
   (mechanism-selection . separate)
   (bootstrap-witness-selection . separate)
   (semantic-law-remains-single . required)
   (implicit-profile-fallback . forbidden)))
