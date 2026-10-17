; D9: десять законів справжніх resident-функцій lib/core4.lisp.
; ЖОДНОГО локального DEFINE: свідок не може підмінити виконавця.
; TMS-запис = (факт . підтримки); сховище = список (адреса значення).
(list
  (обґрунтований-член?
    (quote а)
    (list (створити-обґрунтований (quote а) (quote ()))))
  (not?
    (justified-member?
      (quote відсутній)
      (list (створити-обґрунтований (quote а) (quote ())))))
  (equal?
    (видалити-обґрунтований
      (quote а)
      (list (створити-обґрунтований (quote а) (quote ()))
            (створити-обґрунтований (quote б) (quote ()))
            (створити-обґрунтований (quote а) (quote ()))))
    (list (створити-обґрунтований (quote б) (quote ()))))
  (equal?
    (remove-justified
      (quote а)
      (list (створити-обґрунтований (quote а) (quote ()))))
    (quote ()))
  (equal?
    (додати-нові-обґрунтований
      (list (створити-обґрунтований (quote б) (quote ())))
      (list (створити-обґрунтований (quote а) (quote ()))))
    (list (створити-обґрунтований (quote б) (quote ()))
          (створити-обґрунтований (quote а) (quote ()))))
  (equal?
    (add-new-justified
      (quote ())
      (list (створити-обґрунтований (quote а) (quote ()))))
    (list (створити-обґрунтований (quote а) (quote ()))))
  (equal?
    (вміст-сховище-покласти-світ
      (quote ключ) (quote значення) (quote ()))
    (list (list (quote ключ) (quote значення))))
  (equal?
    (вміст-сховище-отримати
      (content-store-put-world
        (quote ключ) (quote нове)
        (вміст-сховище-покласти-світ
          (quote ключ) (quote старе) (quote ())))
      (quote ключ))
    (list (quote нове)))
  (equal?
    (відкинути-непідтримані
      (list
        (сполучити (quote так) (тотожне? (quote а) (quote а)))
        (сполучити (quote ні) (тотожне? (quote а) (quote б)))))
    (list (сполучити (quote так) (тотожне? (quote а) (quote а)))))
  (equal?
    (drop-unsupported
      (list (сполучити (quote ні) (тотожне? (quote а) (quote б)))))
    (quote ())))
