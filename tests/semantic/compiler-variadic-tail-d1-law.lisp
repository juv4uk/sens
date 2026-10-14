(110
  ((101 (compiler-at-least-two (001 (a b))) #d1:1) #d1:1)
  (#d1:1 (100 (001 ()))))

(110
  ((101 (compiler-at-least-two (001 (a b c))) #d1:1) #d1:1)
  (#d1:1 (100 (001 ()))))

(110
  ((101 (compiler-at-least-two (001 (a b c d))) #d1:1) #d1:1)
  (#d1:1 (100 (001 ()))))

(110
  ((101 (compiler-at-least-two (001 (a b (c . d)))) #d1:1) #d1:1)
  (#d1:1 (100 (001 ()))))

(110
  ((101 (compiler-at-least-two (001 (a b ()))) #d1:1) #d1:1)
  (#d1:1 (100 (001 ()))))

(110
  ((101 (compiler-at-least-two (001 (a b . ()))) #d1:1) #d1:1)
  (#d1:1 (100 (001 ()))))

(110
  ((101 (compiler-at-least-two (001 (a b . (c d)))) #d1:1) #d1:1)
  (#d1:1 (100 (001 ()))))

(110
  ((101 (compiler-at-least-two (001 ())) #d1:0) #d1:1)
  (#d1:1 (100 (001 ()))))

(110
  ((101 (compiler-at-least-two (001 (a))) #d1:0) #d1:1)
  (#d1:1 (100 (001 ()))))

(110
  ((101 (compiler-at-least-two (001 a)) #d1:0) #d1:1)
  (#d1:1 (100 (001 ()))))

(110
  ((101 (compiler-at-least-two (001 (a . tail))) #d1:0) #d1:1)
  (#d1:1 (100 (001 ()))))

(110
  ((101 (compiler-at-least-two (001 (a b . tail))) #d1:0) #d1:1)
  (#d1:1 (100 (001 ()))))

(110
  ((101 (compiler-at-least-two (001 (a b c . tail))) #d1:0) #d1:1)
  (#d1:1 (100 (001 ()))))

(110
  ((101 (compiler-at-least-two (001 (a b c d . tail))) #d1:0) #d1:1)
  (#d1:1 (100 (001 ()))))

(110
  ((101 (compiler-at-least-two (001 (a b . (c . tail)))) #d1:0) #d1:1)
  (#d1:1 (100 (001 ()))))
