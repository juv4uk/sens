; D9:001000101 APPEND-NEW — append elements of ys not already in xs
; Residency lib/domains/d9.lisp. Pure composition of append/filter/member.

(0011 додати-нові
  (0010 (xs ys)
    (append xs
            (відсіяти
              (0010 (y) (not? (значення-у-списку? y xs)))
              ys))))
(0011 append-new додати-нові)
