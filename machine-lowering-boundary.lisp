; Machine-readable authority boundary between language meaning and physical target facts.
; This file deliberately contains no target mnemonic, register, opcode, or ISA name.
; SENS owns language meaning and semantic IDs. Hardware specifications own ISA
; facts. SENS may represent and encode those facts. CML remains an optimizer,
; while the host owns only raw executable-memory / invocation mechanisms.
;
; Machine authority is admitted by properties, not by a historical file path or
; implementation name. An encoder/assembler file is only a replaceable carrier.

(machine-lowering-boundary
  (schema machine-lowering-boundary/2)
  (semantic-authority sens)
  (isa-authority hardware-specification)
  (isa-source intel-xed/intel-sdm)
  (isa-representation sens)
  (instruction-encoding sens)
  (optimization-authority cml)
  (portable-monotonic-observation 1075)
  (semantic-id-allocation explicit-language-contract-only)
  (semantic-id-from-isa forbidden)
  (lowering-direction semantic-to-machine)
  (canonical-machine-effect-layer lib/machine/effect-boundary.lisp)
  (lowering-stage semantic-to-machine-effect required)
  (semantic-to-machine-effect-owner lib/machine/lowering/semantic-effects.lisp)
  (lowering-stage machine-effect-to-target-projection required)
  (target-specific-data-before-machine-effect forbidden)
  (machine-effect-semantic-authority forbidden)
  (reverse-authority forbidden)

  ; Admission belongs to a closed witnessed subset, not to asm-x86.lisp,
  ; x86-64.lisp, or any other implementation carrier by name.
  (machine-authority-basis admitted-subset-properties)
  (admitted-subset-owner sens)
  (admitted-subset-closed required)
  (admitted-subset-machine-readable required)
  (admitted-subset-witnessed required)
  (admitted-subset-implementation replaceable)
  (implementation-file-path authority-forbidden)
  (unadmitted-machine-form reject-before-host)
  (canonical-raw-byte-vector-api forbidden)
  (host-execution-input admitted-output-only)

  (raw-execution-mechanism host)
  (machine-text projection-only)
  (machine-bytes lisp-owned-target-product)
  ; 1153 briefly reached main from a compiler-originated experiment. It is burned:
  ; never assign it to another language meaning, while keeping it out of the active
  ; semantic registry because no language contract admitted that operation.
  (retired-semantic-id 1153))
