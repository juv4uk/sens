; Pinned/versioned external-evidence provenance for #175 (MACHINE-ISA-2).
;
; XED is imported here strictly as external technical evidence for
; instruction-form facts (class, category, ISA-set grouping, operand
; descriptors). It is never semantic authority: nothing here mints or
; renames a public semantic ID, and no XED mnemonic reaches
; lib/generated/meta-semantic-registry.lisp or lib/surface/*. See #150.
;
; The vendored files below are verbatim copies (including their own
; Apache-2.0 license headers) of the named upstream files at the pinned
; commit. Only files actually consumed by the import pipeline are
; vendored; each vendored file keeps its full original content rather
; than a hand-trimmed excerpt, so the import step -- not this commit --
; is the place that decides which extensions/forms are admitted.

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

  ; XED-extension-tag -> my-lisp admitted-extension name (see
  ; lib/machine/cpu/intel-core-i5-6400-inventory.lisp). This mapping is a
  ; data-transport concern only: every target name already exists as an
  ; admitted-extension there, so this table renames nothing new into
  ; existence -- it only aligns two pre-existing vocabularies.
  (extension-mapping (BASE X86-BASE))
  (extension-mapping (LONGMODE X86-64))
  (extension-mapping (X87 X87))
  (extension-mapping (MMX MMX))
  (extension-mapping (SSE SSE))
  (extension-mapping (SSE2 SSE2))
  (extension-mapping (SSE3 SSE3))
  (extension-mapping (SSSE3 SSSE3))
  ; The pinned data's SSE4 tag predates the SSE4.1/SSE4.2 split and carries
  ; no field that distinguishes them, so every SSE4-tagged form is admitted
  ; under both existing admitted extensions rather than guessing which one.
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

  ; ADX has no distinct EXTENSION-tagged source file in the pinned XED
  ; checkout used here (its forms are folded into a chip-set file rather
  ; than an isa-form file at this commit); it is intentionally not
  ; imported in this pass. #174's admission of ADX stands on the CPU
  ; capability profile alone until a suitable source is identified.
  (not-yet-sourced ADX))
