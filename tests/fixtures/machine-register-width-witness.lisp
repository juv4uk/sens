; #491 — register-width discipline after x86-reg-code gained byte aliases.
; The encoder may share one physical register-code mapping across widths, but
; typed operands must not collapse gpr8 into gpr64.

(load "lib/core.lisp")
(load "lib/machine/encoding/x86-64.lisp")
(load "lib/machine/operands/x86-64.lisp")

(0011 machine-register-width-rows
  (0010 ()
    (1110
      (1110 (001 gpr64-rax)
            (x86-gpr64 (001 rax))
            (001 (gpr64 rax)))
      (1110 (001 gpr64-r8)
            (x86-gpr64 (001 r8))
            (001 (gpr64 r8)))
      (1110 (001 gpr64-reject-al)
            (x86-gpr64 (001 al))
            (001 (rejected machine-operand gpr64 al)))
      (1110 (001 gpr64-reject-r8b)
            (x86-gpr64 (001 r8b))
            (001 (rejected machine-operand gpr64 r8b)))
      (1110 (001 gpr8-al)
            (x86-gpr8 (001 al))
            (001 (gpr8 al)))
      (1110 (001 gpr8-spl)
            (x86-gpr8 (001 spl))
            (001 (gpr8 spl)))
      (1110 (001 gpr8-r8b)
            (x86-gpr8 (001 r8b))
            (001 (gpr8 r8b)))
      (1110 (001 gpr8-reject-rax)
            (x86-gpr8 (001 rax))
            (001 (rejected machine-operand gpr8 rax)))
      (1110 (001 setz-al-bytes)
            (x86-encode-setz-r8 (x86-gpr8-value (x86-gpr8 (001 al))))
            (001 (15 148 192)))
      (1110 (001 setz-spl-rex-bytes)
            (x86-encode-setz-r8 (x86-gpr8-value (x86-gpr8 (001 spl))))
            (001 (64 15 148 196)))
      (1110 (001 setz-r8b-rex-bytes)
            (x86-encode-setz-r8 (x86-gpr8-value (x86-gpr8 (001 r8b))))
            (001 (65 15 148 192))))))

(0011 machine-register-width-check
  (0010 (rows)
    (110
      ((010 rows) ()
       (001 (machine-register-width-witness (status pass))))
      ((010 rows) (1)
       (1110
         (001 machine-register-width-witness)
         (001 (status fail))
         (1110 (001 malformed-tail) rows)))
      ((010 rows) (0)
       (001001 ((row (100 rows))
              (name (100 row))
              (actual (1001 row))
              (expected (10011 row)))
         (110
           ((11110111 actual expected) (1)
            (machine-register-width-check (011 rows)))
           ((11110111 actual expected) (0)
            (1110
              (001 machine-register-width-witness)
              (001 (status fail))
              (1110 (001 case) name)
              (1110 (001 expected) expected)
              (1110 (001 actual) actual)))))))))

(machine-register-width-check (machine-register-width-rows))
