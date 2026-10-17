; D10:0011001101 LAST1 and D10:0100001100 LISTP, PAIP/MAL research.
; Native SENS checks: list-shaped NIL/CONS, atom rejection, proper-list last.
; Expected D1 sequence (1 1 0 1 1 1 1 0); no D10 opcode admitted.
(list
  (список? (quote ()))
  (список? (list (quote яблуко)))
  (список? (quote яблуко))
  (список? (cons (quote яблуко) (quote груша)))
  (equal? (останній (list (quote яблуко) (quote груша)))
          (quote груша))
  (equal? (останній (list (quote яблуко))) (quote яблуко))
  (equal? (останній (list (quote яблуко) (list (quote груша))))
          (list (quote груша)))
  (equal? (останній (list (quote яблуко) (quote груша)))
          (quote яблуко)))
