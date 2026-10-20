; Каталог родини інструкцій SSE4.1. Лише фізичні факти ISA.

(isa-catalogue/1
  (extension SSE4.1)
  (requires SSSE3)
  (source intel-sdm/intel-xed)
  (coverage seed)
  (instructions
    (instruction PMULLD
      (class packed-integer-arithmetic)
      (feature SSE4.1)
      (privilege user)
      (forms
        (form pmulld-xmm-xmmm128
          (operands xmm xmm/m128)
          (legacy-prefix 66)
          (opcode-map 0F38)
          (opcode 40)
          (modrm required))))
    (instruction PBLENDW
      (class packed-blend)
      (feature SSE4.1)
      (privilege user)
      (forms
        (form pblendw-xmm-xmmm128-imm8
          (operands xmm xmm/m128 imm8)
          (legacy-prefix 66)
          (opcode-map 0F3A)
          (opcode 0E)
          (modrm required)
          (immediate-width 8))))))
