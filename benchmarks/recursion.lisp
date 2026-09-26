; Recursion benchmark · Benchmark рекурсії · Rekursions-Benchmark
(00001001 walk
  (00001000 (values)
    (00000111
      ((00000010 values) () (00000001 done))
      ((00000010 values) (1) (00000001 done))
      (t (walk (00000110 values))))))
(walk (00000001 (1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20)))
