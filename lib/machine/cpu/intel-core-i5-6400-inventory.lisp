; Ратифікований перелік ISA клієнтського Skylake для Intel Core i5-6400 (#174).
;
; Цей файл допускає перелік форм машинних команд, виведений
; із відомостей intel-core-i5-6400.lisp та звірений з описом Intel
; відмінностей Skylake від Broadwell (Intel XED datafiles/skl/skl-chips.txt:
; SKYLAKE = ALL_OF(BROADWELL) + MPX + XSAVEC + XSAVES + SGX + CLFLUSHOPT).
;
; Допуск посилається лише на наявні каталоги lib/machine/isa/*.lisp,
; якими володіє СЕНС; мнемоніки ISA не одержують семантичних
; повноважень (див. #150). AVX-512 серверного Skylake виключено,
; бо це профіль клієнтської моделі. Для AVX/AVX2 недостатньо
; самого CPUID: ОС повинна ввімкнути XSAVE (CR4.OSXSAVE + XGETBV).

(skylake-client-inventory/1
  (cpu intel-core-i5-6400)
  (microarchitecture skylake)
  (profile-class client)
  (source lib/machine/cpu/intel-core-i5-6400.lisp)
  (походження intel-ark)
  (походження intel-sdm)
  (походження (intel-xed datafiles/skl/skl-chips.txt))
  (admission-policy fail-closed)

  ; Базові можливості архітектури, допущені за даними про підтримку.
  (admitted-extension X86-BASE)
  (admitted-extension X86-64)
  (admitted-extension X87)
  (admitted-extension MMX)
  (admitted-extension SSE)
  (admitted-extension SSE2)
  (admitted-extension SSE3)
  (admitted-extension SSSE3)
  (admitted-extension SSE4.1)
  (admitted-extension SSE4.2)

  ; Родини команд під контролем CPUID, допущені за наявними каталогами СЕНС.
  (admitted-extension AES-NI)
  (admitted-extension PCLMULQDQ)
  (admitted-extension AVX)
  (admitted-extension F16C)
  (admitted-extension FMA3)
  (admitted-extension BMI1)
  (admitted-extension BMI2)
  (admitted-extension AVX2)
  (admitted-extension RDRAND)
  (admitted-extension RDSEED)
  (admitted-extension ADX)
  (admitted-extension XSAVE)
  (admitted-extension CLFLUSHOPT)

  ; Можливості під контролем платформи залишаються в каталозі форм.
  ; Перед виконанням обов'язкова перевірка прошивки й ОС.
  (admitted-extension MPX)
  (admitted-extension SGX)

  ; Форми AVX/AVX2 безпечно виконувати лише після ввімкнення
  ; операційною системою розширеного стану XSAVE. CPUID недостатньо.
  (runtime-gated-extension AVX cpuid-avx+osxsave+xgetbv-xmm-ymm)
  (runtime-gated-extension AVX2 cpuid-avx2+avx-state)

  ; Віртуалізація — властивість платформи, а не допущений набір
  ; команд режиму користувача. VT-X, VT-D та EPT не допускаються.

  ; Явний перелік відсутніх можливостей, відповідно до базового профілю.
  (unavailable-extension TSX)
  (unavailable-extension AVX-512)
  (unavailable-extension AMX))
