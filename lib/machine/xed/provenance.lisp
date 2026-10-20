; Закріплені й версіоновані джерела зовнішніх технічних доказів для #175 (MACHINE-ISA-2).
;
; XED імпортується сюди виключно як зовнішнє джерело технічних
; відомостей про форми інструкцій: класи, категорії, набори ISA
; та описи операндів. Це не джерело семантичних повноважень:
; тут не створюють і не перейменовують відкриті семантичні коди,
; а мнемоніки XED не потрапляють до метареєстру чи мовних
; проєкцій lib/surface/*. Див. #150.
;
; Наведені нижче файли постачальника є точними копіями
; відповідних файлів джерела на закріпленому коміті, разом
; із заголовками ліцензії Apache-2.0. Копіюються лише файли,
; які справді читає процес імпорту. Кожен зберігає повний
; вихідний вміст, без ручного обрізання фрагментів.
; Лише етап імпорту визначає, які розширення й форми допускати.

(xed-provenance/1
  (repository "https://github.com/intelxed/xed.git")
  (pinned-commit "0bcb6237345c5066726dcc08b3d87928df3b5b26")
  (pinned-commit-date "2026-08-24T14:44:12+03:00")
  (license "Apache-2.0")

  (vendored-file
    (path "lib/machine/xed/vendor/base/xed-isa.txt")
    (upstream-path "datafiles/xed-isa.txt")
    (covers-extensions (BASE LONGMODE X87 MMX SSE SSE2 SSE3 SSSE3 SSE4 AES PCLMULQDQ XSAVE)))

  (vendored-file
    (path "lib/machine/xed/vendor/avx/avx-isa.txt")
    (upstream-path "datafiles/avx/avx-isa.txt")
    (covers-extensions (AVX)))

  (vendored-file
    (path "lib/machine/xed/vendor/avx2-fma/avx-fma-isa.xed.txt")
    (upstream-path "datafiles/hswavx/avx-fma-isa.xed.txt")
    (covers-extensions (FMA)))

  (vendored-file
    (path "lib/machine/xed/vendor/avx2-fma/hsw-int256-isa.txt")
    (upstream-path "datafiles/hswavx/hsw-int256-isa.txt")
    (covers-extensions (AVX2)))

  (vendored-file
    (path "lib/machine/xed/vendor/avx2-fma/hsw-vshift-isa.txt")
    (upstream-path "datafiles/hswavx/hsw-vshift-isa.txt")
    (covers-extensions (AVX2)))

  (vendored-file
    (path "lib/machine/xed/vendor/avx2-fma/movnt-load-isa.txt")
    (upstream-path "datafiles/hswavx/movnt-load-isa.txt")
    (covers-extensions (AVX2)))

  (vendored-file
    (path "lib/machine/xed/vendor/bmi/hsw-bmi-vex-isa.xed.txt")
    (upstream-path "datafiles/hswbmi/hsw-bmi-vex-isa.xed.txt")
    (covers-extensions (BMI1 BMI2)))

  (vendored-file
    (path "lib/machine/xed/vendor/bmi/tzcnt-isa.xed.txt")
    (upstream-path "datafiles/hswbmi/tzcnt-isa.xed.txt")
    (covers-extensions (BMI1)))

  (vendored-file
    (path "lib/machine/xed/vendor/clflushopt/clflushopt.xed.txt")
    (upstream-path "datafiles/clflushopt/clflushopt.xed.txt")
    (covers-extensions (CLFLUSHOPT)))

  (vendored-file
    (path "lib/machine/xed/vendor/mpx/mpx-isa.txt")
    (upstream-path "datafiles/mpx/mpx-isa.txt")
    (covers-extensions (MPX)))

  (vendored-file
    (path "lib/machine/xed/vendor/sgx/sgx-isa.xed.txt")
    (upstream-path "datafiles/sgx/sgx-isa.xed.txt")
    (covers-extensions (SGX)))

  (vendored-file
    (path "lib/machine/xed/vendor/rdrand/rdrand-isa.xed.txt")
    (upstream-path "datafiles/rdrand/rdrand-isa.xed.txt")
    (covers-extensions (RDRAND)))

  (vendored-file
    (path "lib/machine/xed/vendor/rdseed/rdseed-isa.xed.txt")
    (upstream-path "datafiles/rdseed/rdseed-isa.xed.txt")
    (covers-extensions (RDSEED)))

  (vendored-file
    (path "lib/machine/xed/vendor/f16c/fp16-isa.txt")
    (upstream-path "datafiles/ivbavx/fp16-isa.txt")
    (covers-extensions (F16C)))

  ; Тег розширення XED зіставляється з уже допущеним розширенням
  ; у lib/machine/cpu/intel-core-i5-6400-inventory.lisp.
  ; Це лише узгодження форматів даних: усі цільові назви
  ; вже існують у профілі допуску. Таблиця не створює
  ; нових семантичних сутностей, а поєднує два наявні словники.
  (extension-mapping (BASE X86-BASE))
  (extension-mapping (LONGMODE X86-64))
  (extension-mapping (X87 X87))
  (extension-mapping (MMX MMX))
  (extension-mapping (SSE SSE))
  (extension-mapping (SSE2 SSE2))
  (extension-mapping (SSE3 SSE3))
  (extension-mapping (SSSE3 SSSE3))
  ; У закріплених даних тег SSE4 передує розподілу на SSE4.1/SSE4.2
  ; та не має поля для їх розрізнення. Тому кожна форма з тегом SSE4
  ; віднесена до обох уже допущених розширень без довільного вибору.
  (extension-mapping (SSE4 SSE4.1+SSE4.2))
  (extension-mapping (AES AES-NI))
  (extension-mapping (PCLMULQDQ PCLMULQDQ))
  (extension-mapping (XSAVE XSAVE))
  (extension-mapping (AVX AVX))
  (extension-mapping (AVX2 AVX2))
  (extension-mapping (FMA FMA3))
  (extension-mapping (BMI1 BMI1))
  (extension-mapping (BMI2 BMI2))
  (extension-mapping (CLFLUSHOPT CLFLUSHOPT))
  (extension-mapping (MPX MPX))
  (extension-mapping (SGX SGX))
  (extension-mapping (RDRAND RDRAND))
  (extension-mapping (RDSEED RDSEED))
  (extension-mapping (F16C F16C))

  ; У закріпленому XED немає окремого вихідного файлу ADX
  ; з тегом EXTENSION: його форми містяться у файлі набору
  ; можливостей процесора, а не форм ISA. Тому в цьому проході
  ; ADX свідомо не імпортовано. Допуск ADX за #174 наразі
  ; спирається лише на профіль можливостей процесора,
  ; доки не встановлено відповідне джерело.
  (not-yet-sourced ADX))
