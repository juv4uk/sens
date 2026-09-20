(def verdicts
  (read-all (read-file "tests/semantic-authority-verdict.lisp")))

(def verdict (car verdicts))
(def verdict-tag (car verdict))

(cond
  ((eq verdict-tag (quote semantic-authority-ok))
   (identity-relation same)
   (quote semantic-authority-ok))
  ((eq verdict-tag (quote semantic-authority-ok))
   (identity-relation distinct)
   (car ())))