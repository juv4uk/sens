; #1810 — спільний закон Д3:110, укр «за-умовою» (історичне COND).
;
; Українська операція не тлумачить довільні алгебри відповідей.
; Він споживає лише контекстне однобітне значення предиката:
;
;   1 -> вибрати та обчислити вираз
;   0 -> перейти до наступного варіанта
;
; Умовна гілка має рівно два поля:
;   умова, вираз — пояснювальні назви; поля даних нижче незмінні.
;
; Якщо варіанти вичерпано, результатом є структурне ().
; Це дані, а не логічна хиба предиката.

(control-dispatch-contract-2
  ((identity . (D3 "110"))
   (укр . за-умовою)
   (domain-owner . control)
   (canonical-clause-shape . (test expression))
   (test-domain . predicate-one-bit)
   (select-on . one)
   (skip-on . zero)
   (no-match . structural-empty)
   (three-part-clause . forbidden)
   (expected-result-field . forbidden)
   (explicit-result-equality . forbidden)
   (generic-truth-coercion . forbidden)
   (host-bool-coercion . forbidden)
   (empty-list-as-false . forbidden)
   (arbitrary-nonempty-as-true . forbidden)))