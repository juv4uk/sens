; #176 — x86-64 instruction harvest witness (LEA, JMP rel32, Jcc rel32).
; Ukrainian projection only.

(load "lib/core.lisp")
(load "lib/machine/encoding/x86-64.lisp")
(load "lib/machine/admission/x86-64.lisp")

(визначити x86-instruction-witness-tests
  (як-є
    (((encode lea-basic)
      (x86-encode-lea-r64-mem-disp8 (як-є rax) (як-є rbx) 10)
      (72 141 67 10))
     ((encode jmp-rel32-pos)
      (x86-encode-jmp-rel32 200)
      (233 200 0 0 0))
     ((encode jz-rel32)
      (x86-encode-jz-rel32 1000)
      (15 132 232 3 0 0))
     ((admission lea-valid)
      (x86-admitted-instruction? (як-є (lea-r64-mem-disp8 rax rbx 10)))
      так)
     ((admission jmp-rel32-valid)
      (x86-admitted-instruction? (як-є (jmp-rel32 50000)))
      так)
     ((native imul-product)
      (викликати-допущену-машинну-програму
        (як-є
          ((mov-r64-imm64 rax 7)
           (mov-r64-imm64 rbx 6)
           (imul-r64-r64 rax rbx)
           (ret)))
        0)
      42)
     ((native idiv-quotient)
      (викликати-допущену-машинну-програму
        (як-є
          ((mov-r64-imm64 rax 100)
           (cqo)
           (mov-r64-imm64 rbx 7)
           (idiv-r64 rbx)
           (ret)))
        0)
      14)
     ((native sete-equal)
      (викликати-допущену-машинну-програму
        (як-є
          ((mov-r64-imm64 rax 10)
           (mov-r64-imm64 rbx 10)
           (cmp-r64-r64 rax rbx)
           (sete-r8 al)
           (movzx-r64-r8 rax al)
           (ret)))
        0)
      1)
     ((encode nop)
      (x86-encode-nop)
      (144))
     ((admission nop-valid)
      (x86-admitted-instruction? (як-є (nop)))
      так))))

(визначити x86-instruction-check-rows
  (функція (rows)
    (за-умовою
      ((атом? rows)
       (як-є (x86-64-instruction-set-witness (status pass))))
      (так
       (нехай ((row (перше rows))
              (name (перше row))
              (actual (друге row))
              (expected (третє row)))
         (за-умовою
           ((однакові? actual expected)
            (x86-instruction-check-rows (решта rows)))
           (так
            (список
              (як-є x86-64-instruction-set-witness)
              (як-є (status fail))
              (список (як-є case) name)
              (список (як-є actual) actual)
              (список (як-є expected) expected)))))))))

(визначити x86-64-instruction-set-witness
  (функція ()
    (x86-instruction-check-rows x86-instruction-witness-tests)))

(x86-64-instruction-set-witness)
