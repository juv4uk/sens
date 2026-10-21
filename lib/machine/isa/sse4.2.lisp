; Каталог родини інструкцій SSE4.2. Лише фізичні факти ISA.

(isa-catalogue-1
  (extension SSE4.2)
  (requires SSE4.1)
  (source intel-sdm/intel-xed)
  (coverage seed)
  (instructions
    (instruction PCMPISTRI
      (class packed-string-compare)
      (feature SSE4.2)
      (privilege user)
      (forms
        (form pcmpistri-xmm-xmmm128-imm8
          (operands xmm xmm/m128 imm8)
          (legacy-prefix 66)
          (opcode-map 0F3A)
          (opcode 63)
          (modrm required)
          (immediate-width 8))))
    (instruction CRC32
      (class checksum)
      (feature SSE4.2)
      (privilege user)
      (forms
        (form crc32-r32-rm32
          (operands r32 r/m32)
          (legacy-prefix F2)
          (opcode-map 0F38)
          (opcode F1)
          (modrm required))))

    (instruction POPCNT
      (class bit-manipulation)
      (feature SSE4.2)
      (privilege user)
      (mode64 valid)
      (forms
        (form popcnt-r64-r64
          (operands r64 r/m64)
          (legacy-prefix F3)
          (rex W)
          (opcode-map 0F)
          (opcode B8)
          (modrm required))))))
