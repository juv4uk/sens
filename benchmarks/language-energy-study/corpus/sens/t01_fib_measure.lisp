; #6287 ENERGY-02 / T01-symbolic-recursion, MEASURE_SIZE n=24.
; Identical recurrence to t01_fib.lisp (VERIFY_SIZE n=12).
; Source-side fixed input because CLI file execution does not accept TASK_N.
; This is NOT a semantic law and is not a substitute for native SENS witnesses.
; Expected external observable stdout for the frozen T01 measurement: 46368.

(визначити два
  (додати число-один число-один))

(визначити фіб
  (функція (к)
    (за-умовою
      ((менше? к два) к)
      ((додати (фіб (відняти к число-один))
               (фіб (відняти к два)))))))

(фіб 24)
