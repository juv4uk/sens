; #1001 — Datalog integer execution capability under exact SID8 identity.
;
; Canon/function-table owns every SID, meaning, domain and law.
; Datalog owns only bounded integer execution machinery.
; Semantic operation identity comes only from the shared 8-bit SID.
; Payload bytes carry arguments only; operator text is forbidden as identity.

(datalog-math-capability/2
  ((kernel . wsm-datalog-kernel)
   (numeric-domain . signed-i64)
   (expression-evaluator . native)
   (semantic-authority . my-lisp)
   (semantic-operation-selector . exact-sid8)
   (payload-role . arguments-only)
   (operator-text-as-semantic-identity . forbidden)
   (unsupported-extension-policy . explicit)
   (witness . crates/wsm-datalog-kernel/tests/arithmetic_execution_1001.rs))

  ((sid . 00001100) (mechanism . integer-add) (native . present))
  ((sid . 00001101) (mechanism . integer-subtract) (native . present))
  ((sid . 00001110) (mechanism . integer-multiply) (native . present))
  ((sid . 00001111) (mechanism . integer-divide) (native . present))
  ((sid . 00010000) (mechanism . integer-abs) (native . present))
  ((sid . 00010001) (mechanism . integer-min) (native . present))
  ((sid . 00010010) (mechanism . integer-max) (native . present))
  ((sid . 00010011) (mechanism . integer-mod) (native . present))
  ((sid . 00010100) (mechanism . integer-quotient) (native . present))

  ((failure . division-by-zero)
   (status . typed-kernel-error)
   (identity . datalog-math-division-by-zero))

  ((failure . overflow)
   (status . typed-kernel-error)
   (identity . datalog-math-overflow))
)