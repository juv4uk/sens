; D9:010010001 ADD-NEW-JUSTIFIED; D10:0000000001 RESULT-COUNT;
; D10:0001001001 FORALL-EVERY-CANDIDATE-SATISFIES.
; Eight independent exact D1 judgments, including negative falsifiers.
(list
  (equal? (кількість-результатів (quote ())) #d24:000000000000000000000000)
  (equal? (кількість-результатів (list (quote а) (quote б))) #d24:000000000000000000000010)
  (not? (equal? (кількість-результатів (list (quote а))) #d24:000000000000000000000010))
  (кожен-задовольняє?
    (0010 (значення) (equal? значення (quote а))) (list (quote а) (quote а)))
  (not? (кожен-задовольняє?
    (0010 (значення) (equal? значення (quote а))) (list (quote а) (quote б))))
  (кожен-задовольняє?
    (0010 (значення) (equal? значення (quote а))) (quote ()))
  (equal? (додати-нові-обґрунтований (list (quote а)) (list (quote б)))
          (list (quote а) (quote б)))
  (not? (equal? (додати-нові-обґрунтований (list (quote а)) (list (quote б)))
                (list (quote а)))))
