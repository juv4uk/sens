; core-math.lisp — мінімальний канон Core-Math.
;
; Core-Math = двійкові числа + доведені математичні закони.
;
; Канонічний семантичний шлях:
;
;   binary input(s)
;   + proved mathematical law
;   -> binary output
;
; Результат можна повторно подати на інший доведений закон.
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
; Важливий критерій для функцій-чисел:
;
;   E(semantic-operation(f,g))
;   =
;   binary-math(E(f), E(g))
;
; де обидві сторони визначені незалежно.
; Гарний бітовий візерунок без такого доказу не є законом.
;
; Людське подання може лишатися зручним:
;   раціонали, звичайні математичні записи, назви операцій.
; Але вони є лише проєкціями над канонічним двійковим представленням.
;
; Поки перший закон #2425 не доведено у цій простій формі,
; файл навмисно не містить executable definitions.
;
; Roadmap:
;   #2424  bits
;   #2425  laws
;   #2426  seeds
;   #2460  grow/reuse
;   #2485  execute: bits + law -> bits
