; tests/fixtures/semantic/cond-2part-v1.lisp — #1709, закон #1713.
; УCondition допускаються лише 2-частинні клаузи (test expression):
;   test = 1       -> select; результат = значення виразу
;   test = 0       -> skip; перейти до наступної клаузи
;   усі skip       -> вичерпання, структурне ()
;   інша форма     -> не допускається (negative fixture)
;
; Важлива різниця після #3161: () не є значенням D1 і не дорівнює 0.
; Total predicates у цьому fixture дають лише D1 1/0. Явно partial predicate
; може окремо дати structural () як EMPTY/no-witness; canonical D3:011 тоді
; теж пропускає клаузу, не перетворюючи () на FALSE.
;
; COND admits only 2-part clauses (test expression):
;   test = D1:1 -> select; result is the expression value
;   test = D1:0 -> skip; explicit NO
;   test = ()   -> skip; EMPTY/no-witness (canonical #3161 path)
;   all skip    -> exhaustion, the structural value ()
;   other form  -> named failure
;
; This file still carries historical Function8/SID-shaped fixtures as
; compatibility evidence. Exact-domain D3:011 #3161 behavior is exercised by
; crates/sens/tests/empty_witness_law.rs and must not be inferred from these
; legacy bytes.

((expect . expect-value)
 (expr . "(00000111 ((00100010 1 1) 7))")
 (expected . (value 7))
 (active . t)
 (name . "COND: test 1 вибирає клаузу")
 (semantic-id . 00000111)
 (governs . "#1713")
 (note . "Точний біт 1 select -> значення виразу 7."))

((expect . expect-value)
 (expr . "(00000111 ((00100010 1 2) 7))")
 (expected . (value ()))
 (active . t)
 (name . "COND: test 0 пропускає, вичерпання дає структурне ()")
 (semantic-id . 00000111)
 (governs . "#1713")
 (note . "Точний D1:0 skip -> structural (), де () є exhaustion/EMPTY і не дорівнює PredicateBit 0."))

((expect . expect-value)
 (expr . "(00000111 ((00100010 1 2) 7) ((00100010 1 1) 9))")
 (expected . (value 9))
 (active . t)
 (name . "COND: skip 0 продовжує до наступної клаузи з 1")
 (semantic-id . 00000111)
 (governs . "#1713")
 (note . "0 пропускається, наступний 1 вибирає 9 — не перший ненулльовий."))

; Negative fixture. Тричастинна клауза (query expected-result expression) —
; спадоковий migration-форма, який #1713/#1714 мають прибрати з читача.
; Ряд НЕ активний: поки що рантайм приймає її як query і повертає
; UnsatisfiedConditional замість відхилення читачем.
; Negative fixture. A 3-part clause is a legacy migration form that
; #1713/#1714 must remove from the reader. Inactive: the runtime still
; accepts it as a query and fails with UnsatisfiedConditional instead of
; being rejected by the reader.
((expect . expect-rejected)
 (expr . "(00000111 (0 7 8))")
 (expected . (rejected "(00000111 (0 7 8))"))
 (active . ())
 (name . "COND: тричастинна клауза не допускається читачем")
 (semantic-id . 00000111)
 (governs . "#1713 #1714")
 (note . "Неактивний: main ще приймає 3-частинну форму. Порожній cond (InvalidForm) має нерatifікований закон — ряд свідомо не додано."))
