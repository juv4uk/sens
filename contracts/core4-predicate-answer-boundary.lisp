; #1391 — закон розмежування п'ятнадцяти станів відповіді Core4
; та функцій мови СЕНС.
;
; Логічні відповіді:
;   0^n | 1^n | (), n=1..7
;
; Чинні функції СЕНС: точні D1–D10 та повна «укр»-проєкція.
; Вісім бітів історичного SID8 не визначають D8 чи механізм виконання.
;
; Шкала Core4 — історичне свідчення; її бітові ступені не є D1-предикатами.
; Історичні байтові адреси не можна прирівнювати до сучасних D8-координат.
; Право виклику встановлюють окремі закони та механізми SENS.

(core4-predicate-answer-boundary-4

  ((profile . core4)
   (scope . predicate-answer-space)
   (answer-scale . "contracts/core4-predicate-answer-scale.lisp")
   (answer-count . 15)
   (historical-flat-count . 256)
   (current-function-space . exact-domain-ladder-d1-d10)
   (current-call-surface . укр)
   (spaces . orthogonal))

  ((no-path . ("0" "00" "000" "0000" "00000" "000000" "0000000"))
   (converges-to . ()))

  ((yes-path . ("1" "11" "111" "1111" "11111" "111111" "1111111"))
   (converges-to . ()))

  ((undirected-answer . ())
   (sanskrit . ajñāta)
   (direction . none))

  ; Історичний приклад збіжності не встановлює сучасного закону D8.
  ((function-convergence . historical-only)
   (function-identities . exact-domain-and-bits)
   (result-value . not-inferred-from-retired-byte)
   (current-d8-example . (д8 10110001 текст-передує?))
   (current-callability . requires-proved-law-and-mechanism))

  ((laws . boundary)
   (short-answer-to-sens-function . forbidden)
   (sens-function-to-answer . forbidden)
   (eighth-bit-in-grading . forbidden)
   (legacy-byte-as-d8 . forbidden)
   (historical-answer-as-d1 . forbidden)
   (core1-core2-core3-impact . none)))
