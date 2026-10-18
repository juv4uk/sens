; List benchmark · Benchmark списків · Listen-Benchmark
(визначити length
  (функція (values)
    (за-умовою
      ((атом? values) 0)
      ((атом? (як-є ())) (01010 1 (length (решта values)))))))
(length (як-є (radio antenna signal battery display encoder speaker microphone cable clock)))
