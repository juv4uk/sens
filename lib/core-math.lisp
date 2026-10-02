; core-math.lisp — тимчасовий research carrier для окремої мови Core-Math.
;
; МЕЖА:
;   Core      = окрема Lisp-derived SENS lineage; ratified authority у lib/core.lisp.
;   Core-Math = окрема Lisp-independent mathematical-language lineage.
;
; Цей файл НЕ є другим runtime Core, Lisp-бібліотекою чи semantic authority.
; Це лише тимчасовий лабораторний носій, поки language-neutral semantics
; Core-Math виводяться та отримують власні executable witnesses.
;
; S-expression syntax, .lisp extension і current evaluator тут є mechanism only.
; Вони не дають Lisp/Core семантичної влади над Core-Math.
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
; Мінімальний шлях до Core-Math language law:
;
;   hypothesis
;     -> language-neutral object/law statement
;     -> executable witness
;     -> explicit falsifier
;     -> typed domain/codomain
;     -> anti-numerology / re-encoding check where applicable
;     -> second non-Lisp model/interpreter where required
;     -> Core-Math admission by its own law
;
; Міст до Core не є promotion path за замовчуванням.
; Якщо та сама структура окремо потрібна Core, це нове незалежне Core proof +
; owner-ratification. Core-Math може залишатись валідним без Core і без Lisp.
;
; Початковий scaffold навмисно не містить executable definitions.
; Це захищає межу: створення carrier-файлу не створює жодної нової семантики.
;
; Umbrella: #2411
; Language independence: #2424
; Core lineage boundary: #2423
; Ratified-domain architecture: #2410
; Function algebra: #2239
; Math free placement: #2248
; Coordination: #1599
