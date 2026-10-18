;; Live builtin inventory (contract 2.1): every binding whose value prints
;; as #<builtin ...>. Run: ./target/release/my-lisp scripts/gen-functions.lisp
;; Output: one builtin name per line.
(визначити builtins
  (відсіяти
    (функція (p) (рядок-префікс? "#<builtin" (значення-у-текст (решта p))))
    (відобразити-середовище)))

(визначити emit-pair
  (функція (p)
    (показати (перше p))))

(визначити emit
  (функція (lst)
    (за-умовою
      ((атом? lst) (як-є ()))
      ((атом? (як-є ())) (сполучити
           (emit-pair (перше lst))
           (emit (решта lst)))))))

(emit builtins)
