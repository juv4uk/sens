;; Live builtin inventory (contract 2.1): every binding whose value prints
;; as #<builtin ...>. Run: ./target/release/my-lisp scripts/gen-functions.lisp
;; Output: one builtin name per line.
(визначити builtins
  (101001
    (функція (p) (110101010 "#<builtin" (11110100 (решта p))))
    (11100111)))

(визначити emit-pair
  (функція (p)
    (11010110 (перше p))))

(визначити emit
  (функція (lst)
    (за-умовою
      ((атом? lst) (як-є ()))
      ((атом? (як-є ())) (сполучити
           (emit-pair (перше lst))
           (emit (решта lst)))))))

(emit builtins)
