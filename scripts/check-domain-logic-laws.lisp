; Тест семанти й логіки двійковим сенсом.
; Семантику визначає сам SENS: закони доменів перевіряються бінарними кодами,
; а не зовнішнім інструментом. Базові закони D3 (пара), D4 (предикати) і D5
; (порядок і арифметика) у точних доменних адресах.
;
; Коди: 100=car 011=cdr 111=cons 010=atom? 101=eq? 001=quote 110=cond
;       0100=not?  01010=plus 11010=lessp? 11011=greaterp?  11011011=print
;
; Порівняння символів — eq? (101). Числа — лише через порядкові предикати
; lessp?/greaterp? (перевірено в lib/utf8.lisp): рівність 2+3==5 виражено як
; «не (2+3 < 5) і не (2+3 > 5)», тож жодного недоведеного порівняння чисел.
;
; Успіх -> друк PASS. Невдача -> навмисний незв'язаний символ
; domain-logic-law-fail, тож файловий режим CLI повертає ненульовий код.

(110
  ; D3: (car (cons (quote a) (quote b))) == (quote a)
  ((101 (100 (111 (001 a) (001 b))) (001 a))
   (110
     ; D3: (cdr (cons (quote a) (quote b))) == (quote b)
     ((101 (011 (111 (001 a) (001 b))) (001 b))
      (110
        ; D3: (atom? (quote a)) істинне
        ((010 (001 a))
         (110
           ; D3: (not? (atom? (cons a b))) істинне — пара не атом
           ((0100 (010 (111 (001 a) (001 b))))
            (110
              ; D3: (eq? (quote a) (quote a)) істинне
              ((101 (001 a) (001 a))
               (110
                 ; D3: (not? (eq? (quote a) (quote b))) істинне — різні символи
                 ((0100 (101 (001 a) (001 b)))
                  (110
                    ; D5: 2 < 3 істинне
                    ((11010 2 3)
                     (110
                       ; D5: 3 > 2 істинне
                       ((11011 3 2)
                        (110
                          ; D5: (not? (3 < 2)) істинне
                          ((0100 (11010 3 2))
                           (110
                             ; D5: (not? (2 > 3)) істинне
                             ((0100 (11011 2 3))
                              (110
                                ; D5: (not? (2+3 < 5)) -> 2+3 >= 5
                                ((0100 (11010 (01010 2 3) 5))
                                 (110
                                   ; D5: (not? (2+3 > 5)) -> 2+3 <= 5  => 2+3 == 5
                                   ((0100 (11011 (01010 2 3) 5))
                                    (11011011 "DOMAIN-LOGIC-LAWS: PASS d3-pair=4 d4-pred=2 d5-order=4 d5-sum=1"))
                                   (1 (domain-logic-law-fail plus-le))))
                                 (1 (domain-logic-law-fail plus-ge))))
                              (1 (domain-logic-law-fail greaterp-neg))))
                           (1 (domain-logic-law-fail lessp-neg))))
                        (1 (domain-logic-law-fail greaterp))))
                     (1 (domain-logic-law-fail lessp))))
                  (1 (domain-logic-law-fail eq-distinct))))
               (1 (domain-logic-law-fail eq-reflexive))))
            (1 (domain-logic-law-fail atom-on-cons))))
         (1 (domain-logic-law-fail atom-symbol))))
      (1 (domain-logic-law-fail cdr))))
  (1 (domain-logic-law-fail car)))
