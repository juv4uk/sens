; D9: десять законів справжніх resident-функцій lib/core4.lisp.
; Жодного локального DEFINE: нативний SENS перевіряє виробничі визначення.
; TMS-запис = (факт . підтримки). CONTENT-STORE-PUT-WORLD має інший
; двоаргументний контракт у lib/content-store.lisp — не підміняємо його мапою.
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
    (додати-нові-обґрунтований
      (list (створити-обґрунтований (quote а) (quote ())))
      (list (створити-обґрунтований (quote а) (quote ()))))
    (list (створити-обґрунтований (quote а) (quote ()))))
  (not? (обґрунтований-член? (quote а) (quote ())))
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
