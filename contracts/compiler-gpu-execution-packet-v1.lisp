; compiler-gpu-execution-packet-v1.lisp
;
; Binary execution transport for already-admitted SENS GPU operations.
; This contract defines transport shape only. Semantic meaning and operation
; admission remain owned by SENS compiler/law machinery.

((schema . compiler-gpu-execution-packet/1)
 (magic . "SGP\\x01")
 (opcode . ((domain-width . exact)
            (domain-payload . exact)
            (admission . compiler-execution-role-from-sens)))
 (inputs . ((count . canonical-unsigned-varint)
            (handle . u64-opaque)))
 (output . ((materialize . 0)
            (handle-slot . 1+u64)))
 (dependency . ((none . 0)
                 (present . 1+u64)))
 (provenance . ((bytes . 32)
                (role . transport-only)
                (recommended-key . semantic-request-sha256)))
 (rules
   . ((binary-first . yes)
      (textual-function-name . forbidden)
      (legacy-sid8-semantic-authority . forbidden)
      (d8-opcode-admission . fail-closed)
      (d7-opcode-admission . fail-closed)
      (unknown-opcode . fail-closed)
      (trailing-bytes . fail-closed)
      (input-count-bound . 1024)
      (scheduler-owner . cml#472)
      (semantic-authority . sens)
      (target-mechanism-owner . downstream))))

; Width and payload are transport fields, not a semantic u8 identity.
; Exact width remains attached to the payload; numeric equality alone never
; collapses domain identities.
