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
  (функція (name sections)
    (за-умовою
      ((атом? sections) (як-є ()))
      ((тотожне? (перше (перше sections)) name) (перше sections))
      ((атом? (як-є ()))
       (механізм-знайти-секцію name (решта sections))))))

(визначити mechanism-selector-routes
  (решта (механізм-знайти-секцію
         (як-є rows)
         mechanism-selector-metadata)))

(визначити реєстр-містить-ідентичність?
  (функція (sid rows)
    (за-умовою
      ((атом? rows) (як-є no))
      ((тотожне? sid (перше (перше rows))) (як-є yes))
      ((атом? (як-є ()))
       (реєстр-містить-ідентичність? sid (решта rows))))))

(визначити механізм-знайти-маршрут
  (функція (sid executor rows)
    (за-умовою
      ((атом? rows) (як-є ()))
      ((атом? (як-є ()))
       ((функція (row)
          (за-умовою
            ((тотожне? sid (перше row))
             (за-умовою
               ((тотожне? executor (друге row)) row)
               ((атом? (як-є ()))
                (механізм-знайти-маршрут sid executor (решта rows)))))
            ((атом? (як-є ()))
             (механізм-знайти-маршрут sid executor (решта rows)))))
        (перше rows))))))

(визначити вибрати-механізм
  (функція (sid executor)
    (за-умовою
      ((тотожне?
         (реєстр-містить-ідентичність?
           sid mechanism-selector-registry-rows)
         (як-є no))
       (список
         (як-є mechanism-selection-failure)
         (як-є sid-not-in-function-table)
         sid))
      ((атом? (як-є ()))
       ((функція (route)
          (за-умовою
            ((атом? route)
             (список (як-є mechanism-unavailable) sid executor))
            ((атом? (як-є ()))
             (список (як-є mechanism-selected)
               sid executor (третє route)))))
        (механізм-знайти-маршрут
          sid executor mechanism-selector-routes))))))


; Сумісні англомовні назви залишаються псевдонімами тих самих Lisp-значень.
(визначити mechanism-selector-find-section механізм-знайти-секцію)
(визначити mechanism-selector-registry-has-sid? реєстр-містить-ідентичність?)
(визначити mechanism-selector-find-route механізм-знайти-маршрут)
(визначити mechanism-select вибрати-механізм)
