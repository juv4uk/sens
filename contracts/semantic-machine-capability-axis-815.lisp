; #815 — target-neutral machine capability axis.
; Projection/evidence only; not a semantic registry.
; Canonical SID authority: lib/surface/semantic-registry.lisp.
; Realization evidence: lib/machine/capability-provenance.lisp.

(semantic-machine-capability-axis/1
  (semantic-authority . "lib/surface/semantic-registry.lisp")
  (machine-evidence-authority . "lib/machine/capability-provenance.lisp")
  (rows
    (((sid . "00001100") (capability . bounded-integer-add)
      (targets . (x86-64)) (status . witnessed) (provenance . add-u64))
     ((sid . "00000011") (capability . equality-compare)
      (targets . (x86-64)) (status . witnessed) (provenance . eq-cond-u64))
     ((sid . "00000111") (capability . conditional-branch)
      (targets . (x86-64)) (status . witnessed) (provenance . eq-cond-u64))
     ((sid . "00000100") (capability . pair-field-store)
      (targets . (x86-64)) (status . witnessed) (provenance . car-cons-u64))
     ((sid . "00000101") (capability . pair-field-load-head)
      (targets . (x86-64)) (status . witnessed) (provenance . car-cons-u64))
     ((sid . "00000110") (capability . pair-field-load-tail)
      (targets . (x86-64)) (status . no-execution-witness) (provenance . ()))))))