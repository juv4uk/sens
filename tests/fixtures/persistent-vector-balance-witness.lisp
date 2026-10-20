; #305 — persistent-vector AVL-balance law is owned by Lisp.
; Inserting ascending keys into an empty vector must produce an AVL-balanced
; tree whose height remains logarithmic (< 15 for 500 items), not O(n).
; Ukrainian projection only.

(load "lib/core.lisp")
(load "lib/persistent-vector.lisp")

(визначити range-list
  (функція (n acc)
    (за-умовою
      ((менше? n 0) acc)
      (так (range-list (відняти n 1) (сполучити n acc))))))

(визначити persistent-vector-balance-check
  (функція ()
    (нехай ((v (вектор-з-список (range-list 499 (як-є ()))))
           (h (вектор-вузол-висота (отримати-дерево-вектора v))))
      (за-умовою
        ((менше? h 15)
         (як-є (persistent-vector-balance-witness (status pass))))
        (так
         (список
           (як-є persistent-vector-balance-witness)
           (як-є (status fail))
           (список (як-є height) h)))))))

(persistent-vector-balance-check)
