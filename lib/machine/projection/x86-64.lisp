; #4347 — explicit projection from canonical machine effects to one target.
;
; Upstream effect identity is target-neutral. This file alone chooses physical
; registers and admitted target forms. Projection rejection is distinct from
; effect-construction rejection.

(визначити x86-project-machine-effect
  (функція (effect)
    (за-умовою
      ((machine-effect-bounded-u64-add-form? effect)
       (нехай
         ((left (перше (решта effect)))
          (right (перше (решта (решта effect)))))
         (список
           (список (як-є mov-r64-imm64) (як-є rax) left)
           (список (як-є mov-r64-imm64) (як-є rcx) right)
           (список (як-є add-r64-r64) (як-є rax) (як-є rcx))
           (список (як-є ret)))))
      ((machine-effect-bounded-u64-sub-form? effect)
       (нехай
         ((left (перше (решта effect)))
          (right (перше (решта (решта effect)))))
         (список
           (список (як-є mov-r64-imm64) (як-є rax) left)
           (список (як-є mov-r64-imm64) (як-є rcx) right)
           (список (як-є sub-r64-r64) (як-є rax) (як-є rcx))
           (список (як-є ret)))))
      ((machine-effect-bounded-u64-mul-form? effect)
       (нехай
         ((left (перше (решта effect)))
          (right (перше (решта (решта effect)))))
         (список
           (список (як-є mov-r64-imm64) (як-є rax) left)
           (список (як-є mov-r64-imm64) (як-є rcx) right)
           (список (як-є imul-r64-r64) (як-є rax) (як-є rcx))
           (список (як-є ret)))))
      ((атом? ()) (як-є x86-projection-rejected)))))

(визначити x86-encode-machine-effect
  (функція (effect)
    (нехай ((forms (x86-project-machine-effect effect)))
      (за-умовою
        ((атом? forms)
         (як-є x86-projection-rejected))
        ((атом? ())
         (x86-encode-admitted-program forms))))))
