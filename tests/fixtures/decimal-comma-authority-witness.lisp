; #220 — decimal comma semantic expectations belong to Lisp, not Rust.
; Rust may continue to observe parser mechanics, but equivalence/identity
; verdicts for comma/dot exact numbers and numeric buffers are language data.

(def decimal-comma-authority-rows
  (lambda ()
    (list
      (list (quote comma-dot-exact)
            (eq? 12,455 12.455)
            (quote (1)))
      (list (quote comma-dot-negative-exact)
            (eq? -0,25 -0.25)
            (quote (1)))
      (list (quote comma-exponent-exact)
            (eq? 1,5e3 1500)
            (quote (1)))
      (list (quote read-comma-exact)
            (eq? (read "12,455") 12.455)
            (quote (1)))
      (list (quote comma-arithmetic-exact)
            (eq? (+ 1,5 2,5) 4)
            (quote (1)))
      (list (quote f32-comma-signed-zero-distinct)
            (eq? #f32(-0,0) #f32(0,0))
            (quote (0)))
      (list (quote f32-dot-signed-zero-distinct)
            (eq? #f32(-0.0) #f32(0.0))
            (quote (0))))))

(def decimal-comma-authority-check
  (lambda (rows)
    (cond
      ((atom? rows) ()
       (quote (decimal-comma-authority-witness (status pass))))
      ((atom? rows) (0)
       (let ((row (car rows)))
         (cond
           ((equal? (second row) (third row)) (1)
            (decimal-comma-authority-check (cdr rows)))
           ((equal? (second row) (third row)) (0)
            (list
              (quote decimal-comma-authority-witness)
              (list (quote status) (quote fail))
              (list (quote case) (car row))
              (list (quote actual) (second row))
              (list (quote expected) (third row))))))))))

(def decimal-comma-authority-witness
  (lambda ()
    (decimal-comma-authority-check (decimal-comma-authority-rows))))
