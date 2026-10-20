; Каталог родини машинних інструкцій RDSEED.
; Описує тільки фізичні факти ISA, не семантичні закони СЕНС.
; Поля, мнемоніки й апаратні ознаки є незмінними даними.

(isa-catalogue/1
  (extension RDSEED)
  (source intel-sdm/intel-xed)
  (runtime-gate cpuid-rdseed)
  (coverage seed)
  (instructions
    (instruction RDSEED
      (class hardware-seed)
      (feature RDSEED)
      (privilege user))))
