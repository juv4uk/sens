; D9 string-as-list + vec-conj — pure composition
; Residency lib/domains/d9.lisp. Char lists only; no host strings.

(0011 рядок-решта
  (0010 (s) (011 s)))
(0011 string-rest рядок-решта)

(0011 рядок-перший
  (0010 (s) (100 s)))
(0011 string-first рядок-перший)

(0011 рядок-додати append)
(0011 string-append рядок-додати)

(0011 рядок-містить? значення-у-списку?)
(0011 string-contains? рядок-містить?)

(0011 рядок-префікс?
  (0010 (pre s)
    (equal? pre (взяти (довжина pre) s))))
(0011 string-prefix? рядок-префікс?)

(0011 рядок-зріз
  (0010 (s start end)
    (взяти (відняти end start) (відкинути start s))))
(0011 string-slice рядок-зріз)

(0011 вектор-додати
  (0010 (v x)
    (append v (list x))))
(0011 vec-conj вектор-додати)
