; Каталог машинних команд SSSE3; лише факти фізичної архітектури.
; Мнемоніки та поля залишаються точними даними ISA.

(isa-catalogue-1
  (extension SSSE3)
  (requires SSE3)
  (source intel-sdm/intel-xed)
  (coverage seed)
  (instructions
    (instruction PSHUFB
      (class packed-byte-shuffle)
      (feature SSSE3)
      (privilege user)
      (forms
        (form pshufb-xmm-xmmm128
          (operands xmm xmm/m128)
          (legacy-prefix 66)
          (opcode-map 0F38)
          (opcode 00)
          (modrm required))))
    (instruction PABSD
      (class packed-integer-absolute)
      (feature SSSE3)
      (privilege user)
      (forms
        (form pabsd-xmm-xmmm128
          (operands xmm xmm/m128)
          (legacy-prefix 66)
          (opcode-map 0F38)
          (opcode 1E)
          (modrm required))))))
