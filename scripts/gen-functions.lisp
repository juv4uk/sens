;; Live builtin inventory (contract 2.1): every binding whose value prints
;; as #<builtin ...>. Run: ./target/release/my-lisp scripts/gen-functions.lisp
;; Output: one builtin name per line.
(00001001 builtins
  (00111000
    (00001000 (p) (00111101 "#<builtin" (01001100 (00000110 p))))
    (01001110)))

(00001001 emit-pair
  (00001000 (p)
    (01001001 (00000101 p))))

(00001001 emit
  (00001000 (lst)
    (00000111
      ((00000010 lst) () (00000001 ()))
      ((00000010 lst) (1) (00000001 ()))
      (t (00000100
           (emit-pair (00000101 lst))
           (emit (00000110 lst)))))))

(emit builtins)
