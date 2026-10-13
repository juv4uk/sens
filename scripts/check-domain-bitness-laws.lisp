; Тест бітності доменів двійковим сенсом.
; Закон: домен Dn має рівно 2^n рядків — ширина = ідентичність, кожен біт вартий.
; Семантику визначає сам SENS: таблиці читаються мовою (read-file/read-all),
; довжина рахується length, порівнюється eq?. Жодного зовнішнього інструмента.
;
; Коди: 100=car 011=cdr 001=quote 101=eq? 110=cond 0011=define 0010=lambda
;       000000=D6 length  110110111=read-file  110101001=read-all
;       11011011=D8 print
;
; Успіх -> друк PASS. Невдача -> названий, спостережуваний провал (аксіома S2):
; навмисний незв'язаний символ domain-bitness-fail -> ненульовий код виходу.

(0011 load-domain
  (0010 (path)
    (100 (110101001 (110110111 path)))))

(0011 table-rows
  (0010 (form)
    (011 form)))

(0011 bitness-check
  (0010 (name rows expected)
    (110
      ((101 (000000 rows) expected) (001 ()))
      (1 (domain-bitness-fail name)))))

(0011 d1 (load-domain "lib/domains/d1.lisp"))
(0011 d2 (load-domain "lib/domains/d2.lisp"))
(0011 d3 (load-domain "lib/domains/d3.lisp"))
(0011 d4 (load-domain "lib/domains/d4.lisp"))
(0011 d5 (load-domain "lib/domains/d5.lisp"))
(0011 d6 (load-domain "lib/domains/d6.lisp"))
(0011 d7 (load-domain "lib/domains/d7.lisp"))
(0011 d8 (load-domain "lib/domains/d8.lisp"))
(0011 d9 (load-domain "lib/domains/d9.lisp"))
(0011 d10 (load-domain "lib/domains/d10.lisp"))
(0011 d11 (load-domain "lib/domains/d11.lisp"))

(bitness-check (001 d1) (table-rows d1) 2)
(bitness-check (001 d2) (table-rows d2) 4)
(bitness-check (001 d3) (table-rows d3) 8)
(bitness-check (001 d4) (table-rows d4) 16)
(bitness-check (001 d5) (table-rows d5) 32)
(bitness-check (001 d6) (table-rows d6) 64)
(bitness-check (001 d7) (table-rows d7) 128)
(bitness-check (001 d8) (table-rows d8) 256)
(bitness-check (001 d9) (table-rows d9) 512)
(bitness-check (001 d10) (table-rows d10) 1024)
; D11 — словник тестів, sparse: рівно 43 зайнятих координати з 2048 (авторитет)
(bitness-check (001 d11) (table-rows d11) 43)

(11011011 "DOMAIN-BITNESS-LAWS: PASS d1..d10 = 2^n; d11 = 43 (sparse testing vocabulary)")
