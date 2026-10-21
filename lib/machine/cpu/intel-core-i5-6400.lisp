; Конкретний профіль можливостей процесора Intel Core i5-6400 (Skylake).
; Це відомості про обладнання, а не семантичний реєстр СЕНС.
; Статичні властивості моделі походять з Intel ARK та Intel SDM.
; Можливості, залежні від стану процесу, перевіряються під час
; виконання через CPUID, XGETBV та підтримку операційної системи.

(cpu-profile-1
  (cpu intel-core-i5-6400)
  (microarchitecture skylake)
  (isa x86-64)
  (mode 64-bit)

  ; Базові можливості архітектури в 64-бітному режимі користувача.
  (supported-extension X86-BASE)
  (supported-extension X86-64)
  (supported-extension X87)
  (supported-extension MMX)
  (supported-extension SSE)
  (supported-extension SSE2)
  (supported-extension SSE3)
  (supported-extension SSSE3)
  (supported-extension SSE4.1)
  (supported-extension SSE4.2)

  ; Векторні, криптографічні, випадкові та побітові можливості
  ; цього клієнтського процесора Skylake. Перед вибором шляху,
  ; залежного від стану процесу чи ОС, виконавець перевіряє
  ; відповідні CPUID та XGETBV.
  (gated-extension AES-NI (gate cpuid-aes))
  (gated-extension PCLMULQDQ (gate cpuid-pclmulqdq))
  (gated-extension AVX (gate cpuid-avx+osxsave+xgetbv-xmm-ymm))
  (gated-extension F16C (gate cpuid-f16c+avx-state))
  (gated-extension FMA3 (gate cpuid-fma+avx-state))
  (gated-extension BMI1 (gate cpuid-bmi1))
  (gated-extension BMI2 (gate cpuid-bmi2))
  (gated-extension AVX2 (gate cpuid-avx2+avx-state))
  (gated-extension RDRAND (gate cpuid-rdrand))
  (gated-extension RDSEED (gate cpuid-rdseed))
  (gated-extension ADX (gate cpuid-adx))
  (gated-extension XSAVE (gate cpuid-xsave))
  (gated-extension CLFLUSHOPT (gate cpuid-clflushopt))

  ; Можливості моделі, які додатково обмежує прошивка, ОС чи платформа.
  (platform-gated-extension MPX (gate cpuid-mpx+os-support))
  (platform-gated-extension SGX (gate cpuid-sgx+firmware+os-support))

  ; Віртуалізація належить до можливостей процесора та платформи,
  ; а не до звичайних команд режиму користувача для зниження семантики.
  (virtualization-capability VT-X supported)
  (virtualization-capability VT-D supported)
  (virtualization-capability EPT supported)

  ; Явні відомості про відсутні можливості забороняють вибирати
  ; пізніші покоління Intel або вимкнені функції цієї моделі.
  (unavailable-extension TSX)
  (unavailable-extension AVX-512)
  (unavailable-extension AMX)

  (execution-policy
    (ordinary-user-instructions user-mode)
    (privileged-instructions forbidden)
    (runtime-feature-check required)
    (avx-state-check xgetbv-required)))
