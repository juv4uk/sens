; #178 — Lisp-owned composition witness for current admitted register forms.
; Ukrainian projection only. Encoder/admission owns machine facts;
; atoms own typed composition only.

(load "lib/core.lisp")
(load "lib/machine/block.lisp")
(load "lib/machine/encoding/x86-64.lisp")
(load "lib/machine/operands/x86-64.lisp")
(load "lib/machine/admission/x86-64.lisp")
(load "lib/machine/atoms/x86-64.lisp")

(визначити machine-current-gpr-atom-rows
  (функція ()
    (список
      (список (як-є mov-r64-r64)
            (x86-mov-r64-r64 (як-є r8) (як-є r15))
            (як-є (mov-r64-r64 r8 r15)))
      (список (як-є test-r64-r64)
            (x86-test-r64-r64 (як-є rax) (як-є rcx))
            (як-є (test-r64-r64 rax rcx)))
      (список (як-є imul-r64-r64)
            (x86-imul-r64-r64 (як-є rax) (як-є rcx))
            (як-є (imul-r64-r64 rax rcx)))
      (список (як-є cqo) (x86-cqo) (як-є (cqo)))
      (список (як-є idiv-r64)
            (x86-idiv-r64 (як-є r10))
            (як-є (idiv-r64 r10)))
      (список (як-є setz-r8)
            (x86-setz-r8 (як-є r8b))
            (як-є (setz-r8 r8b)))
      (список (як-є movzx-r64-r8)
            (x86-movzx-r64-r8 (як-є rax) (як-є r8b))
            (як-є (movzx-r64-r8 rax r8b)))
      (список (як-є nop) (x86-nop) (як-є (nop)))
      (список (як-є reject-setcc-gpr64)
            (x86-setz-r8 (як-є rax))
            (як-є (rejected machine-operand gpr8 rax)))
      (список (як-є typed-rejection)
            (x86-imul-r64-r64 (як-є xmm0) (як-є rax))
            (як-є (rejected machine-operand gpr64 xmm0))))))

(визначити machine-current-gpr-check-rows
  (функція (rows)
    (за-умовою
      ((атом? rows) (як-є pass))
      (так
       (нехай ((row (перше rows))
              (name (перше row))
              (actual (друге row))
              (expected (третє row)))
         (за-умовою
           ((однакові? actual expected)
            (machine-current-gpr-check-rows (решта rows)))
           (так (список (як-є fail) name expected actual))))))))

(визначити machine-native
  (функція (forms)
    (викликати-допущену-машинну-програму forms 0)))

(визначити machine-current-gpr-native-rows
  (функція ()
    (список
      (список
        (як-є imul)
        (machine-native
          (список (x86-mov-r64-imm64 (як-є rax) 6)
                (x86-mov-r64-imm64 (як-є rcx) 7)
                (x86-imul-r64-r64 (як-є rax) (як-є rcx))
                (x86-ret)))
        42)
      (список
        (як-є idiv)
        (machine-native
          (список (x86-mov-r64-imm64 (як-є rax) 84)
                (x86-cqo)
                (x86-mov-r64-imm64 (як-є rcx) 2)
                (x86-idiv-r64 (як-є rcx))
                (x86-ret)))
        42)
      (список
        (як-є nop)
        (machine-native
          (список (x86-mov-r64-imm64 (як-є rax) 42)
                (x86-nop)
                (x86-ret)))
        42))))

(визначити machine-current-gpr-witness
  (функція ()
    (нехай ((form-state
            (machine-current-gpr-check-rows
              (machine-current-gpr-atom-rows))))
      (за-умовою
        ((тотожне? form-state (як-є pass))
         (нехай ((native-state
                 (machine-current-gpr-check-rows
                   (machine-current-gpr-native-rows))))
           (за-умовою
             ((тотожне? native-state (як-є pass))
              (як-є (machine-current-gpr-atoms-witness (status pass))))
             (так
              (список (як-є machine-current-gpr-atoms-witness)
                    (як-є (status fail))
                    (список (як-є native) native-state))))))
        (так
         (список (як-є machine-current-gpr-atoms-witness)
               (як-є (status fail))
               (список (як-є forms) form-state)))))))

(machine-current-gpr-witness)
