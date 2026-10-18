; D9 research harvest: five SENS-owned derived functions, eight D1 witnesses.
; Exact codes: 010010011 / 101000000 / 101111011 / 110001111 / 110011010.
; No local DEFINE: these laws must exercise lib/core4.lisp, not test stubs.
; The list-backed vector/arglist model is not D9 machine admission.
(список
  (equal? (вектор-з-список (список (quote а) (quote б)))
          (список (quote а) (quote б)))
  (порожнє? (вектор-з-список (quote ())))
  (equal? (аргументи (список (quote х) (quote у)))
          (список (quote х) (quote у)))
  (порожнє? (аргументи (quote ())))
  (equal? (числовий-буфер-довжина (список (quote а) (quote б)))
          #d24:000000000000000000000010)
  (equal? (числовий-буфер-довжина (quote ()))
          #d24:000000000000000000000000)
  (equal? (обґрунтування-від
            (quote ключ)
            (додати-обґрунтування
              (quote ключ) (список (quote доказ)) (quote ())))
          (список (список (quote доказ))))
  (порожнє? (обґрунтування-від
               (quote відсутній)
               (додати-обґрунтування
                 (quote ключ) (список (quote доказ)) (quote ())))))

; opt-in повна укр-поверхня: exact identity = lib/domains/d*.lisp; DEFINE-аліас, без нової диспетчеризації.
(визначити список list)
