; ЗГЕНЕРОВАНО `sens scripts/generate-encoder-coverage.lisp` -- не редагувати вручну.
; Джерела: закріплений індекс допущених ICLASS #175 + структурована проєкція допуску Lisp.
; Кожна закріплена пара (extension, ICLASS) з'являється рівно раз. `partial` означає
; що принаймні одна структурована допущена форма виконувана; це не стверджує повного
; покриття кожної форми операнда/адресації XED. Жодного тихого третього статусу (#176/#604).

(x86-encoder-coverage-1
  (form-count 1176)
  (partial-count 122)
  (coverage
    (iclass "AAA")
    (extension X86-BASE)
    (status not-yet-implemented)
    (reason "Решта форм BASE очікує поетапної реалізації"))
  (coverage
    (iclass "AAD")
    (extension X86-BASE)
    (status not-yet-implemented)
    (reason "Решта форм BASE очікує поетапної реалізації"))
  (coverage
    (iclass "AAM")
    (extension X86-BASE)
    (status not-yet-implemented)
    (reason "Решта форм BASE очікує поетапної реалізації"))
  (coverage
    (iclass "AAS")
    (extension X86-BASE)
    (status not-yet-implemented)
    (reason "Решта форм BASE очікує поетапної реалізації"))
  (coverage
    (iclass "ADC")
    (extension X86-BASE)
    (status not-yet-implemented)
    (reason "Решта форм BASE очікує поетапної реалізації"))
  (coverage
    (iclass "ADC_LOCK")
    (extension X86-BASE)
    (status not-yet-implemented)
    (reason "Решта форм BASE очікує поетапної реалізації"))
  (coverage
    (iclass "ADD")
    (extension X86-BASE)
    (status partial)
    (reason "За структурованим допуском Lisp щонайменше одна форма відповідає закріпленому ICLASS; повне покриття операндів і способів адресації XED не підтверджене"))
  (coverage
    (iclass "ADDPD")
    (extension SSE2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "ADDPS")
    (extension SSE)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "ADDSD")
    (extension SSE2)
    (status partial)
    (reason "За структурованим допуском Lisp щонайменше одна форма відповідає закріпленому ICLASS; повне покриття операндів і способів адресації XED не підтверджене"))
  (coverage
    (iclass "ADDSS")
    (extension SSE)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "ADDSUBPD")
    (extension SSE3)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "ADDSUBPS")
    (extension SSE3)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "ADD_LOCK")
    (extension X86-BASE)
    (status not-yet-implemented)
    (reason "Решта форм BASE очікує поетапної реалізації"))
  (coverage
    (iclass "AESDEC")
    (extension AES-NI)
    (status partial)
    (reason "За структурованим допуском Lisp щонайменше одна форма відповідає закріпленому ICLASS; повне покриття операндів і способів адресації XED не підтверджене"))
  (coverage
    (iclass "AESDECLAST")
    (extension AES-NI)
    (status partial)
    (reason "За структурованим допуском Lisp щонайменше одна форма відповідає закріпленому ICLASS; повне покриття операндів і способів адресації XED не підтверджене"))
  (coverage
    (iclass "AESENC")
    (extension AES-NI)
    (status partial)
    (reason "За структурованим допуском Lisp щонайменше одна форма відповідає закріпленому ICLASS; повне покриття операндів і способів адресації XED не підтверджене"))
  (coverage
    (iclass "AESENCLAST")
    (extension AES-NI)
    (status partial)
    (reason "За структурованим допуском Lisp щонайменше одна форма відповідає закріпленому ICLASS; повне покриття операндів і способів адресації XED не підтверджене"))
  (coverage
    (iclass "AESIMC")
    (extension AES-NI)
    (status partial)
    (reason "За структурованим допуском Lisp щонайменше одна форма відповідає закріпленому ICLASS; повне покриття операндів і способів адресації XED не підтверджене"))
  (coverage
    (iclass "AESKEYGENASSIST")
    (extension AES-NI)
    (status partial)
    (reason "За структурованим допуском Lisp щонайменше одна форма відповідає закріпленому ICLASS; повне покриття операндів і способів адресації XED не підтверджене"))
  (coverage
    (iclass "AND")
    (extension X86-BASE)
    (status partial)
    (reason "За структурованим допуском Lisp щонайменше одна форма відповідає закріпленому ICLASS; повне покриття операндів і способів адресації XED не підтверджене"))
  (coverage
    (iclass "ANDN")
    (extension BMI1)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "ANDNPD")
    (extension SSE2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "ANDNPS")
    (extension SSE)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "ANDPD")
    (extension SSE2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "ANDPS")
    (extension SSE)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "AND_LOCK")
    (extension X86-BASE)
    (status not-yet-implemented)
    (reason "Решта форм BASE очікує поетапної реалізації"))
  (coverage
    (iclass "ARPL")
    (extension X86-BASE)
    (status not-yet-implemented)
    (reason "Решта форм BASE очікує поетапної реалізації"))
  (coverage
    (iclass "BEXTR")
    (extension BMI1)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "BLENDPD")
    (extension SSE4.1+SSE4.2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "BLENDPS")
    (extension SSE4.1+SSE4.2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "BLENDVPD")
    (extension SSE4.1+SSE4.2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "BLENDVPS")
    (extension SSE4.1+SSE4.2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "BLSI")
    (extension BMI1)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "BLSMSK")
    (extension BMI1)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "BLSR")
    (extension BMI1)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "BNDCL")
    (extension MPX)
    (status not-yet-implemented)
    (reason "Кодування регістрів BND ще не реалізовано"))
  (coverage
    (iclass "BNDCN")
    (extension MPX)
    (status not-yet-implemented)
    (reason "Кодування регістрів BND ще не реалізовано"))
  (coverage
    (iclass "BNDCU")
    (extension MPX)
    (status not-yet-implemented)
    (reason "Кодування регістрів BND ще не реалізовано"))
  (coverage
    (iclass "BNDLDX")
    (extension MPX)
    (status not-yet-implemented)
    (reason "Кодування регістрів BND ще не реалізовано"))
  (coverage
    (iclass "BNDMK")
    (extension MPX)
    (status not-yet-implemented)
    (reason "Кодування регістрів BND ще не реалізовано"))
  (coverage
    (iclass "BNDMOV")
    (extension MPX)
    (status not-yet-implemented)
    (reason "Кодування регістрів BND ще не реалізовано"))
  (coverage
    (iclass "BNDSTX")
    (extension MPX)
    (status not-yet-implemented)
    (reason "Кодування регістрів BND ще не реалізовано"))
  (coverage
    (iclass "BOUND")
    (extension X86-BASE)
    (status not-yet-implemented)
    (reason "Решта форм BASE очікує поетапної реалізації"))
  (coverage
    (iclass "BSF")
    (extension X86-BASE)
    (status partial)
    (reason "За структурованим допуском Lisp щонайменше одна форма відповідає закріпленому ICLASS; повне покриття операндів і способів адресації XED не підтверджене"))
  (coverage
    (iclass "BSR")
    (extension X86-BASE)
    (status partial)
    (reason "За структурованим допуском Lisp щонайменше одна форма відповідає закріпленому ICLASS; повне покриття операндів і способів адресації XED не підтверджене"))
  (coverage
    (iclass "BSWAP")
    (extension X86-BASE)
    (status partial)
    (reason "За структурованим допуском Lisp щонайменше одна форма відповідає закріпленому ICLASS; повне покриття операндів і способів адресації XED не підтверджене"))
  (coverage
    (iclass "BT")
    (extension X86-BASE)
    (status partial)
    (reason "За структурованим допуском Lisp щонайменше одна форма відповідає закріпленому ICLASS; повне покриття операндів і способів адресації XED не підтверджене"))
  (coverage
    (iclass "BTC")
    (extension X86-BASE)
    (status partial)
    (reason "За структурованим допуском Lisp щонайменше одна форма відповідає закріпленому ICLASS; повне покриття операндів і способів адресації XED не підтверджене"))
  (coverage
    (iclass "BTC_LOCK")
    (extension X86-BASE)
    (status not-yet-implemented)
    (reason "Решта форм BASE очікує поетапної реалізації"))
  (coverage
    (iclass "BTR")
    (extension X86-BASE)
    (status partial)
    (reason "За структурованим допуском Lisp щонайменше одна форма відповідає закріпленому ICLASS; повне покриття операндів і способів адресації XED не підтверджене"))
  (coverage
    (iclass "BTR_LOCK")
    (extension X86-BASE)
    (status not-yet-implemented)
    (reason "Решта форм BASE очікує поетапної реалізації"))
  (coverage
    (iclass "BTS")
    (extension X86-BASE)
    (status partial)
    (reason "За структурованим допуском Lisp щонайменше одна форма відповідає закріпленому ICLASS; повне покриття операндів і способів адресації XED не підтверджене"))
  (coverage
    (iclass "BTS_LOCK")
    (extension X86-BASE)
    (status not-yet-implemented)
    (reason "Решта форм BASE очікує поетапної реалізації"))
  (coverage
    (iclass "BZHI")
    (extension BMI2)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "CALL_FAR")
    (extension X86-BASE)
    (status not-yet-implemented)
    (reason "Решта форм BASE очікує поетапної реалізації"))
  (coverage
    (iclass "CALL_NEAR")
    (extension X86-BASE)
    (status partial)
    (reason "За структурованим допуском Lisp щонайменше одна форма відповідає закріпленому ICLASS; повне покриття операндів і способів адресації XED не підтверджене"))
  (coverage
    (iclass "CBW")
    (extension X86-BASE)
    (status not-yet-implemented)
    (reason "Решта форм BASE очікує поетапної реалізації"))
  (coverage
    (iclass "CDQ")
    (extension X86-BASE)
    (status not-yet-implemented)
    (reason "Решта форм BASE очікує поетапної реалізації"))
  (coverage
    (iclass "CDQE")
    (extension X86-64)
    (status not-yet-implemented)
    (reason "Форми BASE для 64-бітного режиму очікують поетапної реалізації"))
  (coverage
    (iclass "CLC")
    (extension X86-BASE)
    (status not-yet-implemented)
    (reason "Решта форм BASE очікує поетапної реалізації"))
  (coverage
    (iclass "CLD")
    (extension X86-BASE)
    (status partial)
    (reason "За структурованим допуском Lisp щонайменше одна форма відповідає закріпленому ICLASS; повне покриття операндів і способів адресації XED не підтверджене"))
  (coverage
    (iclass "CLFLUSHOPT")
    (extension CLFLUSHOPT)
    (status not-yet-implemented)
    (reason "Кодування команд керування кешем ще не реалізовано"))
  (coverage
    (iclass "CLI")
    (extension X86-BASE)
    (status not-yet-implemented)
    (reason "Решта форм BASE очікує поетапної реалізації"))
  (coverage
    (iclass "CLTS")
    (extension X86-BASE)
    (status not-yet-implemented)
    (reason "Решта форм BASE очікує поетапної реалізації"))
  (coverage
    (iclass "CMC")
    (extension X86-BASE)
    (status not-yet-implemented)
    (reason "Решта форм BASE очікує поетапної реалізації"))
  (coverage
    (iclass "CMOVB")
    (extension X86-BASE)
    (status partial)
    (reason "За структурованим допуском Lisp щонайменше одна форма відповідає закріпленому ICLASS; повне покриття операндів і способів адресації XED не підтверджене"))
  (coverage
    (iclass "CMOVBE")
    (extension X86-BASE)
    (status partial)
    (reason "За структурованим допуском Lisp щонайменше одна форма відповідає закріпленому ICLASS; повне покриття операндів і способів адресації XED не підтверджене"))
  (coverage
    (iclass "CMOVL")
    (extension X86-BASE)
    (status partial)
    (reason "За структурованим допуском Lisp щонайменше одна форма відповідає закріпленому ICLASS; повне покриття операндів і способів адресації XED не підтверджене"))
  (coverage
    (iclass "CMOVLE")
    (extension X86-BASE)
    (status partial)
    (reason "За структурованим допуском Lisp щонайменше одна форма відповідає закріпленому ICLASS; повне покриття операндів і способів адресації XED не підтверджене"))
  (coverage
    (iclass "CMOVNB")
    (extension X86-BASE)
    (status partial)
    (reason "За структурованим допуском Lisp щонайменше одна форма відповідає закріпленому ICLASS; повне покриття операндів і способів адресації XED не підтверджене"))
  (coverage
    (iclass "CMOVNBE")
    (extension X86-BASE)
    (status partial)
    (reason "За структурованим допуском Lisp щонайменше одна форма відповідає закріпленому ICLASS; повне покриття операндів і способів адресації XED не підтверджене"))
  (coverage
    (iclass "CMOVNL")
    (extension X86-BASE)
    (status partial)
    (reason "За структурованим допуском Lisp щонайменше одна форма відповідає закріпленому ICLASS; повне покриття операндів і способів адресації XED не підтверджене"))
  (coverage
    (iclass "CMOVNLE")
    (extension X86-BASE)
    (status partial)
    (reason "За структурованим допуском Lisp щонайменше одна форма відповідає закріпленому ICLASS; повне покриття операндів і способів адресації XED не підтверджене"))
  (coverage
    (iclass "CMOVNO")
    (extension X86-BASE)
    (status partial)
    (reason "За структурованим допуском Lisp щонайменше одна форма відповідає закріпленому ICLASS; повне покриття операндів і способів адресації XED не підтверджене"))
  (coverage
    (iclass "CMOVNP")
    (extension X86-BASE)
    (status partial)
    (reason "За структурованим допуском Lisp щонайменше одна форма відповідає закріпленому ICLASS; повне покриття операндів і способів адресації XED не підтверджене"))
  (coverage
    (iclass "CMOVNS")
    (extension X86-BASE)
    (status partial)
    (reason "За структурованим допуском Lisp щонайменше одна форма відповідає закріпленому ICLASS; повне покриття операндів і способів адресації XED не підтверджене"))
  (coverage
    (iclass "CMOVNZ")
    (extension X86-BASE)
    (status partial)
    (reason "За структурованим допуском Lisp щонайменше одна форма відповідає закріпленому ICLASS; повне покриття операндів і способів адресації XED не підтверджене"))
  (coverage
    (iclass "CMOVO")
    (extension X86-BASE)
    (status partial)
    (reason "За структурованим допуском Lisp щонайменше одна форма відповідає закріпленому ICLASS; повне покриття операндів і способів адресації XED не підтверджене"))
  (coverage
    (iclass "CMOVP")
    (extension X86-BASE)
    (status partial)
    (reason "За структурованим допуском Lisp щонайменше одна форма відповідає закріпленому ICLASS; повне покриття операндів і способів адресації XED не підтверджене"))
  (coverage
    (iclass "CMOVS")
    (extension X86-BASE)
    (status partial)
    (reason "За структурованим допуском Lisp щонайменше одна форма відповідає закріпленому ICLASS; повне покриття операндів і способів адресації XED не підтверджене"))
  (coverage
    (iclass "CMOVZ")
    (extension X86-BASE)
    (status partial)
    (reason "За структурованим допуском Lisp щонайменше одна форма відповідає закріпленому ICLASS; повне покриття операндів і способів адресації XED не підтверджене"))
  (coverage
    (iclass "CMP")
    (extension X86-BASE)
    (status partial)
    (reason "За структурованим допуском Lisp щонайменше одна форма відповідає закріпленому ICLASS; повне покриття операндів і способів адресації XED не підтверджене"))
  (coverage
    (iclass "CMPPD")
    (extension SSE2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "CMPPS")
    (extension SSE)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "CMPSB")
    (extension X86-BASE)
    (status not-yet-implemented)
    (reason "Решта форм BASE очікує поетапної реалізації"))
  (coverage
    (iclass "CMPSD")
    (extension X86-BASE)
    (status not-yet-implemented)
    (reason "Решта форм BASE очікує поетапної реалізації"))
  (coverage
    (iclass "CMPSD_XMM")
    (extension SSE2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "CMPSQ")
    (extension X86-64)
    (status not-yet-implemented)
    (reason "Форми BASE для 64-бітного режиму очікують поетапної реалізації"))
  (coverage
    (iclass "CMPSS")
    (extension SSE)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "CMPSW")
    (extension X86-BASE)
    (status not-yet-implemented)
    (reason "Решта форм BASE очікує поетапної реалізації"))
  (coverage
    (iclass "CMPXCHG")
    (extension X86-BASE)
    (status partial)
    (reason "За структурованим допуском Lisp щонайменше одна форма відповідає закріпленому ICLASS; повне покриття операндів і способів адресації XED не підтверджене"))
  (coverage
    (iclass "CMPXCHG16B")
    (extension X86-64)
    (status not-yet-implemented)
    (reason "Форми BASE для 64-бітного режиму очікують поетапної реалізації"))
  (coverage
    (iclass "CMPXCHG16B_LOCK")
    (extension X86-64)
    (status not-yet-implemented)
    (reason "Форми BASE для 64-бітного режиму очікують поетапної реалізації"))
  (coverage
    (iclass "CMPXCHG8B")
    (extension X86-BASE)
    (status not-yet-implemented)
    (reason "Решта форм BASE очікує поетапної реалізації"))
  (coverage
    (iclass "CMPXCHG8B_LOCK")
    (extension X86-BASE)
    (status not-yet-implemented)
    (reason "Решта форм BASE очікує поетапної реалізації"))
  (coverage
    (iclass "CMPXCHG_LOCK")
    (extension X86-BASE)
    (status not-yet-implemented)
    (reason "Решта форм BASE очікує поетапної реалізації"))
  (coverage
    (iclass "COMISD")
    (extension SSE2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "COMISS")
    (extension SSE)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "CPUID")
    (extension X86-BASE)
    (status not-yet-implemented)
    (reason "Решта форм BASE очікує поетапної реалізації"))
  (coverage
    (iclass "CQO")
    (extension X86-64)
    (status partial)
    (reason "За структурованим допуском Lisp щонайменше одна форма відповідає закріпленому ICLASS; повне покриття операндів і способів адресації XED не підтверджене"))
  (coverage
    (iclass "CRC32")
    (extension SSE4.1+SSE4.2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "CVTDQ2PD")
    (extension SSE2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "CVTDQ2PS")
    (extension SSE2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "CVTPD2DQ")
    (extension SSE2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "CVTPD2PI")
    (extension SSE2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "CVTPD2PS")
    (extension SSE2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "CVTPI2PD")
    (extension SSE2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "CVTPI2PS")
    (extension SSE)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "CVTPS2DQ")
    (extension SSE2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "CVTPS2PD")
    (extension SSE2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "CVTPS2PI")
    (extension SSE)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "CVTSD2SI")
    (extension SSE2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "CVTSD2SS")
    (extension SSE2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "CVTSI2SD")
    (extension SSE2)
    (status partial)
    (reason "За структурованим допуском Lisp щонайменше одна форма відповідає закріпленому ICLASS; повне покриття операндів і способів адресації XED не підтверджене"))
  (coverage
    (iclass "CVTSI2SS")
    (extension SSE)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "CVTSS2SD")
    (extension SSE2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "CVTSS2SI")
    (extension SSE)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "CVTTPD2DQ")
    (extension SSE2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "CVTTPD2PI")
    (extension SSE2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "CVTTPS2DQ")
    (extension SSE2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "CVTTPS2PI")
    (extension SSE)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "CVTTSD2SI")
    (extension SSE2)
    (status partial)
    (reason "За структурованим допуском Lisp щонайменше одна форма відповідає закріпленому ICLASS; повне покриття операндів і способів адресації XED не підтверджене"))
  (coverage
    (iclass "CVTTSS2SI")
    (extension SSE)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "CWD")
    (extension X86-BASE)
    (status not-yet-implemented)
    (reason "Решта форм BASE очікує поетапної реалізації"))
  (coverage
    (iclass "CWDE")
    (extension X86-BASE)
    (status not-yet-implemented)
    (reason "Решта форм BASE очікує поетапної реалізації"))
  (coverage
    (iclass "DAA")
    (extension X86-BASE)
    (status not-yet-implemented)
    (reason "Решта форм BASE очікує поетапної реалізації"))
  (coverage
    (iclass "DAS")
    (extension X86-BASE)
    (status not-yet-implemented)
    (reason "Решта форм BASE очікує поетапної реалізації"))
  (coverage
    (iclass "DEC")
    (extension X86-BASE)
    (status partial)
    (reason "За структурованим допуском Lisp щонайменше одна форма відповідає закріпленому ICLASS; повне покриття операндів і способів адресації XED не підтверджене"))
  (coverage
    (iclass "DEC_LOCK")
    (extension X86-BASE)
    (status not-yet-implemented)
    (reason "Решта форм BASE очікує поетапної реалізації"))
  (coverage
    (iclass "DIV")
    (extension X86-BASE)
    (status not-yet-implemented)
    (reason "Решта форм BASE очікує поетапної реалізації"))
  (coverage
    (iclass "DIVPD")
    (extension SSE2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "DIVPS")
    (extension SSE)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "DIVSD")
    (extension SSE2)
    (status partial)
    (reason "За структурованим допуском Lisp щонайменше одна форма відповідає закріпленому ICLASS; повне покриття операндів і способів адресації XED не підтверджене"))
  (coverage
    (iclass "DIVSS")
    (extension SSE)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "DPPD")
    (extension SSE4.1+SSE4.2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "DPPS")
    (extension SSE4.1+SSE4.2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "EMMS")
    (extension MMX)
    (status not-yet-implemented)
    (reason "Кодування таблиці кодів операцій MMX ще не реалізовано"))
  (coverage
    (iclass "ENCLS")
    (extension SGX)
    (status not-yet-implemented)
    (reason "Кодування підфункцій ENCLS/ENCLU ще не реалізовано"))
  (coverage
    (iclass "ENCLU")
    (extension SGX)
    (status not-yet-implemented)
    (reason "Кодування підфункцій ENCLS/ENCLU ще не реалізовано"))
  (coverage
    (iclass "ENTER")
    (extension X86-BASE)
    (status not-yet-implemented)
    (reason "Решта форм BASE очікує поетапної реалізації"))
  (coverage
    (iclass "EXTRACTPS")
    (extension SSE4.1+SSE4.2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "F2XM1")
    (extension X87)
    (status not-yet-implemented)
    (reason "Кодування стекових регістрів x87 ще не реалізовано"))
  (coverage
    (iclass "FABS")
    (extension X87)
    (status not-yet-implemented)
    (reason "Кодування стекових регістрів x87 ще не реалізовано"))
  (coverage
    (iclass "FADD")
    (extension X87)
    (status not-yet-implemented)
    (reason "Кодування стекових регістрів x87 ще не реалізовано"))
  (coverage
    (iclass "FADDP")
    (extension X87)
    (status not-yet-implemented)
    (reason "Кодування стекових регістрів x87 ще не реалізовано"))
  (coverage
    (iclass "FBLD")
    (extension X87)
    (status not-yet-implemented)
    (reason "Кодування стекових регістрів x87 ще не реалізовано"))
  (coverage
    (iclass "FBSTP")
    (extension X87)
    (status not-yet-implemented)
    (reason "Кодування стекових регістрів x87 ще не реалізовано"))
  (coverage
    (iclass "FCHS")
    (extension X87)
    (status not-yet-implemented)
    (reason "Кодування стекових регістрів x87 ще не реалізовано"))
  (coverage
    (iclass "FCMOVB")
    (extension X87)
    (status not-yet-implemented)
    (reason "Кодування стекових регістрів x87 ще не реалізовано"))
  (coverage
    (iclass "FCMOVBE")
    (extension X87)
    (status not-yet-implemented)
    (reason "Кодування стекових регістрів x87 ще не реалізовано"))
  (coverage
    (iclass "FCMOVE")
    (extension X87)
    (status not-yet-implemented)
    (reason "Кодування стекових регістрів x87 ще не реалізовано"))
  (coverage
    (iclass "FCMOVNB")
    (extension X87)
    (status not-yet-implemented)
    (reason "Кодування стекових регістрів x87 ще не реалізовано"))
  (coverage
    (iclass "FCMOVNBE")
    (extension X87)
    (status not-yet-implemented)
    (reason "Кодування стекових регістрів x87 ще не реалізовано"))
  (coverage
    (iclass "FCMOVNE")
    (extension X87)
    (status not-yet-implemented)
    (reason "Кодування стекових регістрів x87 ще не реалізовано"))
  (coverage
    (iclass "FCMOVNU")
    (extension X87)
    (status not-yet-implemented)
    (reason "Кодування стекових регістрів x87 ще не реалізовано"))
  (coverage
    (iclass "FCMOVU")
    (extension X87)
    (status not-yet-implemented)
    (reason "Кодування стекових регістрів x87 ще не реалізовано"))
  (coverage
    (iclass "FCOM")
    (extension X87)
    (status not-yet-implemented)
    (reason "Кодування стекових регістрів x87 ще не реалізовано"))
  (coverage
    (iclass "FCOMI")
    (extension X87)
    (status not-yet-implemented)
    (reason "Кодування стекових регістрів x87 ще не реалізовано"))
  (coverage
    (iclass "FCOMIP")
    (extension X87)
    (status not-yet-implemented)
    (reason "Кодування стекових регістрів x87 ще не реалізовано"))
  (coverage
    (iclass "FCOMP")
    (extension X87)
    (status not-yet-implemented)
    (reason "Кодування стекових регістрів x87 ще не реалізовано"))
  (coverage
    (iclass "FCOMPP")
    (extension X87)
    (status not-yet-implemented)
    (reason "Кодування стекових регістрів x87 ще не реалізовано"))
  (coverage
    (iclass "FCOS")
    (extension X87)
    (status not-yet-implemented)
    (reason "Кодування стекових регістрів x87 ще не реалізовано"))
  (coverage
    (iclass "FDECSTP")
    (extension X87)
    (status not-yet-implemented)
    (reason "Кодування стекових регістрів x87 ще не реалізовано"))
  (coverage
    (iclass "FDISI8087_NOP")
    (extension X87)
    (status not-yet-implemented)
    (reason "Кодування стекових регістрів x87 ще не реалізовано"))
  (coverage
    (iclass "FDIV")
    (extension X87)
    (status not-yet-implemented)
    (reason "Кодування стекових регістрів x87 ще не реалізовано"))
  (coverage
    (iclass "FDIVP")
    (extension X87)
    (status not-yet-implemented)
    (reason "Кодування стекових регістрів x87 ще не реалізовано"))
  (coverage
    (iclass "FDIVR")
    (extension X87)
    (status not-yet-implemented)
    (reason "Кодування стекових регістрів x87 ще не реалізовано"))
  (coverage
    (iclass "FDIVRP")
    (extension X87)
    (status not-yet-implemented)
    (reason "Кодування стекових регістрів x87 ще не реалізовано"))
  (coverage
    (iclass "FENI8087_NOP")
    (extension X87)
    (status not-yet-implemented)
    (reason "Кодування стекових регістрів x87 ще не реалізовано"))
  (coverage
    (iclass "FFREE")
    (extension X87)
    (status not-yet-implemented)
    (reason "Кодування стекових регістрів x87 ще не реалізовано"))
  (coverage
    (iclass "FFREEP")
    (extension X87)
    (status not-yet-implemented)
    (reason "Кодування стекових регістрів x87 ще не реалізовано"))
  (coverage
    (iclass "FIADD")
    (extension X87)
    (status not-yet-implemented)
    (reason "Кодування стекових регістрів x87 ще не реалізовано"))
  (coverage
    (iclass "FICOM")
    (extension X87)
    (status not-yet-implemented)
    (reason "Кодування стекових регістрів x87 ще не реалізовано"))
  (coverage
    (iclass "FICOMP")
    (extension X87)
    (status not-yet-implemented)
    (reason "Кодування стекових регістрів x87 ще не реалізовано"))
  (coverage
    (iclass "FIDIV")
    (extension X87)
    (status not-yet-implemented)
    (reason "Кодування стекових регістрів x87 ще не реалізовано"))
  (coverage
    (iclass "FIDIVR")
    (extension X87)
    (status not-yet-implemented)
    (reason "Кодування стекових регістрів x87 ще не реалізовано"))
  (coverage
    (iclass "FILD")
    (extension X87)
    (status not-yet-implemented)
    (reason "Кодування стекових регістрів x87 ще не реалізовано"))
  (coverage
    (iclass "FIMUL")
    (extension X87)
    (status not-yet-implemented)
    (reason "Кодування стекових регістрів x87 ще не реалізовано"))
  (coverage
    (iclass "FINCSTP")
    (extension X87)
    (status not-yet-implemented)
    (reason "Кодування стекових регістрів x87 ще не реалізовано"))
  (coverage
    (iclass "FIST")
    (extension X87)
    (status not-yet-implemented)
    (reason "Кодування стекових регістрів x87 ще не реалізовано"))
  (coverage
    (iclass "FISTP")
    (extension X87)
    (status not-yet-implemented)
    (reason "Кодування стекових регістрів x87 ще не реалізовано"))
  (coverage
    (iclass "FISTTP")
    (extension SSE3)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "FISUB")
    (extension X87)
    (status not-yet-implemented)
    (reason "Кодування стекових регістрів x87 ще не реалізовано"))
  (coverage
    (iclass "FISUBR")
    (extension X87)
    (status not-yet-implemented)
    (reason "Кодування стекових регістрів x87 ще не реалізовано"))
  (coverage
    (iclass "FLD")
    (extension X87)
    (status not-yet-implemented)
    (reason "Кодування стекових регістрів x87 ще не реалізовано"))
  (coverage
    (iclass "FLD1")
    (extension X87)
    (status not-yet-implemented)
    (reason "Кодування стекових регістрів x87 ще не реалізовано"))
  (coverage
    (iclass "FLDCW")
    (extension X87)
    (status not-yet-implemented)
    (reason "Кодування стекових регістрів x87 ще не реалізовано"))
  (coverage
    (iclass "FLDENV")
    (extension X87)
    (status not-yet-implemented)
    (reason "Кодування стекових регістрів x87 ще не реалізовано"))
  (coverage
    (iclass "FLDL2E")
    (extension X87)
    (status not-yet-implemented)
    (reason "Кодування стекових регістрів x87 ще не реалізовано"))
  (coverage
    (iclass "FLDL2T")
    (extension X87)
    (status not-yet-implemented)
    (reason "Кодування стекових регістрів x87 ще не реалізовано"))
  (coverage
    (iclass "FLDLG2")
    (extension X87)
    (status not-yet-implemented)
    (reason "Кодування стекових регістрів x87 ще не реалізовано"))
  (coverage
    (iclass "FLDLN2")
    (extension X87)
    (status not-yet-implemented)
    (reason "Кодування стекових регістрів x87 ще не реалізовано"))
  (coverage
    (iclass "FLDPI")
    (extension X87)
    (status not-yet-implemented)
    (reason "Кодування стекових регістрів x87 ще не реалізовано"))
  (coverage
    (iclass "FLDZ")
    (extension X87)
    (status not-yet-implemented)
    (reason "Кодування стекових регістрів x87 ще не реалізовано"))
  (coverage
    (iclass "FMUL")
    (extension X87)
    (status not-yet-implemented)
    (reason "Кодування стекових регістрів x87 ще не реалізовано"))
  (coverage
    (iclass "FMULP")
    (extension X87)
    (status not-yet-implemented)
    (reason "Кодування стекових регістрів x87 ще не реалізовано"))
  (coverage
    (iclass "FNCLEX")
    (extension X87)
    (status not-yet-implemented)
    (reason "Кодування стекових регістрів x87 ще не реалізовано"))
  (coverage
    (iclass "FNINIT")
    (extension X87)
    (status not-yet-implemented)
    (reason "Кодування стекових регістрів x87 ще не реалізовано"))
  (coverage
    (iclass "FNOP")
    (extension X87)
    (status not-yet-implemented)
    (reason "Кодування стекових регістрів x87 ще не реалізовано"))
  (coverage
    (iclass "FNSAVE")
    (extension X87)
    (status not-yet-implemented)
    (reason "Кодування стекових регістрів x87 ще не реалізовано"))
  (coverage
    (iclass "FNSTCW")
    (extension X87)
    (status not-yet-implemented)
    (reason "Кодування стекових регістрів x87 ще не реалізовано"))
  (coverage
    (iclass "FNSTENV")
    (extension X87)
    (status not-yet-implemented)
    (reason "Кодування стекових регістрів x87 ще не реалізовано"))
  (coverage
    (iclass "FNSTSW")
    (extension X87)
    (status not-yet-implemented)
    (reason "Кодування стекових регістрів x87 ще не реалізовано"))
  (coverage
    (iclass "FPATAN")
    (extension X87)
    (status not-yet-implemented)
    (reason "Кодування стекових регістрів x87 ще не реалізовано"))
  (coverage
    (iclass "FPREM")
    (extension X87)
    (status not-yet-implemented)
    (reason "Кодування стекових регістрів x87 ще не реалізовано"))
  (coverage
    (iclass "FPREM1")
    (extension X87)
    (status not-yet-implemented)
    (reason "Кодування стекових регістрів x87 ще не реалізовано"))
  (coverage
    (iclass "FPTAN")
    (extension X87)
    (status not-yet-implemented)
    (reason "Кодування стекових регістрів x87 ще не реалізовано"))
  (coverage
    (iclass "FRNDINT")
    (extension X87)
    (status not-yet-implemented)
    (reason "Кодування стекових регістрів x87 ще не реалізовано"))
  (coverage
    (iclass "FRSTOR")
    (extension X87)
    (status not-yet-implemented)
    (reason "Кодування стекових регістрів x87 ще не реалізовано"))
  (coverage
    (iclass "FSCALE")
    (extension X87)
    (status not-yet-implemented)
    (reason "Кодування стекових регістрів x87 ще не реалізовано"))
  (coverage
    (iclass "FSETPM287_NOP")
    (extension X87)
    (status not-yet-implemented)
    (reason "Кодування стекових регістрів x87 ще не реалізовано"))
  (coverage
    (iclass "FSIN")
    (extension X87)
    (status not-yet-implemented)
    (reason "Кодування стекових регістрів x87 ще не реалізовано"))
  (coverage
    (iclass "FSINCOS")
    (extension X87)
    (status not-yet-implemented)
    (reason "Кодування стекових регістрів x87 ще не реалізовано"))
  (coverage
    (iclass "FSQRT")
    (extension X87)
    (status not-yet-implemented)
    (reason "Кодування стекових регістрів x87 ще не реалізовано"))
  (coverage
    (iclass "FST")
    (extension X87)
    (status not-yet-implemented)
    (reason "Кодування стекових регістрів x87 ще не реалізовано"))
  (coverage
    (iclass "FSTP")
    (extension X87)
    (status not-yet-implemented)
    (reason "Кодування стекових регістрів x87 ще не реалізовано"))
  (coverage
    (iclass "FSTPNCE")
    (extension X87)
    (status not-yet-implemented)
    (reason "Кодування стекових регістрів x87 ще не реалізовано"))
  (coverage
    (iclass "FSUB")
    (extension X87)
    (status not-yet-implemented)
    (reason "Кодування стекових регістрів x87 ще не реалізовано"))
  (coverage
    (iclass "FSUBP")
    (extension X87)
    (status not-yet-implemented)
    (reason "Кодування стекових регістрів x87 ще не реалізовано"))
  (coverage
    (iclass "FSUBR")
    (extension X87)
    (status not-yet-implemented)
    (reason "Кодування стекових регістрів x87 ще не реалізовано"))
  (coverage
    (iclass "FSUBRP")
    (extension X87)
    (status not-yet-implemented)
    (reason "Кодування стекових регістрів x87 ще не реалізовано"))
  (coverage
    (iclass "FTST")
    (extension X87)
    (status not-yet-implemented)
    (reason "Кодування стекових регістрів x87 ще не реалізовано"))
  (coverage
    (iclass "FUCOM")
    (extension X87)
    (status not-yet-implemented)
    (reason "Кодування стекових регістрів x87 ще не реалізовано"))
  (coverage
    (iclass "FUCOMI")
    (extension X87)
    (status not-yet-implemented)
    (reason "Кодування стекових регістрів x87 ще не реалізовано"))
  (coverage
    (iclass "FUCOMIP")
    (extension X87)
    (status not-yet-implemented)
    (reason "Кодування стекових регістрів x87 ще не реалізовано"))
  (coverage
    (iclass "FUCOMP")
    (extension X87)
    (status not-yet-implemented)
    (reason "Кодування стекових регістрів x87 ще не реалізовано"))
  (coverage
    (iclass "FUCOMPP")
    (extension X87)
    (status not-yet-implemented)
    (reason "Кодування стекових регістрів x87 ще не реалізовано"))
  (coverage
    (iclass "FWAIT")
    (extension X87)
    (status not-yet-implemented)
    (reason "Кодування стекових регістрів x87 ще не реалізовано"))
  (coverage
    (iclass "FXAM")
    (extension X87)
    (status not-yet-implemented)
    (reason "Кодування стекових регістрів x87 ще не реалізовано"))
  (coverage
    (iclass "FXCH")
    (extension X87)
    (status not-yet-implemented)
    (reason "Кодування стекових регістрів x87 ще не реалізовано"))
  (coverage
    (iclass "FXRSTOR")
    (extension SSE)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "FXRSTOR64")
    (extension SSE)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "FXSAVE")
    (extension SSE)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "FXSAVE64")
    (extension SSE)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "FXTRACT")
    (extension X87)
    (status not-yet-implemented)
    (reason "Кодування стекових регістрів x87 ще не реалізовано"))
  (coverage
    (iclass "FYL2X")
    (extension X87)
    (status not-yet-implemented)
    (reason "Кодування стекових регістрів x87 ще не реалізовано"))
  (coverage
    (iclass "FYL2XP1")
    (extension X87)
    (status not-yet-implemented)
    (reason "Кодування стекових регістрів x87 ще не реалізовано"))
  (coverage
    (iclass "HADDPD")
    (extension SSE3)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "HADDPS")
    (extension SSE3)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "HLT")
    (extension X86-BASE)
    (status not-yet-implemented)
    (reason "Решта форм BASE очікує поетапної реалізації"))
  (coverage
    (iclass "HSUBPD")
    (extension SSE3)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "HSUBPS")
    (extension SSE3)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "IDIV")
    (extension X86-BASE)
    (status partial)
    (reason "За структурованим допуском Lisp щонайменше одна форма відповідає закріпленому ICLASS; повне покриття операндів і способів адресації XED не підтверджене"))
  (coverage
    (iclass "IMUL")
    (extension X86-BASE)
    (status partial)
    (reason "За структурованим допуском Lisp щонайменше одна форма відповідає закріпленому ICLASS; повне покриття операндів і способів адресації XED не підтверджене"))
  (coverage
    (iclass "IN")
    (extension X86-BASE)
    (status not-yet-implemented)
    (reason "Решта форм BASE очікує поетапної реалізації"))
  (coverage
    (iclass "INC")
    (extension X86-BASE)
    (status partial)
    (reason "За структурованим допуском Lisp щонайменше одна форма відповідає закріпленому ICLASS; повне покриття операндів і способів адресації XED не підтверджене"))
  (coverage
    (iclass "INC_LOCK")
    (extension X86-BASE)
    (status not-yet-implemented)
    (reason "Решта форм BASE очікує поетапної реалізації"))
  (coverage
    (iclass "INSB")
    (extension X86-BASE)
    (status not-yet-implemented)
    (reason "Решта форм BASE очікує поетапної реалізації"))
  (coverage
    (iclass "INSD")
    (extension X86-BASE)
    (status not-yet-implemented)
    (reason "Решта форм BASE очікує поетапної реалізації"))
  (coverage
    (iclass "INSERTPS")
    (extension SSE4.1+SSE4.2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "INSW")
    (extension X86-BASE)
    (status not-yet-implemented)
    (reason "Решта форм BASE очікує поетапної реалізації"))
  (coverage
    (iclass "INT")
    (extension X86-BASE)
    (status not-yet-implemented)
    (reason "Решта форм BASE очікує поетапної реалізації"))
  (coverage
    (iclass "INT1")
    (extension X86-BASE)
    (status not-yet-implemented)
    (reason "Решта форм BASE очікує поетапної реалізації"))
  (coverage
    (iclass "INT3")
    (extension X86-BASE)
    (status not-yet-implemented)
    (reason "Решта форм BASE очікує поетапної реалізації"))
  (coverage
    (iclass "INTO")
    (extension X86-BASE)
    (status not-yet-implemented)
    (reason "Решта форм BASE очікує поетапної реалізації"))
  (coverage
    (iclass "INVD")
    (extension X86-BASE)
    (status not-yet-implemented)
    (reason "Решта форм BASE очікує поетапної реалізації"))
  (coverage
    (iclass "INVLPG")
    (extension X86-BASE)
    (status not-yet-implemented)
    (reason "Решта форм BASE очікує поетапної реалізації"))
  (coverage
    (iclass "IRET")
    (extension X86-BASE)
    (status not-yet-implemented)
    (reason "Решта форм BASE очікує поетапної реалізації"))
  (coverage
    (iclass "IRETD")
    (extension X86-BASE)
    (status not-yet-implemented)
    (reason "Решта форм BASE очікує поетапної реалізації"))
  (coverage
    (iclass "IRETQ")
    (extension X86-64)
    (status not-yet-implemented)
    (reason "Форми BASE для 64-бітного режиму очікують поетапної реалізації"))
  (coverage
    (iclass "JB")
    (extension X86-BASE)
    (status partial)
    (reason "За структурованим допуском Lisp щонайменше одна форма відповідає закріпленому ICLASS; повне покриття операндів і способів адресації XED не підтверджене"))
  (coverage
    (iclass "JBE")
    (extension X86-BASE)
    (status partial)
    (reason "За структурованим допуском Lisp щонайменше одна форма відповідає закріпленому ICLASS; повне покриття операндів і способів адресації XED не підтверджене"))
  (coverage
    (iclass "JCXZ")
    (extension X86-BASE)
    (status not-yet-implemented)
    (reason "Решта форм BASE очікує поетапної реалізації"))
  (coverage
    (iclass "JECXZ")
    (extension X86-BASE)
    (status not-yet-implemented)
    (reason "Решта форм BASE очікує поетапної реалізації"))
  (coverage
    (iclass "JL")
    (extension X86-BASE)
    (status partial)
    (reason "За структурованим допуском Lisp щонайменше одна форма відповідає закріпленому ICLASS; повне покриття операндів і способів адресації XED не підтверджене"))
  (coverage
    (iclass "JLE")
    (extension X86-BASE)
    (status partial)
    (reason "За структурованим допуском Lisp щонайменше одна форма відповідає закріпленому ICLASS; повне покриття операндів і способів адресації XED не підтверджене"))
  (coverage
    (iclass "JMP")
    (extension X86-BASE)
    (status partial)
    (reason "За структурованим допуском Lisp щонайменше одна форма відповідає закріпленому ICLASS; повне покриття операндів і способів адресації XED не підтверджене"))
  (coverage
    (iclass "JMP_FAR")
    (extension X86-BASE)
    (status not-yet-implemented)
    (reason "Решта форм BASE очікує поетапної реалізації"))
  (coverage
    (iclass "JNB")
    (extension X86-BASE)
    (status partial)
    (reason "За структурованим допуском Lisp щонайменше одна форма відповідає закріпленому ICLASS; повне покриття операндів і способів адресації XED не підтверджене"))
  (coverage
    (iclass "JNBE")
    (extension X86-BASE)
    (status partial)
    (reason "За структурованим допуском Lisp щонайменше одна форма відповідає закріпленому ICLASS; повне покриття операндів і способів адресації XED не підтверджене"))
  (coverage
    (iclass "JNL")
    (extension X86-BASE)
    (status partial)
    (reason "За структурованим допуском Lisp щонайменше одна форма відповідає закріпленому ICLASS; повне покриття операндів і способів адресації XED не підтверджене"))
  (coverage
    (iclass "JNLE")
    (extension X86-BASE)
    (status partial)
    (reason "За структурованим допуском Lisp щонайменше одна форма відповідає закріпленому ICLASS; повне покриття операндів і способів адресації XED не підтверджене"))
  (coverage
    (iclass "JNO")
    (extension X86-BASE)
    (status partial)
    (reason "За структурованим допуском Lisp щонайменше одна форма відповідає закріпленому ICLASS; повне покриття операндів і способів адресації XED не підтверджене"))
  (coverage
    (iclass "JNP")
    (extension X86-BASE)
    (status partial)
    (reason "За структурованим допуском Lisp щонайменше одна форма відповідає закріпленому ICLASS; повне покриття операндів і способів адресації XED не підтверджене"))
  (coverage
    (iclass "JNS")
    (extension X86-BASE)
    (status partial)
    (reason "За структурованим допуском Lisp щонайменше одна форма відповідає закріпленому ICLASS; повне покриття операндів і способів адресації XED не підтверджене"))
  (coverage
    (iclass "JNZ")
    (extension X86-BASE)
    (status partial)
    (reason "За структурованим допуском Lisp щонайменше одна форма відповідає закріпленому ICLASS; повне покриття операндів і способів адресації XED не підтверджене"))
  (coverage
    (iclass "JO")
    (extension X86-BASE)
    (status partial)
    (reason "За структурованим допуском Lisp щонайменше одна форма відповідає закріпленому ICLASS; повне покриття операндів і способів адресації XED не підтверджене"))
  (coverage
    (iclass "JP")
    (extension X86-BASE)
    (status partial)
    (reason "За структурованим допуском Lisp щонайменше одна форма відповідає закріпленому ICLASS; повне покриття операндів і способів адресації XED не підтверджене"))
  (coverage
    (iclass "JRCXZ")
    (extension X86-BASE)
    (status not-yet-implemented)
    (reason "Решта форм BASE очікує поетапної реалізації"))
  (coverage
    (iclass "JS")
    (extension X86-BASE)
    (status partial)
    (reason "За структурованим допуском Lisp щонайменше одна форма відповідає закріпленому ICLASS; повне покриття операндів і способів адресації XED не підтверджене"))
  (coverage
    (iclass "JZ")
    (extension X86-BASE)
    (status partial)
    (reason "За структурованим допуском Lisp щонайменше одна форма відповідає закріпленому ICLASS; повне покриття операндів і способів адресації XED не підтверджене"))
  (coverage
    (iclass "LAHF")
    (extension X86-BASE)
    (status not-yet-implemented)
    (reason "Решта форм BASE очікує поетапної реалізації"))
  (coverage
    (iclass "LAR")
    (extension X86-BASE)
    (status not-yet-implemented)
    (reason "Решта форм BASE очікує поетапної реалізації"))
  (coverage
    (iclass "LDDQU")
    (extension SSE3)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "LDMXCSR")
    (extension SSE)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "LDS")
    (extension X86-BASE)
    (status not-yet-implemented)
    (reason "Решта форм BASE очікує поетапної реалізації"))
  (coverage
    (iclass "LEA")
    (extension X86-BASE)
    (status partial)
    (reason "За структурованим допуском Lisp щонайменше одна форма відповідає закріпленому ICLASS; повне покриття операндів і способів адресації XED не підтверджене"))
  (coverage
    (iclass "LEAVE")
    (extension X86-BASE)
    (status not-yet-implemented)
    (reason "Решта форм BASE очікує поетапної реалізації"))
  (coverage
    (iclass "LES")
    (extension X86-BASE)
    (status not-yet-implemented)
    (reason "Решта форм BASE очікує поетапної реалізації"))
  (coverage
    (iclass "LFENCE")
    (extension SSE2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "LFS")
    (extension X86-BASE)
    (status not-yet-implemented)
    (reason "Решта форм BASE очікує поетапної реалізації"))
  (coverage
    (iclass "LGDT")
    (extension X86-BASE)
    (status not-yet-implemented)
    (reason "Решта форм BASE очікує поетапної реалізації"))
  (coverage
    (iclass "LGS")
    (extension X86-BASE)
    (status not-yet-implemented)
    (reason "Решта форм BASE очікує поетапної реалізації"))
  (coverage
    (iclass "LIDT")
    (extension X86-BASE)
    (status not-yet-implemented)
    (reason "Решта форм BASE очікує поетапної реалізації"))
  (coverage
    (iclass "LLDT")
    (extension X86-BASE)
    (status not-yet-implemented)
    (reason "Решта форм BASE очікує поетапної реалізації"))
  (coverage
    (iclass "LMSW")
    (extension X86-BASE)
    (status not-yet-implemented)
    (reason "Решта форм BASE очікує поетапної реалізації"))
  (coverage
    (iclass "LODSB")
    (extension X86-BASE)
    (status not-yet-implemented)
    (reason "Решта форм BASE очікує поетапної реалізації"))
  (coverage
    (iclass "LODSD")
    (extension X86-BASE)
    (status not-yet-implemented)
    (reason "Решта форм BASE очікує поетапної реалізації"))
  (coverage
    (iclass "LODSQ")
    (extension X86-64)
    (status not-yet-implemented)
    (reason "Форми BASE для 64-бітного режиму очікують поетапної реалізації"))
  (coverage
    (iclass "LODSW")
    (extension X86-BASE)
    (status not-yet-implemented)
    (reason "Решта форм BASE очікує поетапної реалізації"))
  (coverage
    (iclass "LOOP")
    (extension X86-BASE)
    (status not-yet-implemented)
    (reason "Решта форм BASE очікує поетапної реалізації"))
  (coverage
    (iclass "LOOPE")
    (extension X86-BASE)
    (status not-yet-implemented)
    (reason "Решта форм BASE очікує поетапної реалізації"))
  (coverage
    (iclass "LOOPNE")
    (extension X86-BASE)
    (status not-yet-implemented)
    (reason "Решта форм BASE очікує поетапної реалізації"))
  (coverage
    (iclass "LSL")
    (extension X86-BASE)
    (status not-yet-implemented)
    (reason "Решта форм BASE очікує поетапної реалізації"))
  (coverage
    (iclass "LSS")
    (extension X86-BASE)
    (status not-yet-implemented)
    (reason "Решта форм BASE очікує поетапної реалізації"))
  (coverage
    (iclass "LTR")
    (extension X86-BASE)
    (status not-yet-implemented)
    (reason "Решта форм BASE очікує поетапної реалізації"))
  (coverage
    (iclass "MASKMOVDQU")
    (extension SSE2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "MASKMOVQ")
    (extension MMX)
    (status not-yet-implemented)
    (reason "Кодування таблиці кодів операцій MMX ще не реалізовано"))
  (coverage
    (iclass "MAXPD")
    (extension SSE2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "MAXPS")
    (extension SSE)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "MAXSD")
    (extension SSE2)
    (status partial)
    (reason "За структурованим допуском Lisp щонайменше одна форма відповідає закріпленому ICLASS; повне покриття операндів і способів адресації XED не підтверджене"))
  (coverage
    (iclass "MAXSS")
    (extension SSE)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "MFENCE")
    (extension SSE2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "MINPD")
    (extension SSE2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "MINPS")
    (extension SSE)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "MINSD")
    (extension SSE2)
    (status partial)
    (reason "За структурованим допуском Lisp щонайменше одна форма відповідає закріпленому ICLASS; повне покриття операндів і способів адресації XED не підтверджене"))
  (coverage
    (iclass "MINSS")
    (extension SSE)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "MOV")
    (extension X86-BASE)
    (status partial)
    (reason "За структурованим допуском Lisp щонайменше одна форма відповідає закріпленому ICLASS; повне покриття операндів і способів адресації XED не підтверджене"))
  (coverage
    (iclass "MOVAPD")
    (extension SSE2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "MOVAPS")
    (extension SSE)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "MOVD")
    (extension MMX)
    (status not-yet-implemented)
    (reason "Кодування таблиці кодів операцій MMX ще не реалізовано"))
  (coverage
    (iclass "MOVD")
    (extension SSE2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "MOVDDUP")
    (extension SSE3)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "MOVDQ2Q")
    (extension SSE2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "MOVDQA")
    (extension SSE2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "MOVDQU")
    (extension SSE2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "MOVHLPS")
    (extension SSE)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "MOVHPD")
    (extension SSE2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "MOVHPS")
    (extension SSE)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "MOVLHPS")
    (extension SSE)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "MOVLPD")
    (extension SSE2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "MOVLPS")
    (extension SSE)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "MOVMSKPD")
    (extension SSE2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "MOVMSKPS")
    (extension SSE)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "MOVNTDQ")
    (extension SSE2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "MOVNTDQA")
    (extension SSE4.1+SSE4.2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "MOVNTI")
    (extension SSE2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "MOVNTPD")
    (extension SSE2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "MOVNTPS")
    (extension SSE)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "MOVNTQ")
    (extension MMX)
    (status not-yet-implemented)
    (reason "Кодування таблиці кодів операцій MMX ще не реалізовано"))
  (coverage
    (iclass "MOVQ")
    (extension MMX)
    (status not-yet-implemented)
    (reason "Кодування таблиці кодів операцій MMX ще не реалізовано"))
  (coverage
    (iclass "MOVQ")
    (extension SSE2)
    (status partial)
    (reason "За структурованим допуском Lisp щонайменше одна форма відповідає закріпленому ICLASS; повне покриття операндів і способів адресації XED не підтверджене"))
  (coverage
    (iclass "MOVQ2DQ")
    (extension SSE2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "MOVSB")
    (extension X86-BASE)
    (status partial)
    (reason "За структурованим допуском Lisp щонайменше одна форма відповідає закріпленому ICLASS; повне покриття операндів і способів адресації XED не підтверджене"))
  (coverage
    (iclass "MOVSD")
    (extension X86-BASE)
    (status not-yet-implemented)
    (reason "Решта форм BASE очікує поетапної реалізації"))
  (coverage
    (iclass "MOVSD_XMM")
    (extension SSE2)
    (status partial)
    (reason "За структурованим допуском Lisp щонайменше одна форма відповідає закріпленому ICLASS; повне покриття операндів і способів адресації XED не підтверджене"))
  (coverage
    (iclass "MOVSHDUP")
    (extension SSE3)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "MOVSLDUP")
    (extension SSE3)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "MOVSQ")
    (extension X86-64)
    (status partial)
    (reason "За структурованим допуском Lisp щонайменше одна форма відповідає закріпленому ICLASS; повне покриття операндів і способів адресації XED не підтверджене"))
  (coverage
    (iclass "MOVSS")
    (extension SSE)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "MOVSW")
    (extension X86-BASE)
    (status not-yet-implemented)
    (reason "Решта форм BASE очікує поетапної реалізації"))
  (coverage
    (iclass "MOVSX")
    (extension X86-BASE)
    (status partial)
    (reason "За структурованим допуском Lisp щонайменше одна форма відповідає закріпленому ICLASS; повне покриття операндів і способів адресації XED не підтверджене"))
  (coverage
    (iclass "MOVSXD")
    (extension X86-64)
    (status partial)
    (reason "За структурованим допуском Lisp щонайменше одна форма відповідає закріпленому ICLASS; повне покриття операндів і способів адресації XED не підтверджене"))
  (coverage
    (iclass "MOVUPD")
    (extension SSE2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "MOVUPS")
    (extension SSE)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "MOVZX")
    (extension X86-BASE)
    (status partial)
    (reason "За структурованим допуском Lisp щонайменше одна форма відповідає закріпленому ICLASS; повне покриття операндів і способів адресації XED не підтверджене"))
  (coverage
    (iclass "MOV_CR")
    (extension X86-BASE)
    (status not-yet-implemented)
    (reason "Решта форм BASE очікує поетапної реалізації"))
  (coverage
    (iclass "MOV_DR")
    (extension X86-BASE)
    (status not-yet-implemented)
    (reason "Решта форм BASE очікує поетапної реалізації"))
  (coverage
    (iclass "MPSADBW")
    (extension SSE4.1+SSE4.2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "MUL")
    (extension X86-BASE)
    (status not-yet-implemented)
    (reason "Решта форм BASE очікує поетапної реалізації"))
  (coverage
    (iclass "MULPD")
    (extension SSE2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "MULPS")
    (extension SSE)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "MULSD")
    (extension SSE2)
    (status partial)
    (reason "За структурованим допуском Lisp щонайменше одна форма відповідає закріпленому ICLASS; повне покриття операндів і способів адресації XED не підтверджене"))
  (coverage
    (iclass "MULSS")
    (extension SSE)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "MULX")
    (extension BMI2)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "NEG")
    (extension X86-BASE)
    (status partial)
    (reason "За структурованим допуском Lisp щонайменше одна форма відповідає закріпленому ICLASS; повне покриття операндів і способів адресації XED не підтверджене"))
  (coverage
    (iclass "NEG_LOCK")
    (extension X86-BASE)
    (status not-yet-implemented)
    (reason "Решта форм BASE очікує поетапної реалізації"))
  (coverage
    (iclass "NOP")
    (extension X86-BASE)
    (status partial)
    (reason "За структурованим допуском Lisp щонайменше одна форма відповідає закріпленому ICLASS; повне покриття операндів і способів адресації XED не підтверджене"))
  (coverage
    (iclass "NOT")
    (extension X86-BASE)
    (status partial)
    (reason "За структурованим допуском Lisp щонайменше одна форма відповідає закріпленому ICLASS; повне покриття операндів і способів адресації XED не підтверджене"))
  (coverage
    (iclass "NOT_LOCK")
    (extension X86-BASE)
    (status not-yet-implemented)
    (reason "Решта форм BASE очікує поетапної реалізації"))
  (coverage
    (iclass "OR")
    (extension X86-BASE)
    (status partial)
    (reason "За структурованим допуском Lisp щонайменше одна форма відповідає закріпленому ICLASS; повне покриття операндів і способів адресації XED не підтверджене"))
  (coverage
    (iclass "ORPD")
    (extension SSE2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "ORPS")
    (extension SSE)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "OR_LOCK")
    (extension X86-BASE)
    (status not-yet-implemented)
    (reason "Решта форм BASE очікує поетапної реалізації"))
  (coverage
    (iclass "OUT")
    (extension X86-BASE)
    (status not-yet-implemented)
    (reason "Решта форм BASE очікує поетапної реалізації"))
  (coverage
    (iclass "OUTSB")
    (extension X86-BASE)
    (status not-yet-implemented)
    (reason "Решта форм BASE очікує поетапної реалізації"))
  (coverage
    (iclass "OUTSD")
    (extension X86-BASE)
    (status not-yet-implemented)
    (reason "Решта форм BASE очікує поетапної реалізації"))
  (coverage
    (iclass "OUTSW")
    (extension X86-BASE)
    (status not-yet-implemented)
    (reason "Решта форм BASE очікує поетапної реалізації"))
  (coverage
    (iclass "PABSB")
    (extension SSSE3)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "PABSD")
    (extension SSSE3)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "PABSW")
    (extension SSSE3)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "PACKSSDW")
    (extension MMX)
    (status not-yet-implemented)
    (reason "Кодування таблиці кодів операцій MMX ще не реалізовано"))
  (coverage
    (iclass "PACKSSDW")
    (extension SSE2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "PACKSSWB")
    (extension MMX)
    (status not-yet-implemented)
    (reason "Кодування таблиці кодів операцій MMX ще не реалізовано"))
  (coverage
    (iclass "PACKSSWB")
    (extension SSE2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "PACKUSDW")
    (extension SSE4.1+SSE4.2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "PACKUSWB")
    (extension MMX)
    (status not-yet-implemented)
    (reason "Кодування таблиці кодів операцій MMX ще не реалізовано"))
  (coverage
    (iclass "PACKUSWB")
    (extension SSE2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "PADDB")
    (extension MMX)
    (status not-yet-implemented)
    (reason "Кодування таблиці кодів операцій MMX ще не реалізовано"))
  (coverage
    (iclass "PADDB")
    (extension SSE2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "PADDD")
    (extension MMX)
    (status not-yet-implemented)
    (reason "Кодування таблиці кодів операцій MMX ще не реалізовано"))
  (coverage
    (iclass "PADDD")
    (extension SSE2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "PADDQ")
    (extension MMX)
    (status not-yet-implemented)
    (reason "Кодування таблиці кодів операцій MMX ще не реалізовано"))
  (coverage
    (iclass "PADDQ")
    (extension SSE2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "PADDSB")
    (extension MMX)
    (status not-yet-implemented)
    (reason "Кодування таблиці кодів операцій MMX ще не реалізовано"))
  (coverage
    (iclass "PADDSB")
    (extension SSE2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "PADDSW")
    (extension MMX)
    (status not-yet-implemented)
    (reason "Кодування таблиці кодів операцій MMX ще не реалізовано"))
  (coverage
    (iclass "PADDSW")
    (extension SSE2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "PADDUSB")
    (extension MMX)
    (status not-yet-implemented)
    (reason "Кодування таблиці кодів операцій MMX ще не реалізовано"))
  (coverage
    (iclass "PADDUSB")
    (extension SSE2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "PADDUSW")
    (extension MMX)
    (status not-yet-implemented)
    (reason "Кодування таблиці кодів операцій MMX ще не реалізовано"))
  (coverage
    (iclass "PADDUSW")
    (extension SSE2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "PADDW")
    (extension MMX)
    (status not-yet-implemented)
    (reason "Кодування таблиці кодів операцій MMX ще не реалізовано"))
  (coverage
    (iclass "PADDW")
    (extension SSE2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "PALIGNR")
    (extension SSSE3)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "PAND")
    (extension MMX)
    (status not-yet-implemented)
    (reason "Кодування таблиці кодів операцій MMX ще не реалізовано"))
  (coverage
    (iclass "PAND")
    (extension SSE2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "PANDN")
    (extension MMX)
    (status not-yet-implemented)
    (reason "Кодування таблиці кодів операцій MMX ще не реалізовано"))
  (coverage
    (iclass "PANDN")
    (extension SSE2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "PAVGB")
    (extension MMX)
    (status not-yet-implemented)
    (reason "Кодування таблиці кодів операцій MMX ще не реалізовано"))
  (coverage
    (iclass "PAVGB")
    (extension SSE2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "PAVGW")
    (extension MMX)
    (status not-yet-implemented)
    (reason "Кодування таблиці кодів операцій MMX ще не реалізовано"))
  (coverage
    (iclass "PAVGW")
    (extension SSE2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "PBLENDVB")
    (extension SSE4.1+SSE4.2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "PBLENDW")
    (extension SSE4.1+SSE4.2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "PCLMULQDQ")
    (extension PCLMULQDQ)
    (status partial)
    (reason "За структурованим допуском Lisp щонайменше одна форма відповідає закріпленому ICLASS; повне покриття операндів і способів адресації XED не підтверджене"))
  (coverage
    (iclass "PCMPEQB")
    (extension MMX)
    (status not-yet-implemented)
    (reason "Кодування таблиці кодів операцій MMX ще не реалізовано"))
  (coverage
    (iclass "PCMPEQB")
    (extension SSE2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "PCMPEQD")
    (extension MMX)
    (status not-yet-implemented)
    (reason "Кодування таблиці кодів операцій MMX ще не реалізовано"))
  (coverage
    (iclass "PCMPEQD")
    (extension SSE2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "PCMPEQQ")
    (extension SSE4.1+SSE4.2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "PCMPEQW")
    (extension MMX)
    (status not-yet-implemented)
    (reason "Кодування таблиці кодів операцій MMX ще не реалізовано"))
  (coverage
    (iclass "PCMPEQW")
    (extension SSE2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "PCMPESTRI")
    (extension SSE4.1+SSE4.2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "PCMPESTRI64")
    (extension SSE4.1+SSE4.2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "PCMPESTRM")
    (extension SSE4.1+SSE4.2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "PCMPESTRM64")
    (extension SSE4.1+SSE4.2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "PCMPGTB")
    (extension MMX)
    (status not-yet-implemented)
    (reason "Кодування таблиці кодів операцій MMX ще не реалізовано"))
  (coverage
    (iclass "PCMPGTB")
    (extension SSE2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "PCMPGTD")
    (extension MMX)
    (status not-yet-implemented)
    (reason "Кодування таблиці кодів операцій MMX ще не реалізовано"))
  (coverage
    (iclass "PCMPGTD")
    (extension SSE2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "PCMPGTQ")
    (extension SSE4.1+SSE4.2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "PCMPGTW")
    (extension MMX)
    (status not-yet-implemented)
    (reason "Кодування таблиці кодів операцій MMX ще не реалізовано"))
  (coverage
    (iclass "PCMPGTW")
    (extension SSE2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "PCMPISTRI")
    (extension SSE4.1+SSE4.2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "PCMPISTRI64")
    (extension SSE4.1+SSE4.2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "PCMPISTRM")
    (extension SSE4.1+SSE4.2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "PDEP")
    (extension BMI2)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "PEXT")
    (extension BMI2)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "PEXTRB")
    (extension SSE4.1+SSE4.2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "PEXTRD")
    (extension SSE4.1+SSE4.2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "PEXTRQ")
    (extension SSE4.1+SSE4.2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "PEXTRW")
    (extension MMX)
    (status not-yet-implemented)
    (reason "Кодування таблиці кодів операцій MMX ще не реалізовано"))
  (coverage
    (iclass "PEXTRW")
    (extension SSE2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "PEXTRW_SSE4")
    (extension SSE4.1+SSE4.2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "PHADDD")
    (extension SSSE3)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "PHADDSW")
    (extension SSSE3)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "PHADDW")
    (extension SSSE3)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "PHMINPOSUW")
    (extension SSE4.1+SSE4.2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "PHSUBD")
    (extension SSSE3)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "PHSUBSW")
    (extension SSSE3)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "PHSUBW")
    (extension SSSE3)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "PINSRB")
    (extension SSE4.1+SSE4.2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "PINSRD")
    (extension SSE4.1+SSE4.2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "PINSRQ")
    (extension SSE4.1+SSE4.2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "PINSRW")
    (extension MMX)
    (status not-yet-implemented)
    (reason "Кодування таблиці кодів операцій MMX ще не реалізовано"))
  (coverage
    (iclass "PINSRW")
    (extension SSE2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "PMADDUBSW")
    (extension SSSE3)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "PMADDWD")
    (extension MMX)
    (status not-yet-implemented)
    (reason "Кодування таблиці кодів операцій MMX ще не реалізовано"))
  (coverage
    (iclass "PMADDWD")
    (extension SSE2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "PMAXSB")
    (extension SSE4.1+SSE4.2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "PMAXSD")
    (extension SSE4.1+SSE4.2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "PMAXSW")
    (extension MMX)
    (status not-yet-implemented)
    (reason "Кодування таблиці кодів операцій MMX ще не реалізовано"))
  (coverage
    (iclass "PMAXSW")
    (extension SSE2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "PMAXUB")
    (extension MMX)
    (status not-yet-implemented)
    (reason "Кодування таблиці кодів операцій MMX ще не реалізовано"))
  (coverage
    (iclass "PMAXUB")
    (extension SSE2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "PMAXUD")
    (extension SSE4.1+SSE4.2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "PMAXUW")
    (extension SSE4.1+SSE4.2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "PMINSB")
    (extension SSE4.1+SSE4.2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "PMINSD")
    (extension SSE4.1+SSE4.2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "PMINSW")
    (extension MMX)
    (status not-yet-implemented)
    (reason "Кодування таблиці кодів операцій MMX ще не реалізовано"))
  (coverage
    (iclass "PMINSW")
    (extension SSE2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "PMINUB")
    (extension MMX)
    (status not-yet-implemented)
    (reason "Кодування таблиці кодів операцій MMX ще не реалізовано"))
  (coverage
    (iclass "PMINUB")
    (extension SSE2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "PMINUD")
    (extension SSE4.1+SSE4.2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "PMINUW")
    (extension SSE4.1+SSE4.2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "PMOVMSKB")
    (extension SSE)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "PMOVMSKB")
    (extension SSE2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "PMOVSXBD")
    (extension SSE4.1+SSE4.2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "PMOVSXBQ")
    (extension SSE4.1+SSE4.2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "PMOVSXBW")
    (extension SSE4.1+SSE4.2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "PMOVSXDQ")
    (extension SSE4.1+SSE4.2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "PMOVSXWD")
    (extension SSE4.1+SSE4.2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "PMOVSXWQ")
    (extension SSE4.1+SSE4.2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "PMOVZXBD")
    (extension SSE4.1+SSE4.2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "PMOVZXBQ")
    (extension SSE4.1+SSE4.2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "PMOVZXBW")
    (extension SSE4.1+SSE4.2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "PMOVZXDQ")
    (extension SSE4.1+SSE4.2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "PMOVZXWD")
    (extension SSE4.1+SSE4.2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "PMOVZXWQ")
    (extension SSE4.1+SSE4.2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "PMULDQ")
    (extension SSE4.1+SSE4.2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "PMULHRSW")
    (extension SSSE3)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "PMULHUW")
    (extension SSE)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "PMULHUW")
    (extension SSE2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "PMULHW")
    (extension MMX)
    (status not-yet-implemented)
    (reason "Кодування таблиці кодів операцій MMX ще не реалізовано"))
  (coverage
    (iclass "PMULHW")
    (extension SSE2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "PMULLD")
    (extension SSE4.1+SSE4.2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "PMULLW")
    (extension MMX)
    (status not-yet-implemented)
    (reason "Кодування таблиці кодів операцій MMX ще не реалізовано"))
  (coverage
    (iclass "PMULLW")
    (extension SSE2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "PMULUDQ")
    (extension SSE2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "POP")
    (extension X86-BASE)
    (status partial)
    (reason "За структурованим допуском Lisp щонайменше одна форма відповідає закріпленому ICLASS; повне покриття операндів і способів адресації XED не підтверджене"))
  (coverage
    (iclass "POPA")
    (extension X86-BASE)
    (status not-yet-implemented)
    (reason "Решта форм BASE очікує поетапної реалізації"))
  (coverage
    (iclass "POPAD")
    (extension X86-BASE)
    (status not-yet-implemented)
    (reason "Решта форм BASE очікує поетапної реалізації"))
  (coverage
    (iclass "POPCNT")
    (extension SSE4.1+SSE4.2)
    (status partial)
    (reason "За структурованим допуском Lisp щонайменше одна форма відповідає закріпленому ICLASS; повне покриття операндів і способів адресації XED не підтверджене"))
  (coverage
    (iclass "POPF")
    (extension X86-BASE)
    (status not-yet-implemented)
    (reason "Решта форм BASE очікує поетапної реалізації"))
  (coverage
    (iclass "POPFD")
    (extension X86-BASE)
    (status not-yet-implemented)
    (reason "Решта форм BASE очікує поетапної реалізації"))
  (coverage
    (iclass "POPFQ")
    (extension X86-64)
    (status not-yet-implemented)
    (reason "Форми BASE для 64-бітного режиму очікують поетапної реалізації"))
  (coverage
    (iclass "POR")
    (extension MMX)
    (status not-yet-implemented)
    (reason "Кодування таблиці кодів операцій MMX ще не реалізовано"))
  (coverage
    (iclass "POR")
    (extension SSE2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "PREFETCHNTA")
    (extension SSE)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "PREFETCHT0")
    (extension SSE)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "PREFETCHT1")
    (extension SSE)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "PREFETCHT2")
    (extension SSE)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "PSADBW")
    (extension MMX)
    (status not-yet-implemented)
    (reason "Кодування таблиці кодів операцій MMX ще не реалізовано"))
  (coverage
    (iclass "PSADBW")
    (extension SSE2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "PSHUFB")
    (extension SSSE3)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "PSHUFD")
    (extension SSE2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "PSHUFHW")
    (extension SSE2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "PSHUFLW")
    (extension SSE2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "PSHUFW")
    (extension MMX)
    (status not-yet-implemented)
    (reason "Кодування таблиці кодів операцій MMX ще не реалізовано"))
  (coverage
    (iclass "PSIGNB")
    (extension SSSE3)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "PSIGND")
    (extension SSSE3)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "PSIGNW")
    (extension SSSE3)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "PSLLD")
    (extension MMX)
    (status not-yet-implemented)
    (reason "Кодування таблиці кодів операцій MMX ще не реалізовано"))
  (coverage
    (iclass "PSLLD")
    (extension SSE2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "PSLLDQ")
    (extension SSE2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "PSLLQ")
    (extension MMX)
    (status not-yet-implemented)
    (reason "Кодування таблиці кодів операцій MMX ще не реалізовано"))
  (coverage
    (iclass "PSLLQ")
    (extension SSE2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "PSLLW")
    (extension MMX)
    (status not-yet-implemented)
    (reason "Кодування таблиці кодів операцій MMX ще не реалізовано"))
  (coverage
    (iclass "PSLLW")
    (extension SSE2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "PSRAD")
    (extension MMX)
    (status not-yet-implemented)
    (reason "Кодування таблиці кодів операцій MMX ще не реалізовано"))
  (coverage
    (iclass "PSRAD")
    (extension SSE2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "PSRAW")
    (extension MMX)
    (status not-yet-implemented)
    (reason "Кодування таблиці кодів операцій MMX ще не реалізовано"))
  (coverage
    (iclass "PSRAW")
    (extension SSE2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "PSRLD")
    (extension MMX)
    (status not-yet-implemented)
    (reason "Кодування таблиці кодів операцій MMX ще не реалізовано"))
  (coverage
    (iclass "PSRLD")
    (extension SSE2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "PSRLDQ")
    (extension SSE2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "PSRLQ")
    (extension MMX)
    (status not-yet-implemented)
    (reason "Кодування таблиці кодів операцій MMX ще не реалізовано"))
  (coverage
    (iclass "PSRLQ")
    (extension SSE2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "PSRLW")
    (extension MMX)
    (status not-yet-implemented)
    (reason "Кодування таблиці кодів операцій MMX ще не реалізовано"))
  (coverage
    (iclass "PSRLW")
    (extension SSE2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "PSUBB")
    (extension MMX)
    (status not-yet-implemented)
    (reason "Кодування таблиці кодів операцій MMX ще не реалізовано"))
  (coverage
    (iclass "PSUBB")
    (extension SSE2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "PSUBD")
    (extension MMX)
    (status not-yet-implemented)
    (reason "Кодування таблиці кодів операцій MMX ще не реалізовано"))
  (coverage
    (iclass "PSUBD")
    (extension SSE2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "PSUBQ")
    (extension SSE2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "PSUBSB")
    (extension MMX)
    (status not-yet-implemented)
    (reason "Кодування таблиці кодів операцій MMX ще не реалізовано"))
  (coverage
    (iclass "PSUBSB")
    (extension SSE2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "PSUBSW")
    (extension MMX)
    (status not-yet-implemented)
    (reason "Кодування таблиці кодів операцій MMX ще не реалізовано"))
  (coverage
    (iclass "PSUBSW")
    (extension SSE2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "PSUBUSB")
    (extension MMX)
    (status not-yet-implemented)
    (reason "Кодування таблиці кодів операцій MMX ще не реалізовано"))
  (coverage
    (iclass "PSUBUSB")
    (extension SSE2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "PSUBUSW")
    (extension MMX)
    (status not-yet-implemented)
    (reason "Кодування таблиці кодів операцій MMX ще не реалізовано"))
  (coverage
    (iclass "PSUBUSW")
    (extension SSE2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "PSUBW")
    (extension MMX)
    (status not-yet-implemented)
    (reason "Кодування таблиці кодів операцій MMX ще не реалізовано"))
  (coverage
    (iclass "PSUBW")
    (extension SSE2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "PTEST")
    (extension SSE4.1+SSE4.2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "PUNPCKHBW")
    (extension MMX)
    (status not-yet-implemented)
    (reason "Кодування таблиці кодів операцій MMX ще не реалізовано"))
  (coverage
    (iclass "PUNPCKHBW")
    (extension SSE2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "PUNPCKHDQ")
    (extension MMX)
    (status not-yet-implemented)
    (reason "Кодування таблиці кодів операцій MMX ще не реалізовано"))
  (coverage
    (iclass "PUNPCKHDQ")
    (extension SSE2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "PUNPCKHQDQ")
    (extension SSE2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "PUNPCKHWD")
    (extension MMX)
    (status not-yet-implemented)
    (reason "Кодування таблиці кодів операцій MMX ще не реалізовано"))
  (coverage
    (iclass "PUNPCKHWD")
    (extension SSE2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "PUNPCKLBW")
    (extension MMX)
    (status not-yet-implemented)
    (reason "Кодування таблиці кодів операцій MMX ще не реалізовано"))
  (coverage
    (iclass "PUNPCKLBW")
    (extension SSE2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "PUNPCKLDQ")
    (extension MMX)
    (status not-yet-implemented)
    (reason "Кодування таблиці кодів операцій MMX ще не реалізовано"))
  (coverage
    (iclass "PUNPCKLDQ")
    (extension SSE2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "PUNPCKLQDQ")
    (extension SSE2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "PUNPCKLWD")
    (extension MMX)
    (status not-yet-implemented)
    (reason "Кодування таблиці кодів операцій MMX ще не реалізовано"))
  (coverage
    (iclass "PUNPCKLWD")
    (extension SSE2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "PUSH")
    (extension X86-BASE)
    (status partial)
    (reason "За структурованим допуском Lisp щонайменше одна форма відповідає закріпленому ICLASS; повне покриття операндів і способів адресації XED не підтверджене"))
  (coverage
    (iclass "PUSHA")
    (extension X86-BASE)
    (status not-yet-implemented)
    (reason "Решта форм BASE очікує поетапної реалізації"))
  (coverage
    (iclass "PUSHAD")
    (extension X86-BASE)
    (status not-yet-implemented)
    (reason "Решта форм BASE очікує поетапної реалізації"))
  (coverage
    (iclass "PUSHF")
    (extension X86-BASE)
    (status not-yet-implemented)
    (reason "Решта форм BASE очікує поетапної реалізації"))
  (coverage
    (iclass "PUSHFD")
    (extension X86-BASE)
    (status not-yet-implemented)
    (reason "Решта форм BASE очікує поетапної реалізації"))
  (coverage
    (iclass "PUSHFQ")
    (extension X86-64)
    (status not-yet-implemented)
    (reason "Форми BASE для 64-бітного режиму очікують поетапної реалізації"))
  (coverage
    (iclass "PXOR")
    (extension MMX)
    (status not-yet-implemented)
    (reason "Кодування таблиці кодів операцій MMX ще не реалізовано"))
  (coverage
    (iclass "PXOR")
    (extension SSE2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "RCL")
    (extension X86-BASE)
    (status not-yet-implemented)
    (reason "Решта форм BASE очікує поетапної реалізації"))
  (coverage
    (iclass "RCPPS")
    (extension SSE)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "RCPSS")
    (extension SSE)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "RCR")
    (extension X86-BASE)
    (status not-yet-implemented)
    (reason "Решта форм BASE очікує поетапної реалізації"))
  (coverage
    (iclass "RDMSR")
    (extension X86-BASE)
    (status not-yet-implemented)
    (reason "Решта форм BASE очікує поетапної реалізації"))
  (coverage
    (iclass "RDPMC")
    (extension X86-BASE)
    (status not-yet-implemented)
    (reason "Решта форм BASE очікує поетапної реалізації"))
  (coverage
    (iclass "RDRAND")
    (extension RDRAND)
    (status partial)
    (reason "За структурованим допуском Lisp щонайменше одна форма відповідає закріпленому ICLASS; повне покриття операндів і способів адресації XED не підтверджене"))
  (coverage
    (iclass "RDSEED")
    (extension RDSEED)
    (status partial)
    (reason "За структурованим допуском Lisp щонайменше одна форма відповідає закріпленому ICLASS; повне покриття операндів і способів адресації XED не підтверджене"))
  (coverage
    (iclass "RDTSC")
    (extension X86-BASE)
    (status partial)
    (reason "За структурованим допуском Lisp щонайменше одна форма відповідає закріпленому ICLASS; повне покриття операндів і способів адресації XED не підтверджене"))
  (coverage
    (iclass "REPE_CMPSB")
    (extension X86-BASE)
    (status not-yet-implemented)
    (reason "Решта форм BASE очікує поетапної реалізації"))
  (coverage
    (iclass "REPE_CMPSD")
    (extension X86-BASE)
    (status not-yet-implemented)
    (reason "Решта форм BASE очікує поетапної реалізації"))
  (coverage
    (iclass "REPE_CMPSQ")
    (extension X86-64)
    (status not-yet-implemented)
    (reason "Форми BASE для 64-бітного режиму очікують поетапної реалізації"))
  (coverage
    (iclass "REPE_CMPSW")
    (extension X86-BASE)
    (status not-yet-implemented)
    (reason "Решта форм BASE очікує поетапної реалізації"))
  (coverage
    (iclass "REPE_SCASB")
    (extension X86-BASE)
    (status not-yet-implemented)
    (reason "Решта форм BASE очікує поетапної реалізації"))
  (coverage
    (iclass "REPE_SCASD")
    (extension X86-BASE)
    (status not-yet-implemented)
    (reason "Решта форм BASE очікує поетапної реалізації"))
  (coverage
    (iclass "REPE_SCASQ")
    (extension X86-64)
    (status not-yet-implemented)
    (reason "Форми BASE для 64-бітного режиму очікують поетапної реалізації"))
  (coverage
    (iclass "REPE_SCASW")
    (extension X86-BASE)
    (status not-yet-implemented)
    (reason "Решта форм BASE очікує поетапної реалізації"))
  (coverage
    (iclass "REPNE_CMPSB")
    (extension X86-BASE)
    (status not-yet-implemented)
    (reason "Решта форм BASE очікує поетапної реалізації"))
  (coverage
    (iclass "REPNE_CMPSD")
    (extension X86-BASE)
    (status not-yet-implemented)
    (reason "Решта форм BASE очікує поетапної реалізації"))
  (coverage
    (iclass "REPNE_CMPSQ")
    (extension X86-64)
    (status not-yet-implemented)
    (reason "Форми BASE для 64-бітного режиму очікують поетапної реалізації"))
  (coverage
    (iclass "REPNE_CMPSW")
    (extension X86-BASE)
    (status not-yet-implemented)
    (reason "Решта форм BASE очікує поетапної реалізації"))
  (coverage
    (iclass "REPNE_SCASB")
    (extension X86-BASE)
    (status not-yet-implemented)
    (reason "Решта форм BASE очікує поетапної реалізації"))
  (coverage
    (iclass "REPNE_SCASD")
    (extension X86-BASE)
    (status not-yet-implemented)
    (reason "Решта форм BASE очікує поетапної реалізації"))
  (coverage
    (iclass "REPNE_SCASQ")
    (extension X86-64)
    (status not-yet-implemented)
    (reason "Форми BASE для 64-бітного режиму очікують поетапної реалізації"))
  (coverage
    (iclass "REPNE_SCASW")
    (extension X86-BASE)
    (status not-yet-implemented)
    (reason "Решта форм BASE очікує поетапної реалізації"))
  (coverage
    (iclass "REP_INSB")
    (extension X86-BASE)
    (status not-yet-implemented)
    (reason "Решта форм BASE очікує поетапної реалізації"))
  (coverage
    (iclass "REP_INSD")
    (extension X86-BASE)
    (status not-yet-implemented)
    (reason "Решта форм BASE очікує поетапної реалізації"))
  (coverage
    (iclass "REP_INSW")
    (extension X86-BASE)
    (status not-yet-implemented)
    (reason "Решта форм BASE очікує поетапної реалізації"))
  (coverage
    (iclass "REP_LODSB")
    (extension X86-BASE)
    (status not-yet-implemented)
    (reason "Решта форм BASE очікує поетапної реалізації"))
  (coverage
    (iclass "REP_LODSD")
    (extension X86-BASE)
    (status not-yet-implemented)
    (reason "Решта форм BASE очікує поетапної реалізації"))
  (coverage
    (iclass "REP_LODSQ")
    (extension X86-64)
    (status not-yet-implemented)
    (reason "Форми BASE для 64-бітного режиму очікують поетапної реалізації"))
  (coverage
    (iclass "REP_LODSW")
    (extension X86-BASE)
    (status not-yet-implemented)
    (reason "Решта форм BASE очікує поетапної реалізації"))
  (coverage
    (iclass "REP_MOVSB")
    (extension X86-BASE)
    (status partial)
    (reason "За структурованим допуском Lisp щонайменше одна форма відповідає закріпленому ICLASS; повне покриття операндів і способів адресації XED не підтверджене"))
  (coverage
    (iclass "REP_MOVSD")
    (extension X86-BASE)
    (status not-yet-implemented)
    (reason "Решта форм BASE очікує поетапної реалізації"))
  (coverage
    (iclass "REP_MOVSQ")
    (extension X86-64)
    (status partial)
    (reason "За структурованим допуском Lisp щонайменше одна форма відповідає закріпленому ICLASS; повне покриття операндів і способів адресації XED не підтверджене"))
  (coverage
    (iclass "REP_MOVSW")
    (extension X86-BASE)
    (status not-yet-implemented)
    (reason "Решта форм BASE очікує поетапної реалізації"))
  (coverage
    (iclass "REP_OUTSB")
    (extension X86-BASE)
    (status not-yet-implemented)
    (reason "Решта форм BASE очікує поетапної реалізації"))
  (coverage
    (iclass "REP_OUTSD")
    (extension X86-BASE)
    (status not-yet-implemented)
    (reason "Решта форм BASE очікує поетапної реалізації"))
  (coverage
    (iclass "REP_OUTSW")
    (extension X86-BASE)
    (status not-yet-implemented)
    (reason "Решта форм BASE очікує поетапної реалізації"))
  (coverage
    (iclass "REP_STOSB")
    (extension X86-BASE)
    (status partial)
    (reason "За структурованим допуском Lisp щонайменше одна форма відповідає закріпленому ICLASS; повне покриття операндів і способів адресації XED не підтверджене"))
  (coverage
    (iclass "REP_STOSD")
    (extension X86-BASE)
    (status not-yet-implemented)
    (reason "Решта форм BASE очікує поетапної реалізації"))
  (coverage
    (iclass "REP_STOSQ")
    (extension X86-64)
    (status partial)
    (reason "За структурованим допуском Lisp щонайменше одна форма відповідає закріпленому ICLASS; повне покриття операндів і способів адресації XED не підтверджене"))
  (coverage
    (iclass "REP_STOSW")
    (extension X86-BASE)
    (status not-yet-implemented)
    (reason "Решта форм BASE очікує поетапної реалізації"))
  (coverage
    (iclass "RET_FAR")
    (extension X86-BASE)
    (status not-yet-implemented)
    (reason "Решта форм BASE очікує поетапної реалізації"))
  (coverage
    (iclass "RET_NEAR")
    (extension X86-BASE)
    (status partial)
    (reason "За структурованим допуском Lisp щонайменше одна форма відповідає закріпленому ICLASS; повне покриття операндів і способів адресації XED не підтверджене"))
  (coverage
    (iclass "ROL")
    (extension X86-BASE)
    (status partial)
    (reason "За структурованим допуском Lisp щонайменше одна форма відповідає закріпленому ICLASS; повне покриття операндів і способів адресації XED не підтверджене"))
  (coverage
    (iclass "ROR")
    (extension X86-BASE)
    (status partial)
    (reason "За структурованим допуском Lisp щонайменше одна форма відповідає закріпленому ICLASS; повне покриття операндів і способів адресації XED не підтверджене"))
  (coverage
    (iclass "RORX")
    (extension BMI2)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "ROUNDPD")
    (extension SSE4.1+SSE4.2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "ROUNDPS")
    (extension SSE4.1+SSE4.2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "ROUNDSD")
    (extension SSE4.1+SSE4.2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "ROUNDSS")
    (extension SSE4.1+SSE4.2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "RSM")
    (extension X86-BASE)
    (status not-yet-implemented)
    (reason "Решта форм BASE очікує поетапної реалізації"))
  (coverage
    (iclass "RSQRTPS")
    (extension SSE)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "RSQRTSS")
    (extension SSE)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "SAHF")
    (extension X86-BASE)
    (status not-yet-implemented)
    (reason "Решта форм BASE очікує поетапної реалізації"))
  (coverage
    (iclass "SALC")
    (extension X86-BASE)
    (status not-yet-implemented)
    (reason "Решта форм BASE очікує поетапної реалізації"))
  (coverage
    (iclass "SAR")
    (extension X86-BASE)
    (status partial)
    (reason "За структурованим допуском Lisp щонайменше одна форма відповідає закріпленому ICLASS; повне покриття операндів і способів адресації XED не підтверджене"))
  (coverage
    (iclass "SARX")
    (extension BMI2)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "SBB")
    (extension X86-BASE)
    (status not-yet-implemented)
    (reason "Решта форм BASE очікує поетапної реалізації"))
  (coverage
    (iclass "SBB_LOCK")
    (extension X86-BASE)
    (status not-yet-implemented)
    (reason "Решта форм BASE очікує поетапної реалізації"))
  (coverage
    (iclass "SCASB")
    (extension X86-BASE)
    (status not-yet-implemented)
    (reason "Решта форм BASE очікує поетапної реалізації"))
  (coverage
    (iclass "SCASD")
    (extension X86-BASE)
    (status not-yet-implemented)
    (reason "Решта форм BASE очікує поетапної реалізації"))
  (coverage
    (iclass "SCASQ")
    (extension X86-64)
    (status not-yet-implemented)
    (reason "Форми BASE для 64-бітного режиму очікують поетапної реалізації"))
  (coverage
    (iclass "SCASW")
    (extension X86-BASE)
    (status not-yet-implemented)
    (reason "Решта форм BASE очікує поетапної реалізації"))
  (coverage
    (iclass "SETB")
    (extension X86-BASE)
    (status partial)
    (reason "За структурованим допуском Lisp щонайменше одна форма відповідає закріпленому ICLASS; повне покриття операндів і способів адресації XED не підтверджене"))
  (coverage
    (iclass "SETBE")
    (extension X86-BASE)
    (status partial)
    (reason "За структурованим допуском Lisp щонайменше одна форма відповідає закріпленому ICLASS; повне покриття операндів і способів адресації XED не підтверджене"))
  (coverage
    (iclass "SETL")
    (extension X86-BASE)
    (status partial)
    (reason "За структурованим допуском Lisp щонайменше одна форма відповідає закріпленому ICLASS; повне покриття операндів і способів адресації XED не підтверджене"))
  (coverage
    (iclass "SETLE")
    (extension X86-BASE)
    (status partial)
    (reason "За структурованим допуском Lisp щонайменше одна форма відповідає закріпленому ICLASS; повне покриття операндів і способів адресації XED не підтверджене"))
  (coverage
    (iclass "SETNB")
    (extension X86-BASE)
    (status partial)
    (reason "За структурованим допуском Lisp щонайменше одна форма відповідає закріпленому ICLASS; повне покриття операндів і способів адресації XED не підтверджене"))
  (coverage
    (iclass "SETNBE")
    (extension X86-BASE)
    (status partial)
    (reason "За структурованим допуском Lisp щонайменше одна форма відповідає закріпленому ICLASS; повне покриття операндів і способів адресації XED не підтверджене"))
  (coverage
    (iclass "SETNL")
    (extension X86-BASE)
    (status partial)
    (reason "За структурованим допуском Lisp щонайменше одна форма відповідає закріпленому ICLASS; повне покриття операндів і способів адресації XED не підтверджене"))
  (coverage
    (iclass "SETNLE")
    (extension X86-BASE)
    (status partial)
    (reason "За структурованим допуском Lisp щонайменше одна форма відповідає закріпленому ICLASS; повне покриття операндів і способів адресації XED не підтверджене"))
  (coverage
    (iclass "SETNO")
    (extension X86-BASE)
    (status partial)
    (reason "За структурованим допуском Lisp щонайменше одна форма відповідає закріпленому ICLASS; повне покриття операндів і способів адресації XED не підтверджене"))
  (coverage
    (iclass "SETNP")
    (extension X86-BASE)
    (status partial)
    (reason "За структурованим допуском Lisp щонайменше одна форма відповідає закріпленому ICLASS; повне покриття операндів і способів адресації XED не підтверджене"))
  (coverage
    (iclass "SETNS")
    (extension X86-BASE)
    (status partial)
    (reason "За структурованим допуском Lisp щонайменше одна форма відповідає закріпленому ICLASS; повне покриття операндів і способів адресації XED не підтверджене"))
  (coverage
    (iclass "SETNZ")
    (extension X86-BASE)
    (status partial)
    (reason "За структурованим допуском Lisp щонайменше одна форма відповідає закріпленому ICLASS; повне покриття операндів і способів адресації XED не підтверджене"))
  (coverage
    (iclass "SETO")
    (extension X86-BASE)
    (status partial)
    (reason "За структурованим допуском Lisp щонайменше одна форма відповідає закріпленому ICLASS; повне покриття операндів і способів адресації XED не підтверджене"))
  (coverage
    (iclass "SETP")
    (extension X86-BASE)
    (status partial)
    (reason "За структурованим допуском Lisp щонайменше одна форма відповідає закріпленому ICLASS; повне покриття операндів і способів адресації XED не підтверджене"))
  (coverage
    (iclass "SETS")
    (extension X86-BASE)
    (status partial)
    (reason "За структурованим допуском Lisp щонайменше одна форма відповідає закріпленому ICLASS; повне покриття операндів і способів адресації XED не підтверджене"))
  (coverage
    (iclass "SETZ")
    (extension X86-BASE)
    (status partial)
    (reason "За структурованим допуском Lisp щонайменше одна форма відповідає закріпленому ICLASS; повне покриття операндів і способів адресації XED не підтверджене"))
  (coverage
    (iclass "SFENCE")
    (extension SSE)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "SGDT")
    (extension X86-BASE)
    (status not-yet-implemented)
    (reason "Решта форм BASE очікує поетапної реалізації"))
  (coverage
    (iclass "SHL")
    (extension X86-BASE)
    (status partial)
    (reason "За структурованим допуском Lisp щонайменше одна форма відповідає закріпленому ICLASS; повне покриття операндів і способів адресації XED не підтверджене"))
  (coverage
    (iclass "SHLD")
    (extension X86-BASE)
    (status not-yet-implemented)
    (reason "Решта форм BASE очікує поетапної реалізації"))
  (coverage
    (iclass "SHLX")
    (extension BMI2)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "SHR")
    (extension X86-BASE)
    (status partial)
    (reason "За структурованим допуском Lisp щонайменше одна форма відповідає закріпленому ICLASS; повне покриття операндів і способів адресації XED не підтверджене"))
  (coverage
    (iclass "SHRD")
    (extension X86-BASE)
    (status not-yet-implemented)
    (reason "Решта форм BASE очікує поетапної реалізації"))
  (coverage
    (iclass "SHRX")
    (extension BMI2)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "SHUFPD")
    (extension SSE2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "SHUFPS")
    (extension SSE)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "SIDT")
    (extension X86-BASE)
    (status not-yet-implemented)
    (reason "Решта форм BASE очікує поетапної реалізації"))
  (coverage
    (iclass "SLDT")
    (extension X86-BASE)
    (status not-yet-implemented)
    (reason "Решта форм BASE очікує поетапної реалізації"))
  (coverage
    (iclass "SMSW")
    (extension X86-BASE)
    (status not-yet-implemented)
    (reason "Решта форм BASE очікує поетапної реалізації"))
  (coverage
    (iclass "SQRTPD")
    (extension SSE2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "SQRTPS")
    (extension SSE)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "SQRTSD")
    (extension SSE2)
    (status partial)
    (reason "За структурованим допуском Lisp щонайменше одна форма відповідає закріпленому ICLASS; повне покриття операндів і способів адресації XED не підтверджене"))
  (coverage
    (iclass "SQRTSS")
    (extension SSE)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "STC")
    (extension X86-BASE)
    (status not-yet-implemented)
    (reason "Решта форм BASE очікує поетапної реалізації"))
  (coverage
    (iclass "STD")
    (extension X86-BASE)
    (status partial)
    (reason "За структурованим допуском Lisp щонайменше одна форма відповідає закріпленому ICLASS; повне покриття операндів і способів адресації XED не підтверджене"))
  (coverage
    (iclass "STI")
    (extension X86-BASE)
    (status not-yet-implemented)
    (reason "Решта форм BASE очікує поетапної реалізації"))
  (coverage
    (iclass "STMXCSR")
    (extension SSE)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "STOSB")
    (extension X86-BASE)
    (status partial)
    (reason "За структурованим допуском Lisp щонайменше одна форма відповідає закріпленому ICLASS; повне покриття операндів і способів адресації XED не підтверджене"))
  (coverage
    (iclass "STOSD")
    (extension X86-BASE)
    (status not-yet-implemented)
    (reason "Решта форм BASE очікує поетапної реалізації"))
  (coverage
    (iclass "STOSQ")
    (extension X86-64)
    (status partial)
    (reason "За структурованим допуском Lisp щонайменше одна форма відповідає закріпленому ICLASS; повне покриття операндів і способів адресації XED не підтверджене"))
  (coverage
    (iclass "STOSW")
    (extension X86-BASE)
    (status not-yet-implemented)
    (reason "Решта форм BASE очікує поетапної реалізації"))
  (coverage
    (iclass "STR")
    (extension X86-BASE)
    (status not-yet-implemented)
    (reason "Решта форм BASE очікує поетапної реалізації"))
  (coverage
    (iclass "SUB")
    (extension X86-BASE)
    (status partial)
    (reason "За структурованим допуском Lisp щонайменше одна форма відповідає закріпленому ICLASS; повне покриття операндів і способів адресації XED не підтверджене"))
  (coverage
    (iclass "SUBPD")
    (extension SSE2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "SUBPS")
    (extension SSE)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "SUBSD")
    (extension SSE2)
    (status partial)
    (reason "За структурованим допуском Lisp щонайменше одна форма відповідає закріпленому ICLASS; повне покриття операндів і способів адресації XED не підтверджене"))
  (coverage
    (iclass "SUBSS")
    (extension SSE)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "SUB_LOCK")
    (extension X86-BASE)
    (status not-yet-implemented)
    (reason "Решта форм BASE очікує поетапної реалізації"))
  (coverage
    (iclass "SWAPGS")
    (extension X86-64)
    (status not-yet-implemented)
    (reason "Форми BASE для 64-бітного режиму очікують поетапної реалізації"))
  (coverage
    (iclass "SYSCALL")
    (extension X86-64)
    (status not-yet-implemented)
    (reason "Форми BASE для 64-бітного режиму очікують поетапної реалізації"))
  (coverage
    (iclass "SYSENTER")
    (extension X86-BASE)
    (status not-yet-implemented)
    (reason "Решта форм BASE очікує поетапної реалізації"))
  (coverage
    (iclass "SYSEXIT")
    (extension X86-BASE)
    (status not-yet-implemented)
    (reason "Решта форм BASE очікує поетапної реалізації"))
  (coverage
    (iclass "SYSRET")
    (extension X86-64)
    (status not-yet-implemented)
    (reason "Форми BASE для 64-бітного режиму очікують поетапної реалізації"))
  (coverage
    (iclass "SYSRET64")
    (extension X86-64)
    (status not-yet-implemented)
    (reason "Форми BASE для 64-бітного режиму очікують поетапної реалізації"))
  (coverage
    (iclass "TEST")
    (extension X86-BASE)
    (status partial)
    (reason "За структурованим допуском Lisp щонайменше одна форма відповідає закріпленому ICLASS; повне покриття операндів і способів адресації XED не підтверджене"))
  (coverage
    (iclass "TZCNT")
    (extension BMI1)
    (status partial)
    (reason "За структурованим допуском Lisp щонайменше одна форма відповідає закріпленому ICLASS; повне покриття операндів і способів адресації XED не підтверджене"))
  (coverage
    (iclass "UCOMISD")
    (extension SSE2)
    (status partial)
    (reason "За структурованим допуском Lisp щонайменше одна форма відповідає закріпленому ICLASS; повне покриття операндів і способів адресації XED не підтверджене"))
  (coverage
    (iclass "UCOMISS")
    (extension SSE)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "UD0")
    (extension X86-BASE)
    (status not-yet-implemented)
    (reason "Решта форм BASE очікує поетапної реалізації"))
  (coverage
    (iclass "UD1")
    (extension X86-BASE)
    (status not-yet-implemented)
    (reason "Решта форм BASE очікує поетапної реалізації"))
  (coverage
    (iclass "UD2")
    (extension X86-BASE)
    (status not-yet-implemented)
    (reason "Решта форм BASE очікує поетапної реалізації"))
  (coverage
    (iclass "UDB")
    (extension X86-BASE)
    (status not-yet-implemented)
    (reason "Решта форм BASE очікує поетапної реалізації"))
  (coverage
    (iclass "UNPCKHPD")
    (extension SSE2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "UNPCKHPS")
    (extension SSE)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "UNPCKLPD")
    (extension SSE2)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "UNPCKLPS")
    (extension SSE)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "VADDPD")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VADDPS")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VADDSD")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VADDSS")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VADDSUBPD")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VADDSUBPS")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VANDNPD")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VANDNPS")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VANDPD")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VANDPS")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VBLENDPD")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VBLENDPS")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VBLENDVPD")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VBLENDVPS")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VBROADCASTF128")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VBROADCASTI128")
    (extension AVX2)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VBROADCASTSD")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VBROADCASTSD")
    (extension AVX2)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VBROADCASTSS")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VBROADCASTSS")
    (extension AVX2)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VCMPPD")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VCMPPS")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VCMPSD")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VCMPSS")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VCOMISD")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VCOMISS")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VCVTDQ2PD")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VCVTDQ2PS")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VCVTPD2DQ")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VCVTPD2PS")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VCVTPH2PS")
    (extension F16C)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VCVTPS2DQ")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VCVTPS2PD")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VCVTPS2PH")
    (extension F16C)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VCVTSD2SI")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VCVTSD2SS")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VCVTSI2SD")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VCVTSI2SS")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VCVTSS2SD")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VCVTSS2SI")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VCVTTPD2DQ")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VCVTTPS2DQ")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VCVTTSD2SI")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VCVTTSS2SI")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VDIVPD")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VDIVPS")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VDIVSD")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VDIVSS")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VDPPD")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VDPPS")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VERR")
    (extension X86-BASE)
    (status not-yet-implemented)
    (reason "Решта форм BASE очікує поетапної реалізації"))
  (coverage
    (iclass "VERW")
    (extension X86-BASE)
    (status not-yet-implemented)
    (reason "Решта форм BASE очікує поетапної реалізації"))
  (coverage
    (iclass "VEXTRACTF128")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VEXTRACTI128")
    (extension AVX2)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VEXTRACTPS")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VFMADD132PD")
    (extension FMA3)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VFMADD132PS")
    (extension FMA3)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VFMADD132SD")
    (extension FMA3)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VFMADD132SS")
    (extension FMA3)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VFMADD213PD")
    (extension FMA3)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VFMADD213PS")
    (extension FMA3)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VFMADD213SD")
    (extension FMA3)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VFMADD213SS")
    (extension FMA3)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VFMADD231PD")
    (extension FMA3)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VFMADD231PS")
    (extension FMA3)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VFMADD231SD")
    (extension FMA3)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VFMADD231SS")
    (extension FMA3)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VFMADDSUB132PD")
    (extension FMA3)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VFMADDSUB132PS")
    (extension FMA3)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VFMADDSUB213PD")
    (extension FMA3)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VFMADDSUB213PS")
    (extension FMA3)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VFMADDSUB231PD")
    (extension FMA3)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VFMADDSUB231PS")
    (extension FMA3)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VFMSUB132PD")
    (extension FMA3)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VFMSUB132PS")
    (extension FMA3)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VFMSUB132SD")
    (extension FMA3)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VFMSUB132SS")
    (extension FMA3)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VFMSUB213PD")
    (extension FMA3)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VFMSUB213PS")
    (extension FMA3)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VFMSUB213SD")
    (extension FMA3)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VFMSUB213SS")
    (extension FMA3)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VFMSUB231PD")
    (extension FMA3)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VFMSUB231PS")
    (extension FMA3)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VFMSUB231SD")
    (extension FMA3)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VFMSUB231SS")
    (extension FMA3)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VFMSUBADD132PD")
    (extension FMA3)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VFMSUBADD132PS")
    (extension FMA3)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VFMSUBADD213PD")
    (extension FMA3)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VFMSUBADD213PS")
    (extension FMA3)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VFMSUBADD231PD")
    (extension FMA3)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VFMSUBADD231PS")
    (extension FMA3)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VFNMADD132PD")
    (extension FMA3)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VFNMADD132PS")
    (extension FMA3)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VFNMADD132SD")
    (extension FMA3)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VFNMADD132SS")
    (extension FMA3)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VFNMADD213PD")
    (extension FMA3)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VFNMADD213PS")
    (extension FMA3)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VFNMADD213SD")
    (extension FMA3)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VFNMADD213SS")
    (extension FMA3)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VFNMADD231PD")
    (extension FMA3)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VFNMADD231PS")
    (extension FMA3)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VFNMADD231SD")
    (extension FMA3)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VFNMADD231SS")
    (extension FMA3)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VFNMSUB132PD")
    (extension FMA3)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VFNMSUB132PS")
    (extension FMA3)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VFNMSUB132SD")
    (extension FMA3)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VFNMSUB132SS")
    (extension FMA3)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VFNMSUB213PD")
    (extension FMA3)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VFNMSUB213PS")
    (extension FMA3)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VFNMSUB213SD")
    (extension FMA3)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VFNMSUB213SS")
    (extension FMA3)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VFNMSUB231PD")
    (extension FMA3)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VFNMSUB231PS")
    (extension FMA3)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VFNMSUB231SD")
    (extension FMA3)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VFNMSUB231SS")
    (extension FMA3)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VHADDPD")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VHADDPS")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VHSUBPD")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VHSUBPS")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VINSERTF128")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VINSERTI128")
    (extension AVX2)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VINSERTPS")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VLDDQU")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VLDMXCSR")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VMASKMOVDQU")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VMASKMOVPD")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VMASKMOVPS")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VMAXPD")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VMAXPS")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VMAXSD")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VMAXSS")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VMINPD")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VMINPS")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VMINSD")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VMINSS")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VMOVAPD")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VMOVAPS")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VMOVD")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VMOVDDUP")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VMOVDQA")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VMOVDQU")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VMOVHLPS")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VMOVHPD")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VMOVHPS")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VMOVLHPS")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VMOVLPD")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VMOVLPS")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VMOVMSKPD")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VMOVMSKPS")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VMOVNTDQ")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VMOVNTDQA")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VMOVNTDQA")
    (extension AVX2)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VMOVNTPD")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VMOVNTPS")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VMOVQ")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VMOVSD")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VMOVSHDUP")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VMOVSLDUP")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VMOVSS")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VMOVUPD")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VMOVUPS")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VMPSADBW")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VMPSADBW")
    (extension AVX2)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VMULPD")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VMULPS")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VMULSD")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VMULSS")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VORPD")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VORPS")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPABSB")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPABSB")
    (extension AVX2)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPABSD")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPABSD")
    (extension AVX2)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPABSW")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPABSW")
    (extension AVX2)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPACKSSDW")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPACKSSDW")
    (extension AVX2)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPACKSSWB")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPACKSSWB")
    (extension AVX2)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPACKUSDW")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPACKUSDW")
    (extension AVX2)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPACKUSWB")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPACKUSWB")
    (extension AVX2)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPADDB")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPADDB")
    (extension AVX2)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPADDD")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPADDD")
    (extension AVX2)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPADDQ")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPADDQ")
    (extension AVX2)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPADDSB")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPADDSB")
    (extension AVX2)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPADDSW")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPADDSW")
    (extension AVX2)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPADDUSB")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPADDUSB")
    (extension AVX2)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPADDUSW")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPADDUSW")
    (extension AVX2)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPADDW")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPADDW")
    (extension AVX2)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPALIGNR")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPALIGNR")
    (extension AVX2)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPAND")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPAND")
    (extension AVX2)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPANDN")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPANDN")
    (extension AVX2)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPAVGB")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPAVGB")
    (extension AVX2)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPAVGW")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPAVGW")
    (extension AVX2)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPBLENDD")
    (extension AVX2)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPBLENDVB")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPBLENDVB")
    (extension AVX2)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPBLENDW")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPBLENDW")
    (extension AVX2)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPBROADCASTB")
    (extension AVX2)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPBROADCASTD")
    (extension AVX2)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPBROADCASTQ")
    (extension AVX2)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPBROADCASTW")
    (extension AVX2)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPCMPEQB")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPCMPEQB")
    (extension AVX2)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPCMPEQD")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPCMPEQD")
    (extension AVX2)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPCMPEQQ")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPCMPEQQ")
    (extension AVX2)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPCMPEQW")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPCMPEQW")
    (extension AVX2)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPCMPESTRI")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPCMPESTRI64")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPCMPESTRM")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPCMPESTRM64")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPCMPGTB")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPCMPGTB")
    (extension AVX2)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPCMPGTD")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPCMPGTD")
    (extension AVX2)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPCMPGTQ")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPCMPGTQ")
    (extension AVX2)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPCMPGTW")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPCMPGTW")
    (extension AVX2)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPCMPISTRI")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPCMPISTRI64")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPCMPISTRM")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPERM2F128")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPERM2I128")
    (extension AVX2)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPERMD")
    (extension AVX2)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPERMILPD")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPERMILPS")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPERMPD")
    (extension AVX2)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPERMPS")
    (extension AVX2)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPERMQ")
    (extension AVX2)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPEXTRB")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPEXTRD")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPEXTRQ")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPEXTRW")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPHADDD")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPHADDD")
    (extension AVX2)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPHADDSW")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPHADDSW")
    (extension AVX2)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPHADDW")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPHADDW")
    (extension AVX2)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPHMINPOSUW")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPHSUBD")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPHSUBD")
    (extension AVX2)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPHSUBSW")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPHSUBSW")
    (extension AVX2)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPHSUBW")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPHSUBW")
    (extension AVX2)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPINSRB")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPINSRD")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPINSRQ")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPINSRW")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPMADDUBSW")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPMADDUBSW")
    (extension AVX2)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPMADDWD")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPMADDWD")
    (extension AVX2)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPMASKMOVD")
    (extension AVX2)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPMASKMOVQ")
    (extension AVX2)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPMAXSB")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPMAXSB")
    (extension AVX2)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPMAXSD")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPMAXSD")
    (extension AVX2)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPMAXSW")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPMAXSW")
    (extension AVX2)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPMAXUB")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPMAXUB")
    (extension AVX2)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPMAXUD")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPMAXUD")
    (extension AVX2)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPMAXUW")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPMAXUW")
    (extension AVX2)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPMINSB")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPMINSB")
    (extension AVX2)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPMINSD")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPMINSD")
    (extension AVX2)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPMINSW")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPMINSW")
    (extension AVX2)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPMINUB")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPMINUB")
    (extension AVX2)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPMINUD")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPMINUD")
    (extension AVX2)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPMINUW")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPMINUW")
    (extension AVX2)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPMOVMSKB")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPMOVMSKB")
    (extension AVX2)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPMOVSXBD")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPMOVSXBD")
    (extension AVX2)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPMOVSXBQ")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPMOVSXBQ")
    (extension AVX2)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPMOVSXBW")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPMOVSXBW")
    (extension AVX2)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPMOVSXDQ")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPMOVSXDQ")
    (extension AVX2)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPMOVSXWD")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPMOVSXWD")
    (extension AVX2)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPMOVSXWQ")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPMOVSXWQ")
    (extension AVX2)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPMOVZXBD")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPMOVZXBD")
    (extension AVX2)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPMOVZXBQ")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPMOVZXBQ")
    (extension AVX2)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPMOVZXBW")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPMOVZXBW")
    (extension AVX2)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPMOVZXDQ")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPMOVZXDQ")
    (extension AVX2)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPMOVZXWD")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPMOVZXWD")
    (extension AVX2)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPMOVZXWQ")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPMOVZXWQ")
    (extension AVX2)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPMULDQ")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPMULDQ")
    (extension AVX2)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPMULHRSW")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPMULHRSW")
    (extension AVX2)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPMULHUW")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPMULHUW")
    (extension AVX2)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPMULHW")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPMULHW")
    (extension AVX2)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPMULLD")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPMULLD")
    (extension AVX2)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPMULLW")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPMULLW")
    (extension AVX2)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPMULUDQ")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPMULUDQ")
    (extension AVX2)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPOR")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPOR")
    (extension AVX2)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPSADBW")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPSADBW")
    (extension AVX2)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPSHUFB")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPSHUFB")
    (extension AVX2)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPSHUFD")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPSHUFD")
    (extension AVX2)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPSHUFHW")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPSHUFHW")
    (extension AVX2)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPSHUFLW")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPSHUFLW")
    (extension AVX2)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPSIGNB")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPSIGNB")
    (extension AVX2)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPSIGND")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPSIGND")
    (extension AVX2)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPSIGNW")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPSIGNW")
    (extension AVX2)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPSLLD")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPSLLD")
    (extension AVX2)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPSLLDQ")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPSLLDQ")
    (extension AVX2)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPSLLQ")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPSLLQ")
    (extension AVX2)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPSLLVD")
    (extension AVX2)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPSLLVQ")
    (extension AVX2)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPSLLW")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPSLLW")
    (extension AVX2)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPSRAD")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPSRAD")
    (extension AVX2)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPSRAVD")
    (extension AVX2)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPSRAW")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPSRAW")
    (extension AVX2)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPSRLD")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPSRLD")
    (extension AVX2)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPSRLDQ")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPSRLDQ")
    (extension AVX2)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPSRLQ")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPSRLQ")
    (extension AVX2)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPSRLVD")
    (extension AVX2)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPSRLVQ")
    (extension AVX2)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPSRLW")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPSRLW")
    (extension AVX2)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPSUBB")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPSUBB")
    (extension AVX2)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPSUBD")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPSUBD")
    (extension AVX2)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPSUBQ")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPSUBQ")
    (extension AVX2)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPSUBSB")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPSUBSB")
    (extension AVX2)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPSUBSW")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPSUBSW")
    (extension AVX2)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPSUBUSB")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPSUBUSB")
    (extension AVX2)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPSUBUSW")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPSUBUSW")
    (extension AVX2)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPSUBW")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPSUBW")
    (extension AVX2)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPTEST")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPUNPCKHBW")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPUNPCKHBW")
    (extension AVX2)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPUNPCKHDQ")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPUNPCKHDQ")
    (extension AVX2)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPUNPCKHQDQ")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPUNPCKHQDQ")
    (extension AVX2)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPUNPCKHWD")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPUNPCKHWD")
    (extension AVX2)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPUNPCKLBW")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPUNPCKLBW")
    (extension AVX2)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPUNPCKLDQ")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPUNPCKLDQ")
    (extension AVX2)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPUNPCKLQDQ")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPUNPCKLQDQ")
    (extension AVX2)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPUNPCKLWD")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPUNPCKLWD")
    (extension AVX2)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPXOR")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VPXOR")
    (extension AVX2)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VRCPPS")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VRCPSS")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VROUNDPD")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VROUNDPS")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VROUNDSD")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VROUNDSS")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VRSQRTPS")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VRSQRTSS")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VSHUFPD")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VSHUFPS")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VSQRTPD")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VSQRTPS")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VSQRTSD")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VSQRTSS")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VSTMXCSR")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VSUBPD")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VSUBPS")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VSUBSD")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VSUBSS")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VTESTPD")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VTESTPS")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VUCOMISD")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VUCOMISS")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VUNPCKHPD")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VUNPCKHPS")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VUNPCKLPD")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VUNPCKLPS")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VXORPD")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VXORPS")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VZEROALL")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "VZEROUPPER")
    (extension AVX)
    (status not-yet-implemented)
    (reason "Кодування з префіксом VEX ще не реалізовано"))
  (coverage
    (iclass "WBINVD")
    (extension X86-BASE)
    (status not-yet-implemented)
    (reason "Решта форм BASE очікує поетапної реалізації"))
  (coverage
    (iclass "WRMSR")
    (extension X86-BASE)
    (status not-yet-implemented)
    (reason "Решта форм BASE очікує поетапної реалізації"))
  (coverage
    (iclass "XADD")
    (extension X86-BASE)
    (status not-yet-implemented)
    (reason "Решта форм BASE очікує поетапної реалізації"))
  (coverage
    (iclass "XADD_LOCK")
    (extension X86-BASE)
    (status not-yet-implemented)
    (reason "Решта форм BASE очікує поетапної реалізації"))
  (coverage
    (iclass "XCHG")
    (extension X86-BASE)
    (status partial)
    (reason "За структурованим допуском Lisp щонайменше одна форма відповідає закріпленому ICLASS; повне покриття операндів і способів адресації XED не підтверджене"))
  (coverage
    (iclass "XGETBV")
    (extension XSAVE)
    (status not-yet-implemented)
    (reason "Кодування стану керування XSAVE ще не реалізовано"))
  (coverage
    (iclass "XLAT")
    (extension X86-BASE)
    (status not-yet-implemented)
    (reason "Решта форм BASE очікує поетапної реалізації"))
  (coverage
    (iclass "XOR")
    (extension X86-BASE)
    (status partial)
    (reason "За структурованим допуском Lisp щонайменше одна форма відповідає закріпленому ICLASS; повне покриття операндів і способів адресації XED не підтверджене"))
  (coverage
    (iclass "XORPD")
    (extension SSE2)
    (status partial)
    (reason "За структурованим допуском Lisp щонайменше одна форма відповідає закріпленому ICLASS; повне покриття операндів і способів адресації XED не підтверджене"))
  (coverage
    (iclass "XORPS")
    (extension SSE)
    (status not-yet-implemented)
    (reason "Кодування обов'язкового префікса й ModRM для SSE ще не реалізовано"))
  (coverage
    (iclass "XOR_LOCK")
    (extension X86-BASE)
    (status not-yet-implemented)
    (reason "Решта форм BASE очікує поетапної реалізації"))
  (coverage
    (iclass "XRSTOR")
    (extension XSAVE)
    (status not-yet-implemented)
    (reason "Кодування стану керування XSAVE ще не реалізовано"))
  (coverage
    (iclass "XRSTOR64")
    (extension XSAVE)
    (status not-yet-implemented)
    (reason "Кодування стану керування XSAVE ще не реалізовано"))
  (coverage
    (iclass "XSAVE")
    (extension XSAVE)
    (status not-yet-implemented)
    (reason "Кодування стану керування XSAVE ще не реалізовано"))
  (coverage
    (iclass "XSAVE64")
    (extension XSAVE)
    (status not-yet-implemented)
    (reason "Кодування стану керування XSAVE ще не реалізовано"))
  (coverage
    (iclass "XSETBV")
    (extension XSAVE)
    (status not-yet-implemented)
    (reason "Кодування стану керування XSAVE ще не реалізовано"))
)
