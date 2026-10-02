; core-math.lisp — дослідницьке математичне ядро SENS.
;
; ВЛАДА:
;   lib/core.lisp      = лише ратифіковані домени та закони.
;   lib/core-math.lisp = лабораторія математичних гіпотез і доказів.
;
; Цей файл НЕ є другим runtime Core і НЕ може сам ратифікувати семантику.
; Жодна математична операція, закон, координата або function identity
; не переходить звідси до lib/core.lisp без окремої owner-ratification.
;
; Поточні напрями дослідження:
;
;   1. Математика над значеннями/примітивами:
;      ADD / NEG / SUB
;      MUL / RECIP / DIV
;      порядок і порівняння
;      GCD / LCM / QUOTIENT / REMAINDER
;      NUMERATOR / DENOMINATOR / NORMALIZE
;      exact / approximate / interval / symbolic provenance
;
;   2. Математика над функціями як семантичними об'єктами:
;      composition
;      partial composition
;      roots + generator laws
;      homomorphisms
;      closure / identity / inverse лише там, де це доведено
;      generated functions + irreducible residue
;
;   3. D7 research:
;      sound + number questions.
;      Sound і Number не ототожнюються лише через спільну ширину/біти.
;      Точний закон D7 має бути виведений окремо.
;
; Статуси дослідницького твердження:
;   HYPOTHESIS
;   WITNESSED
;   FALSIFIED
;   PROVED-BOUNDED
;   RATIFICATION-CANDIDATE
;
; Мінімальний шлях до Core:
;
;   hypothesis
;     -> executable law
;     -> explicit falsifier
;     -> typed domain/codomain
;     -> anti-numerology / re-encoding check where applicable
;     -> mechanism/benchmark evidence where relevant
;     -> owner ratification
;     -> lib/core.lisp
;
; Початковий scaffold навмисно не містить executable definitions.
; Це захищає межу: створення core-math не створює жодної нової семантики.
;
; Umbrella: #2411
; Ratified-domain architecture: #2410
; Function algebra: #2239
; Math free placement: #2248
; Coordination: #1599
