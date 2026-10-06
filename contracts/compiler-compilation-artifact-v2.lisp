; contracts/compiler-compilation-artifact-v2.lisp
; sens#3839 — whole-program backend-neutral compilation artifact.
;
; Version 1 remains the merged single-request witness from #3836.
; Version 2 is the fixed-point/self-host whole-program value produced by SENS.

(compiler-compilation-artifact-contract
  (schema . compiler-compilation-artifact/2)
  (status . current-selfhost-whole-program)
  (producer-authority . sens-compiler-nucleus)
  (installation-authority . none)
  (backend-policy . none)

  ; Canonical ordinary-SENS value shape:
  ;
  ; (compiler-compilation-artifact/2
  ;   sens-compiler-program-data/1
  ;   "<program-sha256>"
  ;   "<ordered-request-sequence-sha256>"
  ;   <provenance>
  ;   <ordered-requests>
  ;   <required-capabilities>
  ;   canonical-backend-neutral)
  ;
  ; The digest mechanism is injected as representation-only capability.
  ; SENS decides which values are hashed and owns this composition.

  (fields
    (program-data-schema exact-symbol)
    (program-sha256 lowercase-hex-64)
    (request-sequence-sha256 lowercase-hex-64)
    (provenance ordinary-sens-data)
    (ordered-requests ordinary-sens-data)
    (required-capabilities ordinary-sens-data)
    (artifact-status canonical-backend-neutral))

  (invariants
    (program-order-preserved . yes)
    (request-order-preserved . yes)
    (proof-lineage-inside-requests . yes)
    (authority-lineage-inside-provenance . yes)
    (compiler-nucleus-digest-inside-provenance . yes)
    (digest-selection-owned-by-sens . yes)
    (digest-bytes-mechanism-only . yes)
    (target-register-allocation . forbidden)
    (cuda-ptx-sass . forbidden)
    (fpga-placement . forbidden)
    (graal-ir . forbidden)
    (sid8-sens8-semantic-fallback . forbidden))

  (compatibility
    (compiler-compilation-artifact/1 . retained-single-request-witness)
    (compiler-compilation-artifact/2 . whole-program-selfhost-witness)))
