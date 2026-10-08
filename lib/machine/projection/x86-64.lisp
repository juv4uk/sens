; #4347 — explicit projection from canonical machine effects to one target.
;
; Upstream effect identity is target-neutral. This file alone chooses physical
; registers and admitted target forms. Projection rejection is distinct from
; effect-construction rejection.

(00001001 x86-project-machine-effect
  (00001000 (effect)
    (00000111
      ((machine-effect-bounded-u64-add-form? effect)
       (10011100
         ((left (00000101 (00000110 effect)))
          (right (00000101 (00000110 (00000110 effect)))))
         (00100111
           (00100111 (00000001 mov-r64-imm64) (00000001 rax) left)
           (00100111 (00000001 mov-r64-imm64) (00000001 rcx) right)
           (00100111 (00000001 add-r64-r64) (00000001 rax) (00000001 rcx))
           (00100111 (00000001 ret)))))
      ((machine-effect-bounded-u64-sub-form? effect)
       (10011100
         ((left (00000101 (00000110 effect)))
          (right (00000101 (00000110 (00000110 effect)))))
         (00100111
           (00100111 (00000001 mov-r64-imm64) (00000001 rax) left)
           (00100111 (00000001 mov-r64-imm64) (00000001 rcx) right)
           (00100111 (00000001 sub-r64-r64) (00000001 rax) (00000001 rcx))
           (00100111 (00000001 ret)))))
      ((machine-effect-bounded-u64-mul-form? effect)
       (10011100
         ((left (00000101 (00000110 effect)))
          (right (00000101 (00000110 (00000110 effect)))))
         (00100111
           (00100111 (00000001 mov-r64-imm64) (00000001 rax) left)
           (00100111 (00000001 mov-r64-imm64) (00000001 rcx) right)
           (00100111 (00000001 imul-r64-r64) (00000001 rax) (00000001 rcx))
           (00100111 (00000001 ret)))))
      (t (00000001 x86-projection-rejected)))))

(00001001 x86-encode-machine-effect
  (00001000 (effect)
    (10011100 ((forms (x86-project-machine-effect effect)))
      (00000111
        ((00000010 forms)
         (00000001 x86-projection-rejected))
        (t
         (x86-encode-admitted-program forms))))))
