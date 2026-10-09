; core-math.lisp — мінімальний канон Core-Math.
;
; Спільна онтологія з Core: #2490.
;
;   semantic object
;   = binary number
;   + explicit domain
;   + proved law
;
; Для Core-Math:
;
;   binary input(s)
;   + proved mathematical law in that domain
;   -> binary output
;
; Результат можна повторно подати на інший доведений закон.
;
; Однакові біти в різних доменах НЕ означають однакову семантику.
; Людські назви функцій/операцій — лише проєкції.
;
; Core і Core-Math можуть зараз розходитись.
; Це нормально.
;
; Бажаний напрям:
;   divergence where evidence differs
;   complementarity where a bridge law is independently proved
;   possible convergence only when both sides force the same
;   binary object + domain + semantic law + mathematical law (#2495).
;
; НЕ є семантикою Core-Math:
;   Lisp / core.lisp
;   S-expression
;   JSON / AST
;   SHA / hash identity
;   registry rows
;   cache
;   human function names
;   proof/certificate file format
;
; Усе це може бути лише лабораторним інструментом.
;
; Критерій для функцій-чисел:
;
;   E(semantic-operation(f,g))
;   =
;   binary-math(E(f), E(g))
;
; де обидві сторони визначені незалежно.
; Гарний бітовий візерунок без такого доказу не є законом.
;
; Поки перший закон #2425 не доведено у цій простій формі,
; файл навмисно не містить executable definitions.
;
; Roadmap:
;   #2424  bits/domains
;   #2425  laws
;   #2426  seeds
;   #2460  grow/reuse
;   #2485  execute: bits + law -> bits
;   #2495  optional convergence research
