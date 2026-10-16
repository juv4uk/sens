; D8:11011010 NTHCDR та D8:11100100 EVERY — нижчодоменні похідні.
; Чотири позитивні нативні D1-свідки, без прямого D8 виклику.
(list
  (equal?
    (n-та-решта #d24:000000000000000000000001
      (list (quote а) (quote б) (quote в)))
    (list (quote б) (quote в)))
  (null?
    (n-та-решта #d24:000000000000000000000100
      (list (quote а) (quote б))))
  (усі-задовольняють?
    (lambda (x) (equal? x (quote так)))
    (list (quote так) (quote так)))
  (not?
    (усі-задовольняють?
      (lambda (x) (equal? x (quote так)))
      (list (quote так) (quote ні)))))
