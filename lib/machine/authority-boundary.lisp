; #150/#211 — one-way authority boundary for machine/backend data.
;
; Lisp semantics may be projected into machine representation. Machine facts
; may describe CPU capabilities, instruction forms, registers, encodings and
; ABI details, but none of those facts may allocate/rename language meaning or
; become their own semantic answer key.
;
; This file is Lisp-owned policy data. Host tooling may transport and enforce
; it, but the authority direction and prohibitions are stated here.

(machine-authority-boundary/1
  (semantic-authority language-contract.lisp+ratified-domain-laws)
  (machine-root lib/machine)
  (public-api-excluded-root lib/machine)
  (machine-public-api-admission explicit-ratification-only)

  (lowering-direction semantic-to-machine)
  (reverse-authority machine-to-semantic forbidden)

  (semantic-id-from-isa forbidden)
  (semantic-id-from-cpu-profile forbidden)
  (peer-surface-from-machine forbidden)

  ; #211 anti-hybrid hardening. A machine/native observation may verify a
  ; realization but may not define the language result it is compared against.
  (machine-semantic-answer-key forbidden)
  (native-only-semantic-witness forbidden)
  (independent-semantic-witness required)
  (representation-specific-meaning forbidden)
  (machine-layer-replaceable required)
  (capability-provenance lib/machine/capability-provenance.lisp)

  (diagnostic machine-authority-boundary-violation)
  (diagnostic machine-semantic-hybrid-violation))
