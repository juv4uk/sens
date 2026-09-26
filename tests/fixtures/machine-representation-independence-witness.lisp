; #211 — representation-independence witness.
; Lisp's existing addition is the answer key. The machine layer realizes the
; same inputs twice: once through the canonical bounded lowerer (RCX scratch),
; once through an alternate admitted register choice (R8 scratch).
; The shell observes only the named pass/fail envelope.

(load "lib/core.lisp")
(load "lib/machine/encoding/x86-64.lisp")
(load "lib/machine/admission/x86-64.lisp")
(load "lib/machine/lowering/semantic-x86-64.lisp")

(def machine-representation-semantic-reference (+ 2 3))

(def machine-representation-primary
  (x86-call-admitted-u64
    (x86-lower-add-u64-forms 2 3)
    0))

(def machine-representation-alternate
  (x86-call-admitted-u64
    (quote
      ((mov-r64-imm64 rax 2)
       (mov-r64-imm64 r8 3)
       (add-r64-r64 rax r8)
       (ret)))
    0))

(def machine-representation-witness
  (lambda ()
    (cond
      ((equal?
         machine-representation-primary
         machine-representation-semantic-reference)
       (1)
       (cond
         ((equal?
            machine-representation-alternate
            machine-representation-semantic-reference)
          (1)
          (quote (machine-representation-independence-witness (status pass))))
         ((equal?
            machine-representation-alternate
            machine-representation-semantic-reference)
          (0)
          (list
            (quote machine-representation-independence-witness)
            (quote (status fail))
            (list (quote case) (quote alternate-register))
            (list (quote semantic) machine-representation-semantic-reference)
            (list (quote actual) machine-representation-alternate)))))
      ((equal?
         machine-representation-primary
         machine-representation-semantic-reference)
       (0)
       (list
         (quote machine-representation-independence-witness)
         (quote (status fail))
         (list (quote case) (quote canonical-register))
         (list (quote semantic) machine-representation-semantic-reference)
         (list (quote actual) machine-representation-primary))))))

(machine-representation-witness)
