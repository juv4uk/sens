; #1047 — mechanism selection after Canon()/function-table identity resolution.
; Exact parent: #1046 function-table mechanism authority.
; This file never decides what a SID means. It only selects among executor
; routes already admitted by transitional #1046 mechanism metadata.
;
; Migrated: duplicate mutually-exclusive EQ arms removed; NOT(ATOM) guard
; replaced by exact two-field D3 COND + D1 ATOM for empty. Fallback uses
; (010 (001 ())) = D1:1. Width is identity; every bit of domain address valued.

(визначити mechanism-selector-registry
  (перше (читати-всі (читати-файл "lib/surface/semantic-registry.lisp"))))

(визначити mechanism-selector-metadata
  (перше (читати-всі (читати-файл "lib/function-table-mechanisms.lisp"))))

(визначити mechanism-selector-registry-rows
  mechanism-selector-registry)

(визначити механізм-знайти-секцію
  (функція (назва секції)
    (за-умовою
      ((атом? секції) (як-є ()))
      ((тотожне? (перше (перше секції)) назва) (перше секції))
      ((атом? (як-є ()))
       (механізм-знайти-секцію назва (решта секції))))))

(визначити mechanism-selector-routes
  (решта (механізм-знайти-секцію
         (як-є rows)
         mechanism-selector-metadata)))

(визначити реєстр-містить-ідентичність?
  (функція (ідентичність рядки)
    (за-умовою
      ((атом? рядки) (як-є no))
      ((тотожне? ідентичність (перше (перше рядки))) (як-є yes))
      ((атом? (як-є ()))
       (реєстр-містить-ідентичність? ідентичність (решта рядки))))))

(визначити механізм-знайти-маршрут
  (функція (ідентичність виконавець рядки)
    (за-умовою
      ((атом? рядки) (як-є ()))
      ((атом? (як-є ()))
       ((функція (рядок)
          (за-умовою
            ((тотожне? ідентичність (перше рядок))
             (за-умовою
               ((тотожне? виконавець (друге рядок)) рядок)
               ((атом? (як-є ()))
                (механізм-знайти-маршрут ідентичність виконавець (решта рядки)))))
            ((атом? (як-є ()))
             (механізм-знайти-маршрут ідентичність виконавець (решта рядки)))))
        (перше рядки))))))

(визначити вибрати-механізм
  (функція (ідентичність виконавець)
    (за-умовою
      ((тотожне?
         (реєстр-містить-ідентичність?
           ідентичність mechanism-selector-registry-rows)
         (як-є no))
       (список
         (як-є mechanism-selection-failure)
         (як-є sid-not-in-function-table)
         ідентичність))
      ((атом? (як-є ()))
       ((функція (маршрут)
          (за-умовою
            ((атом? маршрут)
             (список (як-є mechanism-unavailable) ідентичність виконавець))
            ((атом? (як-є ()))
             (список (як-є mechanism-selected)
               ідентичність виконавець (третє маршрут)))))
        (механізм-знайти-маршрут
          ідентичність виконавець mechanism-selector-routes))))))


; Сумісні англомовні назви залишаються псевдонімами тих самих Lisp-значень.
(визначити mechanism-selector-find-section механізм-знайти-секцію)
(визначити mechanism-selector-registry-has-sid? реєстр-містить-ідентичність?)
(визначити mechanism-selector-find-route механізм-знайти-маршрут)
(визначити mechanism-select вибрати-механізм)
