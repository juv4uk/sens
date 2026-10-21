; Каталог машинних команд F16C для перетворення чисел половинної точності.
; Збережено лише фізичні характеристики набору команд.

(isa-catalogue-1
  (extension F16C)
  (requires AVX)
  (source intel-sdm/intel-xed)
  (runtime-gate cpuid-f16c+avx-state)
  (coverage seed)
  (instructions
    (instruction VCVTPH2PS
      (class floating-convert)
      (feature F16C)
      (privilege user))
    (instruction VCVTPS2PH
      (class floating-convert)
      (feature F16C)
      (privilege user))))
