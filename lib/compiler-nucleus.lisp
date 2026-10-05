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
; Human spellings below are source/UI projections only.  The focused guard
; lowers this file before execution and rejects any historical Sid/Call node,
; proving the D3/D4 operations enter the runtime as exact DomainCall identities.

(define compiler-authority-find
  (lambda (identity rows)
    (cond
      ((atom rows) ())
      ((eq identity (car (car rows))) (car rows))
      ((atom ()) (compiler-authority-find identity (cdr rows))))))

(define compiler-nucleus
  (lambda (identity authority)
    (compiler-authority-find identity authority)))
