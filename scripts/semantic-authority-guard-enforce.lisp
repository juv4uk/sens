(0011 verdicts
  (110101001 (110110111 "tests/semantic-authority-verdict.lisp")))

(0011 verdict (100 verdicts))

(0011 verdict-tag
  (110
    ((010 verdict)
     (110
       ((101 verdict (001 ())) (001 empty-verdict))
       ((010 (001 ())) verdict)))
    ((010 (001 ())) (100 verdict))))

(110
  ((101 verdict-tag (001 semantic-authority-ok))
   (001 semantic-authority-ok))
  ((101 verdict-tag (001 semantic-authority-violation))
   (100 (001 ())))
  ((010 (001 ()))
   (100 (001 ()))))
