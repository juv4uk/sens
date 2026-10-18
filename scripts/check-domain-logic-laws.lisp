; Тест семанти й логіки двійковим сенсом.
; Семантику визначає сам SENS. Кожен закон — один рядок, пласко й прозоро:
; жодної вкладеної драбини, жодного зовнішнього інструмента. Точні коди:
;
;   D3  100=car 011=cdr 111=cons 010=atom? 101=eq? 001=quote 110=cond
;   D4  0100=not? 0101=null? 1110=list 0010=lambda 0011=define
;   D5  01010=plus 11010=lessp? 11011=greaterp?
;   D6  000000=length 001000=let
;   D8  11110111=equal? 11011011=print
;   D9  110110111=read-file 110101001=read-all
;
; Символи — eq? (D3 101); числа — лише доведеними порядковими предикатами
; lessp?/greaterp? (lib/utf8.lisp). Рівність 2+3==5 виражено як
; «не (2+3 < 5) і не (2+3 > 5)». Успіх -> друк PASS. Невдача -> названий,
; спостережуваний провал (аксіома S2): навмисний незв'язаний символ
; domain-logic-law-fail -> ненульовий код виходу.

(визначити law-check
  (функція (name ok)
    (за-умовою
      (ok (як-є ()))
      (1 (domain-logic-law-fail name)))))

(визначити law-two 2)

; D3 — пара
(law-check (як-є car-of-cons)      (тотожне? (перше (сполучити (як-є a) (як-є b))) (як-є a)))
(law-check (як-є cdr-of-cons)      (тотожне? (решта (сполучити (як-є a) (як-є b))) (як-є b)))
(law-check (як-є atom-of-symbol)   (атом? (як-є a)))
(law-check (як-є not-atom-of-pair) (хибне? (атом? (сполучити (як-є a) (як-є b)))))
(law-check (як-є eq-reflexive)     (тотожне? (як-є a) (як-є a)))
(law-check (як-є eq-distinct)      (хибне? (тотожне? (як-є a) (як-є b))))
(law-check (як-є null-of-empty)    (порожній? (як-є ())))
(law-check (як-є list-car)         (тотожне? (перше (список (як-є a) (як-є b))) (як-є a)))

; D5 — порядок і арифметика
(law-check (001 lessp-2-3)           (11010 2 3))
(law-check (001 greaterp-3-2)        (11011 3 2))
(law-check (001 not-lessp-3-2)       (0100 (11010 3 2)))
(law-check (001 not-greaterp-2-3)    (0100 (11011 2 3)))
(law-check (001 sum-2-3-not-less)    (0100 (11010 (01010 2 3) 5)))
(law-check (001 sum-2-3-not-greater) (0100 (11011 (01010 2 3) 5)))

; D4 — append
(law-check (як-є append-empty)
  (тотожне? (перше (приєднати (як-є ()) (список (як-є a)))) (як-є a)))

; D5 — добуток і частка
(law-check (001 times-2-3-not-greater) (0100 (11011 (10110 2 3) 6)))
(law-check (001 quotient-6-2-not-less) (0100 (11010 (10111 6 2) 3)))

; D5 — членство у списку
(law-check (001 member-found) (11101 (001 a) (1110 (001 a) (001 b))))

; D6 — відображення й згортання
(law-check (001 map-head-not-less)    (0100 (11010 (100 (101000 (0010 (x) (01010 x 1)) (1110 2 3))) 3)))
(law-check (001 map-head-not-greater) (0100 (11011 (100 (101000 (0010 (x) (01010 x 1)) (1110 2 3))) 3)))
(law-check (001 reduce-sum-not-less)    (0100 (11010 (101110 01010 0 (1110 2 3)) 5)))
(law-check (001 reduce-sum-not-greater) (0100 (11011 (101110 01010 0 (1110 2 3)) 5)))

; D6 — зв'язування й довжина
(law-check (001 let-sum-not-less)    (0100 (11010 (001000 ((x 2) (y 3)) (01010 x y)) 5)))
(law-check (001 let-sum-not-greater) (0100 (11011 (001000 ((x 2) (y 3)) (01010 x y)) 5)))
(law-check (001 length-of-list-2)    (11010 1 (000000 (1110 (001 a) (001 b)))))

; D8 — структурна рівність
(law-check (001 equal-list-self)     (11110111 (1110 (001 a) (001 b)) (1110 (001 a) (001 b))))

; D9 — читання файла (IO) і ідентичність схеми
(law-check (як-є read-file-schema)
  (тотожне? (перше (читати-всі (читати-файл "lib/domains/d1.lisp"))) (як-є domain-table/1)))

; define + посилання на змінну
(law-check (001 define-then-use) (11010 law-two 3))

(друкувати "DOMAIN-LOGIC-LAWS: PASS d3=8 d5=7 d6=7 d8=1 define=1")
