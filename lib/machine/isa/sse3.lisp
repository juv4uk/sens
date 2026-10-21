; Каталог машинних команд SSE3; лише факти фізичної архітектури.
; Назви команд та поля каталогу залишаються протокольними даними.

(isa-catalogue-1
  (extension SSE3)
  (requires SSE2)
  (source intel-sdm/intel-xed)
  (coverage seed)
  (instructions
    (instruction HADDPS
      (class horizontal-floating-point)
      (feature SSE3)
      (privilege user)
      (forms
        (form haddps-xmm-xmmm128
          (operands xmm xmm/m128)
          (legacy-prefix F2)
          (opcode-map 0F)
          (opcode 7C)
          (modrm required))))
    (instruction LDDQU
      (class unaligned-data-movement)
      (feature SSE3)
      (privilege user)
      (forms
        (form lddqu-xmm-m128
          (operands xmm m128)
          (legacy-prefix F2)
          (opcode-map 0F)
          (opcode F0)
          (modrm required))))))
