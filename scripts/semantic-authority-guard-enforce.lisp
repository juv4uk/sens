(def verdicts
  (read-all (read-file "tests/semantic-authority-verdict.lisp")))

(def verdict (car verdicts))

(def verdict-tag
  (cond
    ((atom? verdict) (1) verdict)
    ((atom? verdict) (0) (car verdict))
    ((atom? verdict) () (quote empty-verdict))))

(cond
  ((eq? verdict-tag (quote semantic-authority-ok))
   (1)
   (quote semantic-authority-ok))
  ((eq? verdict-tag (quote semantic-authority-violation))
   (1)
   (car ()))
  (t
   (car ())))
