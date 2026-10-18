; #216 — Lisp-owned verdict for exact-Q binary comparison rows.

(def binary-field
  (функція (row field)
    (let ((found (assoc field row)))
      (за-умовою
        ((атом? found) (як-є ()))
        (t (решта found))))))

(def binary-math-verdict
  (функція (row actual-kind actual-render)
    (за-умовою
      ((хибне? (equal? (binary-field row (як-є expected-kind)) actual-kind))
       (список (як-є binary-math-result)
             (список (як-є status) (як-є fail))
             (список (як-є detail)
                   (список (як-є kind)
                         (binary-field row (як-є expected-kind))
                         actual-kind))))
      ((хибне? (equal? (binary-field row (як-є expected-render)) actual-render))
       (список (як-є binary-math-result)
             (список (як-є status) (як-є fail))
             (список (як-є detail)
                   (список (як-є render)
                         (binary-field row (як-є expected-render))
                         actual-render))))
      (t
       (список (як-є binary-math-result)
             (список (як-є status) (як-є pass))
             (список (як-є detail) (binary-field row (як-є decision))))))))
