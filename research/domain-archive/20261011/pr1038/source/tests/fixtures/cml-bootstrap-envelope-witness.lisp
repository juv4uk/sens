(def cml-bootstrap-envelope-witness
  (lambda ()
    (list
      (cml-bootstrap-frontend (quote (+ 1 2)))
      (cml-bootstrap-frontend (quote (* 1 2)))
      (cml-bootstrap-frontend (quote (+ 1)))
      (cml-bootstrap-frontend (quote ())))))
