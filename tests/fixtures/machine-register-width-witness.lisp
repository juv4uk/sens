; #491 — register-width discipline after x86-reg-code gained byte aliases.
; The encoder may share one physical register-code mapping across widths, but
; typed operands must not collapse gpr8 into gpr64.

(load "lib/core.lisp")
(load "lib/machine/encoding/x86-64.lisp")
(load "lib/machine/operands/x86-64.lisp")

(def machine-register-width-rows
  (lambda ()
    (list
      (list (quote gpr64-rax)
            (x86-gpr64 (quote rax))
            (quote (gpr64 rax)))
      (list (quote gpr64-r8)
            (x86-gpr64 (quote r8))
            (quote (gpr64 r8)))
      (list (quote gpr64-reject-al)
            (x86-gpr64 (quote al))
            (quote (rejected machine-operand gpr64 al)))
      (list (quote gpr64-reject-r8b)
            (x86-gpr64 (quote r8b))
            (quote (rejected machine-operand gpr64 r8b)))
      (list (quote gpr8-al)
            (x86-gpr8 (quote al))
            (quote (gpr8 al)))
      (list (quote gpr8-spl)
            (x86-gpr8 (quote spl))
            (quote (gpr8 spl)))
      (list (quote gpr8-r8b)
            (x86-gpr8 (quote r8b))
            (quote (gpr8 r8b)))
      (list (quote gpr8-reject-rax)
            (x86-gpr8 (quote rax))
            (quote (rejected machine-operand gpr8 rax)))
      (list (quote setz-al-bytes)
            (x86-encode-setz-r8 (x86-gpr8-value (x86-gpr8 (quote al))))
            (quote (15 148 192)))
      (list (quote setz-spl-rex-bytes)
            (x86-encode-setz-r8 (x86-gpr8-value (x86-gpr8 (quote spl))))
            (quote (64 15 148 196)))
      (list (quote setz-r8b-rex-bytes)
            (x86-encode-setz-r8 (x86-gpr8-value (x86-gpr8 (quote r8b))))
            (quote (65 15 148 192))))))

(def machine-register-width-check
  (lambda (rows)
    (cond
      ((atom? rows) (structural-kind empty-list)
       (quote (machine-register-width-witness (status pass))))
      ((atom? rows) (structural-kind atom)
       (list
         (quote machine-register-width-witness)
         (quote (status fail))
         (list (quote malformed-tail) rows)))
      ((atom? rows) (structural-kind pair)
       (let* ((row (car rows))
              (name (car row))
              (actual (second row))
              (expected (third row)))
         (cond
           ((equal? actual expected) (structural-relation same)
            (machine-register-width-check (cdr rows)))
           ((equal? actual expected) (structural-relation distinct)
            (list
              (quote machine-register-width-witness)
              (quote (status fail))
              (list (quote case) name)
              (list (quote expected) expected)
              (list (quote actual) actual)))))))))

(machine-register-width-check (machine-register-width-rows))
