; lib/compiler-nucleus.lisp
; sens#3759 / #3803 — first executable compiler nucleus slice owned by SENS.
;
; N0 is deliberately smaller than the final self-hosted compiler:
; - exact DomainIdentity is already a first-class runtime value;
; - authority rows are supplied as data by the bootstrap boundary;
; - this program performs the authority lookup/normalization itself;
; - it contains no D3 coordinate table, no Sid8/Sens8 identity, and no backend
;   opcode/mechanism table.
;
; Authority row shape for this bounded slice:
;
;   (exact-domain-identity execution-role proof-ref provenance)
;
; The role/proof/provenance payload is opaque here.  #3806 moves construction
; of that authority projection from the Rust/bootstrap oracle into executable
; SENS-owned law.  Until then this file is a real compiler component, but only
; a PARTIAL nucleus and not a self-host/fixed-point claim.
;
; Ukrainian spellings below are source/UI projections only.  They are chosen
; because the current registry routes Ukrainian D3/D4 surfaces directly to
; exact-domain identities.  The focused guard lowers this file before execution
; and rejects any historical Sid/Call node.

(визначити compiler-authority-find
  (функція (identity rows)
    (за-умовою
      ((атом? rows) ())
      ((тотожне? identity (перше (перше rows))) (перше rows))
      ((атом? ()) (compiler-authority-find identity (решта rows))))))

(визначити compiler-nucleus
  (функція (identity authority)
    (compiler-authority-find identity authority)))


; Representation-only bootstrap seam for #3808.
; DECOMPOSE is an explicitly supplied first-class mechanism.  The language
; chooses when to invoke it; the host function may reveal only exact width/bits
; and has no identity->meaning authority.
(визначити compiler-domain-shape
  (функція (decompose identity)
    (decompose identity)))
