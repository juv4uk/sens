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

; D9:000111111 CONTENT-STORE-PUT-WORLD — map-insert
(0011 вміст-сховище-покласти-світ мапа-вставити)
(0011 content-store-put-world вміст-сховище-покласти-світ)

; D9:010101110 DROP-UNSUPPORTED — keep only pairs whose cdr is D1:1
(0011 відкинути-непідтримані
  (0010 (список)
    (відсіяти
      (0010 (пара)
        (equal? (011 пара) (001 (1))))
      список)))
(0011 drop-unsupported відкинути-непідтримані)
