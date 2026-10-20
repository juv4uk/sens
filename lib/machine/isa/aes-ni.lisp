; Каталог апаратних інструкцій шифрування Intel AES-NI.
; Це лише фізичні властивості ISA, а не мовні закони СЕНС.
; Виконання допускається тільки за підтвердженою ознакою AES у CPUID.
; Назви команд і поля залишаються незмінними даними каталогу.

(isa-catalogue/1
  (extension AES-NI)
  (source intel-sdm/intel-xed)
  (runtime-gate cpuid-aes)
  (coverage seed)
  (instructions
    (instruction AESENC
      (class cryptographic-round)
      (feature AES-NI)
      (privilege user))
    (instruction AESDEC
      (class cryptographic-round)
      (feature AES-NI)
      (privilege user))
    (instruction AESKEYGENASSIST
      (class cryptographic-key-schedule)
      (feature AES-NI)
      (privilege user))))
