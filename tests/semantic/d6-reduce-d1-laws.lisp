; D6:101110 REDUCE: real SENS D1 self-verdicts for nonempty/empty folds.
; Positive controls fail if REDUCE silently drops either head or tail.
(list
  (equal?
    (згорнути (lambda (acc item) (cons item acc))
      (quote ()) (list (quote а) (quote б) (quote в)))
    (list (quote в) (quote б) (quote а)))
  (equal?
    (reduce (lambda (acc item) (cons item acc))
      (quote ()) (list (quote а) (quote б)))
    (list (quote б) (quote а)))
  (equal?
    (згорнути (lambda (acc item) (cons item acc))
      (quote а) (quote ()))
    (quote а)))
