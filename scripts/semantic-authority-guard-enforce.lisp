(def verdicts
  (read-all (read-file "tests/semantic-authority-verdict.lisp")))

(def verdict (car verdicts))

(def verdict-tag
  (cond
    ((atom verdict) (structural-kind atom) verdict)
    ((atom verdict) (structural-kind pair) (car verdict))
    ((atom verdict) (structural-kind empty-list) (quote empty-verdict))))

(cond
  ((eq verdict-tag (quote semantic-authority-ok))
   (identity-relation same)
   (quote semantic-authority-ok))
  ((eq verdict-tag (quote semantic-authority-violation))
   (identity-relation same)
   (car ()))
  (t
   (car ())))
