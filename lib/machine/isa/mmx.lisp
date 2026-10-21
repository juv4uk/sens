; Каталог родини машинних команд MMX.
; Файл містить лише факти фізичного набору команд, не закони SENS.
; MMX зберігається для сумісності з архітектурою процесора i5-6400.
; Імена інструкцій та ключі записів — точні дані ISA, не виклики Lisp.

(isa-catalogue-1
  (extension MMX)
  (source intel-sdm/intel-xed)
  (coverage seed)
  (instructions
    (instruction EMMS
      (class mmx-state)
      (feature MMX)
      (privilege user)
      (forms
        (form emms
          (operands)
          (opcode-map 0F)
          (opcode 77))))
    (instruction MOVQ
      (class packed-move)
      (feature MMX)
      (privilege user))))
