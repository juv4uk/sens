; #491 — register-width discipline after x86-reg-code gained byte aliases.
; The encoder may share one physical register-code mapping across widths, but
; typed operands must not collapse gpr8 into gpr64.

(load "lib/core.lisp")
(load "lib/machine/encoding/x86-64.lisp")
(load "lib/machine/operands/x86-64.lisp")

(00001001 machine-register-width-rows
  (00001000 ()
    (00100111
      (00100111 (00000001 gpr64-rax)
            (x86-gpr64 (00000001 rax))
            (00000001 (gpr64 rax)))
      (00100111 (00000001 gpr64-r8)
            (x86-gpr64 (00000001 r8))
            (00000001 (gpr64 r8)))
      (00100111 (00000001 gpr64-reject-al)
            (x86-gpr64 (00000001 al))
            (00000001 (rejected machine-operand gpr64 al)))
      (00100111 (00000001 gpr64-reject-r8b)
            (x86-gpr64 (00000001 r8b))
            (00000001 (rejected machine-operand gpr64 r8b)))
      (00100111 (00000001 gpr8-al)
            (x86-gpr8 (00000001 al))
            (00000001 (gpr8 al)))
      (00100111 (00000001 gpr8-spl)
            (x86-gpr8 (00000001 spl))
            (00000001 (gpr8 spl)))
      (00100111 (00000001 gpr8-r8b)
            (x86-gpr8 (00000001 r8b))
            (00000001 (gpr8 r8b)))
      (00100111 (00000001 gpr8-reject-rax)
            (x86-gpr8 (00000001 rax))
            (00000001 (rejected machine-operand gpr8 rax)))
      (00100111 (00000001 setz-al-bytes)
            (x86-encode-setz-r8 (x86-gpr8-value (x86-gpr8 (00000001 al))))
            (00000001 (15 148 192)))
      (00100111 (00000001 setz-spl-rex-bytes)
            (x86-encode-setz-r8 (x86-gpr8-value (x86-gpr8 (00000001 spl))))
            (00000001 (64 15 148 196)))
      (00100111 (00000001 setz-r8b-rex-bytes)
            (x86-encode-setz-r8 (x86-gpr8-value (x86-gpr8 (00000001 r8b))))
            (00000001 (65 15 148 192))))))

(00001001 machine-register-width-check
  (00001000 (rows)
    (00000111
      ((00000010 rows) ()
       (00000001 (machine-register-width-witness (status pass))))
      ((00000010 rows) (1)
       (00100111
         (00000001 machine-register-width-witness)
         (00000001 (status fail))
         (00100111 (00000001 malformed-tail) rows)))
      ((00000010 rows) (0)
       (10011101 ((row (00000101 rows))
              (name (00000101 row))
              (actual (00101111 row))
              (expected (00110000 row)))
         (00000111
           ((00100010 actual expected)
            (machine-register-width-check (00000110 rows)))
           ((00100010 (00100010 actual expected)
     (00100010 (00000001 d1-no-left) (00000001 d1-no-right)))
            (00100111
              (00000001 machine-register-width-witness)
              (00000001 (status fail))
              (00100111 (00000001 case) name)
              (00100111 (00000001 expected) expected)
              (00100111 (00000001 actual) actual)))))))))

(machine-register-width-check (machine-register-width-rows))
