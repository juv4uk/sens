; #4342 — canonical target-neutral machine-effect boundary.
;
; This file defines the authority seam only. It deliberately does not enumerate
; an ISA and does not ratify a universal virtual instruction set.
;
; Language meaning is already fixed upstream by the language contract and
; ratified exact-domain laws. A machine effect describes only the mechanism
; required to realize an already-existing meaning. Target-specific forms are a
; later projection and may reject fail-closed without changing that meaning.

(machine-effect-boundary/1
  (role target-neutral-machine-mechanism)
  (semantic-authority upstream-only)
  (semantic-input language-contract.lisp+ratified-domain-laws)
  (machine-effect-semantic-authority forbidden)

  (canonical-machine-effect target-neutral)
  (effect-vocabulary-status bounded-derived-from-witness)
  (global-machine-opcode-enum forbidden)
  (semantic-id-from-machine-effect forbidden)
  (semantic-id-from-target-projection forbidden)

  (projection-direction machine-effect-to-target)
  (reverse-projection-authority forbidden)
  (target-specific-register-before-projection forbidden)
  (target-specific-encoding-before-projection forbidden)
  (target-specific-feature-before-projection forbidden)

  (target-projection-admission fail-closed)
  (target-projection-rejection named)
  (target-projection-may-be-replaceable required)
  (semantic-observable-preserved required)

  (machine-block-container lib/machine/block.lisp)
  (first-proof-slice bounded-vertical-witness)
  (first-proof-status contract-seam-only)
  (diagnostic machine-effect-boundary-violation))
