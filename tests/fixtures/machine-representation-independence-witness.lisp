; #211 — representation-independence witness.
; Lisp's existing addition is the answer key. The machine layer realizes the
; same inputs twice: once through the canonical bounded lowerer (RCX scratch),
; once through an alternate admitted register choice (R8 scratch).
; Ukrainian projection only.

(load "lib/core.lisp")
(load "lib/machine/encoding/x86-64.lisp")
(load "lib/machine/admission/x86-64.lisp")
(load "lib/machine/lowering/semantic-x86-64.lisp")

(визначити еталон-машинного-подання (додати 2 3))

(визначити машинне-подання-основне
  (викликати-допущену-машинну-програму
    (x86-lower-add-u64-forms 2 3)
    0))

(визначити машинне-подання-альтернативне
  (викликати-допущену-машинну-програму
    (як-є
      ((mov-r64-imm64 rax 2)
       (mov-r64-imm64 r8 3)
       (add-r64-r64 rax r8)
       (ret)))
    0))

(визначити свідок-незалежності-машинного-подання
  (функція ()
    (за-умовою
      ((тотожне?
         машинне-подання-основне
         еталон-машинного-подання)
       (за-умовою
         ((тотожне?
            машинне-подання-альтернативне
            еталон-машинного-подання)
          (як-є (machine-representation-independence-witness (status pass))))
         (так
          (список
            (як-є machine-representation-independence-witness)
            (як-є (status fail))
            (список (як-є case) (як-є alternate-register))
            (список (як-є semantic) еталон-машинного-подання)
            (список (як-є actual) машинне-подання-альтернативне)))))
      (так
       (список
         (як-є machine-representation-independence-witness)
         (як-є (status fail))
         (список (як-є case) (як-є canonical-register))
         (список (як-є semantic) еталон-машинного-подання)
         (список (як-є actual) машинне-подання-основне))))))

(свідок-незалежності-машинного-подання)
