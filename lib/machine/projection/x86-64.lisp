; #4347 — explicit projection from canonical machine effects to one target.
;
; Upstream effect identity is target-neutral. This file alone chooses physical
; registers and admitted target forms. Projection rejection is distinct from
; effect-construction rejection.

(визначити x86-project-machine-effect
  (функція (ефект)
    (за-умовою
      ((машинний-ефект-форма-додавання-64? ефект)
       (нехай
         ((лівий (перше (решта ефект)))
          (правий (перше (решта (решта ефект)))))
         (список
           (список (як-є mov-r64-imm64) (як-є rax) лівий)
           (список (як-є mov-r64-imm64) (як-є rcx) правий)
           (список (як-є add-r64-r64) (як-є rax) (як-є rcx))
           (список (як-є ret)))))
      ((машинний-ефект-форма-віднімання-64? ефект)
       (нехай
         ((лівий (перше (решта ефект)))
          (правий (перше (решта (решта ефект)))))
         (список
           (список (як-є mov-r64-imm64) (як-є rax) лівий)
           (список (як-є mov-r64-imm64) (як-є rcx) правий)
           (список (як-є sub-r64-r64) (як-є rax) (як-є rcx))
           (список (як-є ret)))))
      ((машинний-ефект-форма-множення-64? ефект)
       (нехай
         ((лівий (перше (решта ефект)))
          (правий (перше (решта (решта ефект)))))
         (список
           (список (як-є mov-r64-imm64) (як-є rax) лівий)
           (список (як-є mov-r64-imm64) (як-є rcx) правий)
           (список (як-є imul-r64-r64) (як-є rax) (як-є rcx))
           (список (як-є ret)))))
      ((атом? ()) (як-є x86-projection-rejected)))))

(визначити x86-encode-machine-effect
  (функція (ефект)
    (нехай ((форми (x86-project-machine-effect ефект)))
      (за-умовою
        ((атом? форми)
         (як-є x86-projection-rejected))
        ((атом? ())
         (x86-encode-admitted-program форми))))))
