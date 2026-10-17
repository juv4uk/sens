; D9 JUSTIFIED-MEMBER? / REMOVE-JUSTIFIED / ADD-NEW-JUSTIFIED / PUT-WORLD
; Pure list/alist composition. Residency lib/domains/d9.lisp.

; D9:010011101 JUSTIFIED-MEMBER?
(0011 обґрунтований-член? значення-у-списку?)
(0011 justified-member? обґрунтований-член?)

; D9:010101001 REMOVE-JUSTIFIED — drop equal elements
(0011 видалити-обґрунтований
  (0010 (елемент список)
    (відсіяти
      (0010 (x) (not? (equal? x елемент)))
      список)))
(0011 remove-justified видалити-обґрунтований)

; D9:010010001 ADD-NEW-JUSTIFIED — append-new
(0011 додати-нові-обґрунтований додати-нові)
(0011 add-new-justified додати-нові-обґрунтований)

; D9:000111111 CONTENT-STORE-PUT-WORLD: ВИПРАВЛЕНИЙ КОНТРАКТ.
; Першоджерело lib/content-store.lisp:
;   (content-store-put-world store world)
;     = (внутрішня-мапа-вставити
;          (world-content-address world)
;          (world-address-content world)
;          store)
; Адресу з world обчислює сам закон. Не можна ототожнювати цю
; функцію з (мапа-вставити ключ значення мапа): відрізняються
; арність, адресація, тип вхідних даних та спостережувана поведінка.
; Не додавати хибне DEFINE до core4 чи дубль ратифікованого коду.
; Точні SENS-визначення та проєкції живуть у lib/content-store.lisp.

; D9:010101110 DROP-UNSUPPORTED — keep only pairs whose cdr is D1:1
(0011 відкинути-непідтримані
  (0010 (список)
    (відсіяти
      (0010 (пара)
        (equal? (011 пара) (001 (1))))
      список)))
(0011 drop-unsupported відкинути-непідтримані)
