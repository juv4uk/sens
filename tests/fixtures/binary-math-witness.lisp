; #216 — Lisp-owned verdict for exact-Q binary comparison rows.

(визначити binary-field
  (функція (row field)
    (нехай ((found (знайти-за-ключем field row)))
      (за-умовою
        ((атом? found) (як-є ()))
        (так (решта found))))))

(визначити binary-math-verdict
  (функція (row actual-kind actual-render)
    (за-умовою
      ((хибне? (однакові? (binary-field row (як-є expected-kind)) actual-kind))
       (список (як-є binary-math-result)
             (список (як-є status) (як-є fail))
             (список (як-є detail)
                   (список (як-є kind)
                         (binary-field row (як-є expected-kind))
                         actual-kind))))
      ((хибне? (однакові? (binary-field row (як-є expected-render)) actual-render))
       (список (як-є binary-math-result)
             (список (як-є status) (як-є fail))
             (список (як-є detail)
                   (список (як-є render)
                         (binary-field row (як-є expected-render))
                         actual-render))))
      (так
       (список (як-є binary-math-result)
             (список (як-є status) (як-є pass))
             (список (як-є detail) (binary-field row (як-є decision))))))))
