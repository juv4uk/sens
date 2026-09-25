; #1391 — separation law between Core4 15-state answers and SENS functions.
;
; Logic answers:
;   0^n | 1^n | (), n=1..7
;
; SENS functions:
;   00000000..11111111
;
; These spaces are orthogonal. The grading path never turns a short answer
; into an 8-bit function and never turns an 8-bit function into ().

(core4-predicate-answer-boundary/3

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

  ((laws . boundary)
   (short-answer-to-sens-function . forbidden)
   (sens-function-to-answer . forbidden)
   (eighth-bit-in-grading . forbidden)
   (core1-core2-core3-impact . none)))
