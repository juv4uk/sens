; D8 LSH / VALUES-LIST + D5 QUOTIENT uk surface + D6 COMPOSE/FLIP en aliases
; Residency lib/domains. Pure composition / alias only.

; D8:11100110 LSH — left shift = * 2^k (k≥0)
(0011 зсунути-вліво
  (0010 (n k)
    (110
      ((нуль? k) n)
      ((0100 (нуль? k))
       (помножити n (піднести-до-степеня #d24:000000000000000000000010 k))))))
(0011 lsh зсунути-вліво)

; D8:00100100 VALUES-LIST — list is already the value bundle in Core4
(0011 значення-списком
  (0010 (xs) xs))
(0011 values-list значення-списком)

; D5:10111 QUOTIENT uk surface (body already quotient)
(0011 частка quotient)

; D6 COMPOSE/FLIP en aliases (bodies already скласти-функції / поміняти-аргументи)
(0011 compose скласти-функції)
(0011 flip поміняти-аргументи)
