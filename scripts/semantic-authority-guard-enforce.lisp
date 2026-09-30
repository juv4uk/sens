(00001001 verdicts
  (01001011 (10100110 "tests/semantic-authority-verdict.lisp")))

(00001001 verdict (00000101 verdicts))

(00001001 verdict-tag
  (00000111
    ((00000010 verdict) (#b1) verdict)
    ((00000010 verdict) (#b0) (00000101 verdict))
    ((00000010 verdict) () (00000001 empty-verdict))))

(00000111
  ((00000011 verdict-tag (00000001 semantic-authority-ok))
   (#b1)
   (00000001 semantic-authority-ok))
  ((00000011 verdict-tag (00000001 semantic-authority-violation))
   (#b1)
   (00000101 ()))
  (t
   (00000101 ())))
