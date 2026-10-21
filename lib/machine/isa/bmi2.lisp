; Каталог машинних команд BMI2; лише фізичні факти ISA.
; Точні поля VEX звіряються з XED, доки кодувальник Lisp
; не допустить конкретну форму з перевіреною відповідністю.

(isa-catalogue-1
  (extension BMI2)
  (source intel-sdm/intel-xed)
  (runtime-gate cpuid-bmi2)
  (coverage identity-seed)
  (instructions
    (instruction PDEP
      (class parallel-bit-deposit)
      (feature BMI2)
      (privilege user)
      (encoding-authority intel-xed))
    (instruction PEXT
      (class parallel-bit-extract)
      (feature BMI2)
      (privilege user)
      (encoding-authority intel-xed))
    (instruction MULX
      (class integer-multiply)
      (feature BMI2)
      (privilege user)
      (encoding-authority intel-xed))
    (instruction SHLX
      (class variable-shift)
      (feature BMI2)
      (privilege user)
      (encoding-authority intel-xed))
    (instruction SHRX
      (class variable-shift)
      (feature BMI2)
      (privilege user)
      (encoding-authority intel-xed))
    (instruction SARX
      (class variable-shift)
      (feature BMI2)
      (privilege user)
      (encoding-authority intel-xed))))
