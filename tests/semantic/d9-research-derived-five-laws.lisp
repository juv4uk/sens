; D9 research harvest: five SENS-owned derived functions, eight D1 witnesses.
; Exact codes: 010010011 / 101000000 / 101111011 / 110001111 / 110011010.
; No local DEFINE: these laws must exercise lib/core4.lisp, not test stubs.
; The list-backed vector/arglist model is not D9 machine admission.
(list
  (equal? (вектор-з-список (list (quote а) (quote б)))
          (list (quote а) (quote б)))
  (порожнє? (вектор-з-список (quote ())))
  (equal? (аргументи (list (quote х) (quote у)))
          (list (quote х) (quote у)))
  (порожнє? (аргументи (quote ())))
  (equal? (числовий-буфер-довжина (list (quote а) (quote б)))
          #d24:000000000000000000000010)
  (equal? (числовий-буфер-довжина (quote ()))
          #d24:000000000000000000000000)
  (equal? (обґрунтування-від
            (quote ключ)
            (додати-обґрунтування
              (quote ключ) (list (quote доказ)) (quote ())))
          (list (list (quote доказ))))
  (порожнє? (обґрунтування-від
               (quote відсутній)
               (додати-обґрунтування
                 (quote ключ) (list (quote доказ)) (quote ())))))
