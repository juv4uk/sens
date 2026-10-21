; Каталог родини машинних команд SSE2.
; Містить тільки факти фізичного набору команд, не семантику SENS.
; Поля та мнемоніки збережено як машинно-читані дані ISA.

(isa-catalogue-1
  (extension SSE2)
  (requires SSE)
  (source intel-sdm/intel-xed)
  (coverage seed)
  (instructions
    (instruction ADDSD
      (class scalar-floating-point)
      (feature SSE2)
      (privilege user)
      (forms
        (form addsd-xmm-xmmm64
          (operands xmm xmm/m64)
          (legacy-prefix F2)
          (opcode-map 0F)
          (opcode 58)
          (modrm required))))
    (instruction SUBSD
      (class scalar-floating-point)
      (feature SSE2)
      (privilege user)
      (forms
        (form subsd-xmm-xmmm64
          (operands xmm xmm/m64)
          (legacy-prefix F2)
          (opcode-map 0F)
          (opcode 5C)
          (modrm required))))
    (instruction MULSD
      (class scalar-floating-point)
      (feature SSE2)
      (privilege user)
      (forms
        (form mulsd-xmm-xmmm64
          (operands xmm xmm/m64)
          (legacy-prefix F2)
          (opcode-map 0F)
          (opcode 59)
          (modrm required))))
    (instruction DIVSD
      (class scalar-floating-point)
      (feature SSE2)
      (privilege user)
      (forms
        (form divsd-xmm-xmmm64
          (operands xmm xmm/m64)
          (legacy-prefix F2)
          (opcode-map 0F)
          (opcode 5E)
          (modrm required))))
    (instruction SQRTSD
      (class scalar-floating-point)
      (feature SSE2)
      (privilege user)
      (forms
        (form sqrtsd-xmm-xmmm64
          (operands xmm xmm/m64)
          (legacy-prefix F2)
          (opcode-map 0F)
          (opcode 51)
          (modrm required))))
    (instruction MAXSD
      (class scalar-floating-point)
      (feature SSE2)
      (privilege user)
      (forms
        (form maxsd-xmm-xmmm64
          (operands xmm xmm/m64)
          (legacy-prefix F2)
          (opcode-map 0F)
          (opcode 5F)
          (modrm required))))
    (instruction MINSD
      (class scalar-floating-point)
      (feature SSE2)
      (privilege user)
      (forms
        (form minsd-xmm-xmmm64
          (operands xmm xmm/m64)
          (legacy-prefix F2)
          (opcode-map 0F)
          (opcode 5D)
          (modrm required))))
    (instruction UCOMISD
      (class scalar-floating-point-compare)
      (feature SSE2)
      (privilege user)
      (flags ZF PF CF)
      (forms
        (form ucomisd-xmm-xmmm64
          (operands xmm xmm/m64)
          (legacy-prefix 66)
          (opcode-map 0F)
          (opcode 2E)
          (modrm required))))
    (instruction XORPD
      (class packed-floating-point-logic)
      (feature SSE2)
      (privilege user)
      (forms
        (form xorpd-xmm-xmmm128
          (operands xmm xmm/m128)
          (legacy-prefix 66)
          (opcode-map 0F)
          (opcode 57)
          (modrm required))))
    (instruction CVTSI2SD
      (class scalar-floating-point-conversion)
      (feature SSE2)
      (privilege user)
      (forms
        (form cvtsi2sd-xmm-r64
          (operands xmm r/m64)
          (legacy-prefix F2)
          (rex W)
          (opcode-map 0F)
          (opcode 2A)
          (modrm required))))
    (instruction CVTTSD2SI
      (class scalar-floating-point-conversion)
      (feature SSE2)
      (privilege user)
      (forms
        (form cvttsd2si-r64-xmm
          (operands r64 xmm/m64)
          (legacy-prefix F2)
          (rex W)
          (opcode-map 0F)
          (opcode 2C)
          (modrm required))))
    (instruction MOVQ
      (class data-movement-simd)
      (feature SSE2)
      (privilege user)
      (forms
        (form movq-xmm-r64
          (operands xmm r/m64)
          (legacy-prefix 66)
          (rex W)
          (opcode-map 0F)
          (opcode 6E)
          (modrm required))
        (form movq-r64-xmm
          (operands r/m64 xmm)
          (legacy-prefix 66)
          (rex W)
          (opcode-map 0F)
          (opcode 7E)
          (modrm required))))
    (instruction MOVSD
      (class scalar-floating-point-data-movement)
      (feature SSE2)
      (privilege user)
      (forms
        (form movsd-xmm-xmmm64
          (operands xmm xmm/m64)
          (legacy-prefix F2)
          (opcode-map 0F)
          (opcode 10)
          (modrm required))))
    (instruction PADDD
      (class packed-integer-arithmetic)
      (feature SSE2)
      (privilege user)
      (forms
        (form paddd-xmm-xmmm128
          (operands xmm xmm/m128)
          (legacy-prefix 66)
          (opcode-map 0F)
          (opcode FE)
          (modrm required))))))
