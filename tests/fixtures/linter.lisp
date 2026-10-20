(
  (expr . "(аналіз-розмір 5)")
  (expected . "1")
)
(
  (expr . "(аналіз-розмір (як-є (a b)))")
  (expected . "5")
)
(
  (expr . "(аналіз-вкладеність (як-є (a (b c) d)))")
  (expected . "2") ; (b c) is nested 1 level inside the main list... wait. A list of depth 1 has max nesting 1?
  ; '(a) is (a . ()). Nesting(a)=0, Nesting(())=0. Nesting((a)) = max(1+0, 0) = 1.
  ; '(a b) = (a . (b . ())). max(1+0, 1) = 1.
  ; '(a (b c) d) = (a . ((b c) . (d . ()))).
  ; (b c) has nesting 1. (b c) is the car of ((b c) . (d)). So 1+1 = 2! Yes, 2!
)
(
  (expr . "(аналіз-складність (як-є (cond (a b) (c d))))")
  (expected . "2")
)
(
  (expr . "(аналіз-складність (як-є (def f (lambda (x) (cond (x 1) (t 2))))))")
  (expected . "2")
)
(
  (expr . "(аналіз-ефекти (як-є (def f (lambda () (print \"hi\")))))")
  (expected . "((print \"hi\"))")
)
(
  (expr . "(аналіз-глобальні (як-є (lambda (x y) (+ x y z))))")
  (expected . "(z)")
)
(
  (expr . "(аналіз-глобальні (як-є (let* ((x 1) (y x)) (+ x y z))))")
  (expected . "(z)")
)
(
  (expr . "(аналіз-глобальні (як-є (letrec ((even? (lambda (n) (odd? n))) (odd? (lambda (n) (even? n)))) (even? z))))")
  (expected . "(z)")
)
(
  (expr . "(аналіз-глобальні (як-є (let loop ((n 10)) (cond ((= n 0) z) (t (loop (- n 1)))))))")
  (expected . "(z)")
)
(
  (expr . "(аналіз-глобальні (як-є (defmacro m (a b) (+ a b c))))")
  (expected . "(c)")
)
(
  (expr . "(взяти-межу (як-є max-size) (як-є ((max-size . 50))) 99)")
  (expected . "50")
)
(
  (expr . "(взяти-межу (як-є max-nesting) (як-є ((max-size . 50))) 99)")
  (expected . "99")
)
(
  (expr . "(аналіз-перевірити (як-є (def f (lambda (x y) (cond (x 1) (t 2))))) (як-є ((max-complexity . 1) (max-nesting . 10))))")
  (expected . "((complexity-exceeded 2))")
)
(
  (expr . "(аналіз-перевірити (як-є (def f (lambda (x y) (+ x y z)))) (як-є ((max-globals . 0))))")
  (expected . "((globals-exceeded (z)))")
)
(
  (expr . "(аналіз-перевірити (як-є (def f (lambda () (print \"hi\")))) (як-є ((max-effects . 0))))")
  (expected . "((effects-exceeded ((print \"hi\"))))")
)
(
  (expr . "(аналіз-перевірити (як-є (def f (lambda (x) x))) (як-є ((max-size . 1))))")
  (expected . "((size-exceeded 15))")
)
(
  (expr . "(аналіз-перевірити (як-є (def f (lambda (x) x))) (як-є ((max-size . 15) (max-complexity . 5) (max-nesting . 5) (max-globals . 0) (max-effects . 0))))")
  (expected . "()")
)
