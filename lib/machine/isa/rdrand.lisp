; Каталог апаратної інструкції випадкових чисел RDRAND.
; Описує лише фізичні факти ISA, не мовні закони СЕНС.
; Використання дозволяється лише за підтвердженою ознакою RDRAND у CPUID.
; Мнемоніки й структурні поля не перекладаються.

(isa-catalogue/1
  (extension RDRAND)
  (source intel-sdm/intel-xed)
  (runtime-gate cpuid-rdrand)
  (coverage seed)
  (instructions
    (instruction RDRAND
      (class hardware-random)
      (feature RDRAND)
      (privilege user)
      (forms
        (form rdrand-r16/r32/r64
          (opcode-map 0F)
          (opcode C7)
          (modrm-reg 6))))))
