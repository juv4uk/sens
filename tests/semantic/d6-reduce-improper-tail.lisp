; D6:101110 REDUCE must not accept improper nonempty tails as NIL.
(згорнути (lambda (acc item) (cons item acc))
  (quote ()) (cons (quote а) (quote обірвано)))
