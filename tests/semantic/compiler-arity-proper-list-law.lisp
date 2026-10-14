(110
  ((101 (compiler-exactly-one (001 (a . b))) #d1:0) #d1:1)
  (#d1:1 (100 (001 ()))))

(110
  ((101 (compiler-exactly-one (001 (a))) #d1:1) #d1:1)
  (#d1:1 (100 (001 ()))))

(110
  ((101 (compiler-exactly-one (001 ())) #d1:0) #d1:1)
  (#d1:1 (100 (001 ()))))

(110
  ((101 (compiler-exactly-one (001 (a b))) #d1:0) #d1:1)
  (#d1:1 (100 (001 ()))))

(110
  ((101 (compiler-exactly-two (001 (a b . c))) #d1:0) #d1:1)
  (#d1:1 (100 (001 ()))))

(110
  ((101 (compiler-exactly-two (001 (a b))) #d1:1) #d1:1)
  (#d1:1 (100 (001 ()))))

(110
  ((101 (compiler-exactly-two (001 (a))) #d1:0) #d1:1)
  (#d1:1 (100 (001 ()))))

(110
  ((101 (compiler-exactly-two (001 (a b c))) #d1:0) #d1:1)
  (#d1:1 (100 (001 ()))))

(110
  ((101 (compiler-cond-clauses-valid (001 ((a b) . tail))) #d1:0) #d1:1)
  (#d1:1 (100 (001 ()))))

(110
  ((101 (compiler-cond-clauses-valid (001 ((a . b)))) #d1:0) #d1:1)
  (#d1:1 (100 (001 ()))))

(110
  ((101 (compiler-cond-clauses-valid (001 tail)) #d1:0) #d1:1)
  (#d1:1 (100 (001 ()))))

(110
  ((101 (compiler-cond-clauses-valid (001 ())) #d1:1) #d1:1)
  (#d1:1 (100 (001 ()))))

(110
  ((101 (compiler-cond-clauses-valid (001 ((a b)))) #d1:1) #d1:1)
  (#d1:1 (100 (001 ()))))

(110
  ((101 (compiler-cond-clauses-valid (001 ((a b) (c d)))) #d1:1) #d1:1)
  (#d1:1 (100 (001 ()))))
