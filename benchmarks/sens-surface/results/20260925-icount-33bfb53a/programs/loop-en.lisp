(def loop (lambda (n acc)
  (cond ((eq n 0) acc)
        (t (loop (- n 1) (+ acc 2))))))
(print (loop 5000 0))
