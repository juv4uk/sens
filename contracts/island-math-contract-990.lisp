; island-math-contract-990.lisp — four-island mathematical contract.
;
; This artifact is a ratification projection, not semantic authority.
; Semantic identities come only from lib/surface/semantic-registry.lisp.
; Capability evidence is supplied by #988/#1002 and execution evidence by #992.
;
; Current four-way shared domain is deliberately narrower than the union of
; island arithmetic. It uses the common bounded exact-integer subset that can
; be witnessed without depending on floating-point, rational-division,
; implementation-width, or language-specific overflow behavior.
;
; External evidence:
;   Common Lisp: ANSI/HyperSpec numeric operations.
;   SWI-Prolog: arithmetic functions +,-,*,abs,min,max.
;   CLIPS 6.4: basic arithmetic and math functions +,-,*,max,min,abs.
;   Datalog #1001: signed-i64 +,-,*,abs,min,max.
;
(island-math-contract/1
  ((contract-status . ratified-candidate)
   (identity-source . "lib/surface/semantic-registry.lisp")
   (capability-source . "#988 + #1002")
   (execution-source . "#992")
   (authority-rule . "semantic-registry-lisp-only")
   (shared-domain . "bounded-exact-integer")
   (integer-bounds . "[-9223372036854775808,9223372036854775807]")
   (arity-policy . "fixed arity in the shared contract")
   (overflow-policy . "outside-shared-domain")
   (producer-error-policy . "preserve-native-error-domain")
   (non-shared-policy . "visible-partial-overlap")
   (machine-policy . "no-ISA-derived-identity"))

  ((operation . "+")
   (semantic-id . "00001100")
   (arity . 2)
   (operand-domain . "signed-i64")
   (result-domain . "signed-i64")
   (law . "exact integer sum when result is in signed-i64")
   (out-of-domain . "result-outside-signed-i64")
   (common-lisp . present)
   (prolog . present)
   (clips . present)
   (datalog . present))

  ((operation . "-")
   (semantic-id . "00001101")
   (arity . 2)
   (operand-domain . "signed-i64")
   (result-domain . "signed-i64")
   (law . "exact integer difference when result is in signed-i64")
   (out-of-domain . "result-outside-signed-i64")
   (common-lisp . present)
   (prolog . present)
   (clips . present)
   (datalog . present))

  ((operation . "*")
   (semantic-id . "00001110")
   (arity . 2)
   (operand-domain . "signed-i64")
   (result-domain . "signed-i64")
   (law . "exact integer product when result is in signed-i64")
   (out-of-domain . "result-outside-signed-i64")
   (common-lisp . present)
   (prolog . present)
   (clips . present)
   (datalog . present))

  ((operation . "abs")
   (semantic-id . "00010000")
   (arity . 1)
   (operand-domain . "signed-i64-except-min")
   (result-domain . "signed-i64")
   (law . "exact non-negative integer magnitude")
   (out-of-domain . "signed-i64-min-has-no-signed-i64-absolute-value")
   (common-lisp . present)
   (prolog . present)
   (clips . present)
   (datalog . present))

  ((operation . "min")
   (semantic-id . "00010001")
   (arity . 2)
   (operand-domain . "signed-i64")
   (result-domain . "signed-i64")
   (law . "smaller exact integer operand")
   (out-of-domain . ())
   (common-lisp . present)
   (prolog . present)
   (clips . present)
   (datalog . present))

  ((operation . "max")
   (semantic-id . "00010010")
   (arity . 2)
   (operand-domain . "signed-i64")
   (result-domain . "signed-i64")
   (law . "larger exact integer operand")
   (out-of-domain . ())
   (common-lisp . present)
   (prolog . present)
   (clips . present)
   (datalog . present))

  ; Deliberately excluded from the four-way contract.
  ((operation . "/")
   (semantic-id . "00001111")
   (common-lisp . partial)
   (prolog . partial)
   (clips . partial)
   (datalog . partial)
   (exclusion-reason . "Datalog #1001 is integer quotient while Common Lisp and Prolog division may produce non-integer numeric results; no common result law ratified"))

  ((operation . "mod")
   (semantic-id . "00010011")
   (common-lisp . partial)
   (prolog . partial)
   (clips . partial)
   (datalog . partial)
   (exclusion-reason . "negative-operand remainder/modulo laws differ: Common Lisp and SWI-Prolog mod use floored division while #1001 Datalog remainder is truncation-based"))

  ((operation . "quotient")
   (semantic-id . "00010100")
   (common-lisp . derivable)
   (prolog . present)
   (clips . present)
   (datalog . present)
   (exclusion-reason . "Common Lisp has no matching primitive with the same admitted identity/contract; derivation is not promoted to native four-way overlap"))

  ((operation . "sqrt")
   (semantic-id . "00010101")
   (common-lisp . present)
   (prolog . present)
   (clips . present)
   (datalog . absent)
   (exclusion-reason . "Datalog #1001 does not admit sqrt"))

  ((operation . "comparisons")
   (semantic-id . ())
   (common-lisp . present)
   (prolog . present)
   (clips . present)
   (datalog . present)
   (exclusion-reason . "kept in the decision/relation semantic layer; not promoted into the mathematical-result primitive contract")))
