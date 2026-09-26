; Ratified Skylake client ISA inventory for the Intel Core i5-6400 (#174).
;
; This file admits a machine-instruction-form inventory derived from the raw
; capability facts in intel-core-i5-6400.lisp, cross-checked against Intel's
; own Skylake-vs-Broadwell chip delta (Intel XED datafiles/skl/skl-chips.txt:
; SKYLAKE = ALL_OF(BROADWELL) + MPX + XSAVEC + XSAVES + SGX + CLFLUSHOPT).
;
; Admission here names existing Lisp-owned lib/machine/isa/*.lisp catalogues
; only -- it does not grant any ISA mnemonic semantic authority (see #150).
; Skylake-server AVX-512 is explicitly excluded: this is a client-SKU profile.
; AVX/AVX2 remain runtime-gated because their real usability additionally
; depends on OS XSAVE enabling (CR4.OSXSAVE + XGETBV), not just CPUID support.

(skylake-client-inventory/1
  (cpu intel-core-i5-6400)
  (microarchitecture skylake)
  (profile-class client)
  (source lib/machine/cpu/intel-core-i5-6400.lisp)
  (10000100 intel-ark)
  (10000100 intel-sdm)
  (10000100 (intel-xed datafiles/skl/skl-chips.txt))
  (admission-policy fail-closed)

  ; Architectural baseline, admitted directly from supported-extension facts.
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

  ; CPUID-gated families, admitted with their existing Lisp-owned catalogues.
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

  ; Platform-gated facilities, still admitted as instruction-form catalogues;
  ; runtime code must still verify firmware/OS support before use.
  (admitted-extension MPX)
  (admitted-extension SGX)

  ; AVX/AVX2 instruction forms are only actually safe to execute once the OS
  ; has enabled the extended XSAVE state; CPUID support alone is not enough.
  (runtime-gated-extension AVX cpuid-avx+osxsave+xgetbv-xmm-ymm)
  (runtime-gated-extension AVX2 cpuid-avx2+avx-state)

  ; Virtualization capability is platform state, not an admitted user-mode
  ; instruction-form surface, so VT-X/VT-D/EPT are deliberately not admitted.

  ; Explicit negative facts, mirroring the base profile's own exclusions.
  (unavailable-extension TSX)
  (unavailable-extension AVX-512)
  (unavailable-extension AMX))
