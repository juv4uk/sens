; D9 make/add/of/prune justified + vec-from-list + arglist + buffer-length + string-empty?
; Pure list composition. Residency lib/domains/d9.lisp.

; D9:001111010 MAKE-JUSTIFIED — (fact support)
(0011 створити-обґрунтований
  (0010 (факт підтримка)
    (111 факт (111 підтримка (001 ())))))
(0011 make-justified створити-обґрунтований)

; D9:010010011 JUSTIFICATIONS-OF → map-get
(0011 обґрунтування-від мапа-отримати)
(0011 justifications-of обґрунтування-від)

; D9:101000000 ADD-JUSTIFICATION → map-insert
(0011 додати-обґрунтування мапа-вставити)
(0011 add-justification додати-обґрунтування)

; D9:001110000 PRUNE-JUSTIFICATIONS — drop pairs with null support
(0011 обрізати-обґрунтування
  (0010 (список)
    (відсіяти
      (0010 (пара) (not? (0101 (011 пара))))
      список)))
(0011 prune-justifications обрізати-обґрунтування)

; D9:101111011 VEC-FROM-LIST
(0011 вектор-з-список
  (0010 (xs) xs))
(0011 vec-from-list вектор-з-список)

; D9:110001111 ARGLIST
(0011 аргументи
  (0010 (xs) xs))
(0011 arglist аргументи)

; D9:110011010 NUMERIC-BUFFER-LENGTH
(0011 числовий-буфер-довжина довжина)
(0011 numeric-buffer-length числовий-буфер-довжина)

; D9:110011100 STRING-EMPTY? — null list (char lists)
(0011 рядок-порожній?
  (0010 (s) (0101 s)))
(0011 string-empty? рядок-порожній?)
