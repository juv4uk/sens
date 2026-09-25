(def fib (lambda (n)
  (cond ((eq n 0) 0)
        ((eq n 1) 1)
        (t (+ (fib (- n 1)) (fib (- n 2)))))))
