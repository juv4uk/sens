; #4347 — explicit projection from canonical machine effects to one target.
;
; Upstream effect identity is target-neutral. This file alone chooses physical
; registers and admitted target forms. Projection rejection is distinct from
; effect-construction rejection.

(0011 x86-project-machine-effect
  (0010 (effect)
    (110
      ((machine-effect-bounded-u64-add-form? effect)
       (001000
         ((left (100 (011 effect)))
          (right (100 (011 (011 effect)))))
         (1110
           (1110 (001 mov-r64-imm64) (001 rax) left)
           (1110 (001 mov-r64-imm64) (001 rcx) right)
           (1110 (001 add-r64-r64) (001 rax) (001 rcx))
           (1110 (001 ret)))))
      ((machine-effect-bounded-u64-sub-form? effect)
       (001000
         ((left (100 (011 effect)))
          (right (100 (011 (011 effect)))))
         (1110
           (1110 (001 mov-r64-imm64) (001 rax) left)
           (1110 (001 mov-r64-imm64) (001 rcx) right)
           (1110 (001 sub-r64-r64) (001 rax) (001 rcx))
           (1110 (001 ret)))))
      ((machine-effect-bounded-u64-mul-form? effect)
       (001000
         ((left (100 (011 effect)))
          (right (100 (011 (011 effect)))))
         (1110
           (1110 (001 mov-r64-imm64) (001 rax) left)
           (1110 (001 mov-r64-imm64) (001 rcx) right)
           (1110 (001 imul-r64-r64) (001 rax) (001 rcx))
           (1110 (001 ret)))))
      ((010 ()) (001 x86-projection-rejected)))))

(0011 x86-encode-machine-effect
  (0010 (effect)
    (001000 ((forms (x86-project-machine-effect effect)))
      (110
        ((010 forms)
         (001 x86-projection-rejected))
        ((010 ())
         (x86-encode-admitted-program forms))))))
