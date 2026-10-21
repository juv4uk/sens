; Каталог оптимізованої інструкції очищення рядка кешу CLFLUSHOPT.
; Містить лише фізичні факти ISA, не мовні закони СЕНС.
; Назви апаратних можливостей та полів залишаються незмінними.

(isa-catalogue-1
  (extension CLFLUSHOPT)
  (source intel-sdm/intel-xed)
  (runtime-gate cpuid-clflushopt)
  (coverage seed)
  (instructions
    (instruction CLFLUSHOPT
      (class cache-line-flush)
      (feature CLFLUSHOPT)
      (privilege user))))
