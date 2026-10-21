; Каталог команд SSE. Тут зібрано тільки факти фізичного набору команд;
; англомовні мнемоніки — точні дані ISA, а не викличні імена SENS.

(isa-catalogue-1
  (extension SSE)
  (source intel-sdm/intel-xed)
  (coverage seed)
  (instructions
    (instruction ADDSS
      (class scalar-floating-point)
      (feature SSE)
      (privilege user)
      (forms
        (form addss-xmm-xmmm32
          (operands xmm xmm/m32)
          (legacy-prefix F3)
          (opcode-map 0F)
          (opcode 58)
          (modrm required))))
    (instruction MOVSS
      (class scalar-floating-point-data-movement)
      (feature SSE)
      (privilege user)
      (forms
        (form movss-xmm-xmmm32
          (operands xmm xmm/m32)
          (legacy-prefix F3)
          (opcode-map 0F)
          (opcode 10)
          (modrm required))))))
