; Каталог інструкції PCLMULQDQ для множення без перенесення.
; Це лише фізичні факти ISA, а не математичні закони СЕНС.
; Машинні мнемоніки й поля каталогу залишаються точними даними.

(isa-catalogue/1
  (extension PCLMULQDQ)
  (source intel-sdm/intel-xed)
  (runtime-gate cpuid-pclmulqdq)
  (coverage seed)
  (instructions
    (instruction PCLMULQDQ
      (class carry-less-multiply)
      (feature PCLMULQDQ)
      (privilege user))))
