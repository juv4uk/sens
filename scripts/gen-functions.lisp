;; Live builtin inventory (contract 2.1): every binding whose value prints
;; as #<builtin ...>. Run: ./target/release/my-lisp scripts/gen-functions.lisp
;; Output: one builtin name per line.
(0011 builtins
  (101001
    (0010 (p) (110101010 "#<builtin" (11110100 (011 p))))
    (11100111)))

(0011 emit-pair
  (0010 (p)
    (11010110 (100 p))))

(0011 emit
  (0010 (lst)
    (110
      ((010 lst) () (001 ()))
      ((010 lst) (1) (001 ()))
      (t (111
           (emit-pair (100 lst))
           (emit (011 lst)))))))

(emit builtins)
