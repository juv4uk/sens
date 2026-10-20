; #1391 — закон розмежування п'ятнадцяти станів відповіді Core4
; та функцій мови СЕНС.
;
; Логічні відповіді:
;   0^n | 1^n | (), n=1..7
;
; Функції СЕНС:
;   00000000..11111111
;
; Ці простори незалежні. Перетворення ступеня логічної відповіді
; не створює восьмибітної функції СЕНС. Так само восьмибітний
; код функції не може неявно перетворитися на порожню структуру.

(core4-predicate-answer-boundary/4

  ((profile . core4)
   (scope . predicate-answer-space)
   (answer-scale . "contracts/core4-predicate-answer-scale.lisp")
   (answer-count . 15)
   (sens-function-count . 256)
   (spaces . orthogonal))

  ((no-path . ("0" "00" "000" "0000" "00000" "000000" "0000000"))
   (converges-to . ()))

  ((yes-path . ("1" "11" "111" "1111" "11111" "111111" "1111111"))
   (converges-to . ()))

  ((undirected-answer . ())
   (sanskrit . ajñāta)
   (direction . none))

  ((function-convergence .
     ((00000000 ())
      (11111111 ())))
   (function-identities . distinct)
   (result-value . one-empty-list))

  ((laws . boundary)
   (short-answer-to-sens-function . forbidden)
   (sens-function-to-answer . forbidden)
   (eighth-bit-in-grading . forbidden)
   (core1-core2-core3-impact . none)))
