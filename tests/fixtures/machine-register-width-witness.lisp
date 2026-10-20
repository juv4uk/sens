; #491 — register-width discipline after x86-reg-code gained byte aliases.
; The encoder may share one physical register-code mapping across widths, but
; typed operands must not collapse gpr8 into gpr64.

(load "lib/core.lisp")
(load "lib/machine/encoding/x86-64.lisp")
(load "lib/machine/operands/x86-64.lisp")

(визначити machine-register-width-rows
  (функція ()
    (список
      (список (як-є gpr64-rax)
            (x86-gpr64 (як-є rax))
            (як-є (gpr64 rax)))
      (список (як-є gpr64-r8)
            (x86-gpr64 (як-є r8))
            (як-є (gpr64 r8)))
      (список (як-є gpr64-reject-al)
            (x86-gpr64 (як-є al))
            (як-є (rejected machine-operand gpr64 al)))
      (список (як-є gpr64-reject-r8b)
            (x86-gpr64 (як-є r8b))
            (як-є (rejected machine-operand gpr64 r8b)))
      (список (як-є gpr8-al)
            (x86-gpr8 (як-є al))
            (як-є (gpr8 al)))
      (список (як-є gpr8-spl)
            (x86-gpr8 (як-є spl))
            (як-є (gpr8 spl)))
      (список (як-є gpr8-r8b)
            (x86-gpr8 (як-є r8b))
            (як-є (gpr8 r8b)))
      (список (як-є gpr8-reject-rax)
            (x86-gpr8 (як-є rax))
            (як-є (rejected machine-operand gpr8 rax)))
      (список (як-є setz-al-bytes)
            (x86-encode-setz-r8 (x86-gpr8-value (x86-gpr8 (як-є al))))
            (як-є (15 148 192)))
      (список (як-є setz-spl-rex-bytes)
            (x86-encode-setz-r8 (x86-gpr8-value (x86-gpr8 (як-є spl))))
            (як-є (64 15 148 196)))
      (список (як-є setz-r8b-rex-bytes)
            (x86-encode-setz-r8 (x86-gpr8-value (x86-gpr8 (як-є r8b))))
            (як-є (65 15 148 192))))))

(визначити machine-register-width-check
  (функція (rows)
    (за-умовою
      ((атом? rows)
       (як-є (machine-register-width-witness (status pass))))
      (так
       (нехай ((row (перше rows))
              (name (перше row))
              (actual (друге row))
              (expected (третє row)))
         (за-умовою
           ((однакові? actual expected)
            (machine-register-width-check (решта rows)))
           (так
            (список
              (як-є machine-register-width-witness)
              (як-є (status fail))
              (список (як-є case) name)
              (список (як-є expected) expected)
              (список (як-є actual) actual)))))))))

(machine-register-width-check (machine-register-width-rows))
