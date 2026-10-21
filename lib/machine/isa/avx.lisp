; Каталог машинних команд AVX; жодних семантичних законів SENS.
; Виконання AVX дозволене лише після перевірки CPUID.OSXSAVE
; і стану регістрів, прочитаного через XGETBV.

(isa-catalogue-1
  (extension AVX)
  (requires SSE4.2)
  (source intel-sdm/intel-xed)
  (runtime-gate cpuid-avx+osxsave+xgetbv-xmm-ymm)
  (coverage seed)
  (instructions
    (instruction VADDPS
      (class packed-floating-point)
      (feature AVX)
      (privilege user)
      (forms
        (form vaddps-ymm-ymm-ymmm256
          (operands ymm ymm ymm/m256)
          (encoding VEX)
          (opcode-map 0F)
          (opcode 58)
          (modrm required))))
    (instruction VXORPS
      (class packed-logical)
      (feature AVX)
      (privilege user)
      (forms
        (form vxorps-ymm-ymm-ymmm256
          (operands ymm ymm ymm/m256)
          (encoding VEX)
          (opcode-map 0F)
          (opcode 57)
          (modrm required))))))
