; Каталог розширення Intel 64 / x86-64 поверх базового набору x86.
; Тут описані лише фізичні форми команд. Назви інструкцій,
; поля каталогу та коди машинних операцій лишаються незмінними даними.

(isa-catalogue/1
  (extension X86-64)
  (requires X86-BASE)
  (source intel-sdm/intel-xed)
  (coverage proof-slice)
  (instructions
    (instruction MOVSXD
      (class data-movement)
      (privilege user)
      (mode64 valid)
      (forms
        (form movsxd-r64-rm32
          (operands r64 r/m32)
          (rex W)
          (opcode 63)
          (modrm required))))
    (instruction CDQE
      (class integer-conversion)
      (privilege user)
      (mode64 valid)
      (forms
        (form cdqe
          (operands)
          (bytes 48 98))))
    (instruction CQO
      (class integer-conversion)
      (privilege user)
      (mode64 valid)
      (forms
        (form cqo
          (operands)
          (bytes 48 99))))))
