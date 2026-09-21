; error-kind-vocabulary.lisp — language-owned current error-category ledger.
;
; #1104 consolidates already-admitted observable failure categories above Rust.
; It does NOT invent a new category or make implementation prose authoritative.
;
; Provenance:
; - Contract 3.0: Parse, UnknownSymbol, Arity, Type, InvalidForm,
;   NumericOverflow, OutOfMemory, DivisionByZero.
; - #250 / #811 replay law: MechanismUnavailable distinguishes an unreadable
;   mechanism/capability registry from semantic absence.
; - Contract 8.0 / ADR-012: UnsatisfiedConditional names exhaustion of a
;   structurally valid canonical three-part COND.
; - ADR-011: category is contractual; message/span/detail remain diagnostic.
;
; The ordered category list below is the machine-readable current vocabulary
; that implementation observers must match. Rust may represent these categories,
; but Rust does not own admission.

(error-kind-vocabulary/1
  ((status . current)
   (authority . language-owned-consolidation)
   (observation-identity . category-only)
   (message-text . diagnostic)
   (source-span . diagnostic)
   (categories .
     ("Parse"
      "UnknownSymbol"
      "Arity"
      "Type"
      "InvalidForm"
      "UnsatisfiedConditional"
      "MechanismUnavailable"
      "OutOfMemory"
      "NumericOverflow"
      "DivisionByZero"))
   (provenance .
     ((contract-3.0 .
       ("Parse"
        "UnknownSymbol"
        "Arity"
        "Type"
        "InvalidForm"
        "OutOfMemory"
        "NumericOverflow"
        "DivisionByZero"))
      (issue-250 .
       ("MechanismUnavailable"))
      (contract-8.0 .
       ("UnsatisfiedConditional"))))))
