; #211 — representation-independence witness.
; Lisp's existing addition is the answer key. The machine layer realizes the
; same inputs twice: once through the canonical bounded lowerer (RCX scratch),
; once through an alternate admitted register choice (R8 scratch).
; The shell observes only the named pass/fail envelope.

(load "lib/core.lisp")
(load "lib/machine/encoding/x86-64.lisp")
(load "lib/machine/admission/x86-64.lisp")
(load "lib/machine/lowering/semantic-x86-64.lisp")

(00001001 machine-representation-semantic-reference (00001100 #b10 #b11))

(00001001 machine-representation-primary
  (x86-call-admitted-u64
    (x86-lower-add-u64-forms #b10 #b11)
    #b0))

(00001001 machine-representation-alternate
  (x86-call-admitted-u64
    (00000001
      ((mov-r64-imm64 rax #b10)
       (mov-r64-imm64 r8 #b11)
       (add-r64-r64 rax r8)
       (ret)))
    #b0))

(00001001 machine-representation-witness
  (00001000 ()
    (00000111
      ((00100010
         machine-representation-primary
         machine-representation-semantic-reference)
       (1)
       (00000111
         ((00100010
            machine-representation-alternate
            machine-representation-semantic-reference)
          (#b1)
          (00000001 (machine-representation-independence-witness (status pass))))
         ((00100010
            machine-representation-alternate
            machine-representation-semantic-reference)
          (0)
          (00100111
            (00000001 machine-representation-independence-witness)
            (00000001 (status fail))
            (00100111 (00000001 case) (00000001 alternate-register))
            (00100111 (00000001 semantic) machine-representation-semantic-reference)
            (00100111 (00000001 actual) machine-representation-alternate)))))
      ((00100010
         machine-representation-primary
         machine-representation-semantic-reference)
       (0)
       (00100111
         (00000001 machine-representation-independence-witness)
         (00000001 (status fail))
         (00100111 (00000001 case) (00000001 canonical-register))
         (00100111 (00000001 semantic) machine-representation-semantic-reference)
         (00100111 (00000001 actual) machine-representation-primary))))))

(machine-representation-witness)
