; Core4 15-state predicate-answer scale — Lisp-owned law for #1391.
;
; Two orthogonal spaces:
;   logic answers: 0^n | 1^n | (), n=1..7
;   SENS functions: 00000000..11111111
;
; The grading path never enters the 8-bit SENS function space.
; More repeated bits mean less determination and convergence toward ().
;
; Sanskrit labels are SENS/Core4 terminology anchors, not a claim that
; historical Nyāya defined this exact 15-state scale.

(core4-predicate-answer-scale/2

  ((identity . predicate-answer-domain)
   (profile . core4)
   (answer-grammar . "0^n | 1^n | (), n=1..7")
   (answer-count . 15)
   (semantic-form . homogeneous-bits)
   (sens-function-space . separate-00000000-through-11111111)
   (probability-model . forbidden)
   (confidence-score . forbidden)
   (record-wrapper . forbidden))

  ((direction . no)
   (bit . "0")
   (levels .
     (("0"       1 dṛḍha-niścaya)
      ("00"      2 niścaya)
      ("000"     3 nirṇaya)
      ("0000"    4 saṃbhāvanā)
      ("00000"   5 saṃśaya)
      ("000000"  6 aniścaya)
      ("0000000" 7 ajñāta-sīmā))))

  ((boundary . ())
   (sanskrit . ajñāta)
   (meaning-uk . "невідомо")
   (direction . none)
   (sens-function . none)
   (convergence-functions . (00000000 11111111))
   (function-result . ()))

  ((direction . yes)
   (bit . "1")
   (levels .
     (("1"       1 dṛḍha-niścaya)
      ("11"      2 niścaya)
      ("111"     3 nirṇaya)
      ("1111"    4 saṃbhāvanā)
      ("11111"   5 saṃśaya)
      ("111111"  6 aniścaya)
      ("1111111" 7 ajñāta-sīmā))))

  ((algebra . minimal)
   (not-law . same-width-bit-inversion)
   (weakening-law . append-same-bit)
   (boundary-law . seven-directed-grades-converge-to-empty-list)
   (eighth-bit-law . belongs-to-sens-function-space)
   (function-convergence-law . distinct-functions-same-empty-result)
   (and-or-cond-law . deliberately-unratified)))
