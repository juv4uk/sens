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
;
; /3 (2026-09-26, рішення власника в #1391): затверджено NOT/AND/OR/COND,
; носій відповіді — список двійкових бітів, проєкції atom?/eq? для Core4.
; Виконуваний свідок законів — experiments/core4-logic15-algebra.lisp.
; Runtime цей контракт ще не перемикає: atom?/eq? переходять окремим PR.

(core4-predicate-answer-scale/3

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
   (meaning-en . "unknown")
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
   ; Усі 15 відповідей лежать на одній лінії істинності:
   ;   0 < 00 < … < 0000000 < () < 1111111 < … < 11 < 1
   (truth-order . "0 < 00 < 000 < 0000 < 00000 < 000000 < 0000000 < () < 1111111 < 111111 < 11111 < 1111 < 111 < 11 < 1")
   ; AND — мінімум на лінії: «ні» перемагає; з двох «ні» — коротше
   ; (сильніше); з двох «так» — довше (слабше); () поглинає «так».
   (and-law . meet-on-truth-order)
   ; OR — максимум на лінії; дорівнює NOT(AND(NOT a, NOT b)) (де Морган).
   (or-law . join-on-truth-order)
   (de-morgan-law . or-is-not-of-and-of-nots)
   ; NOT дзеркально перевертає лінію; єдина нерухома точка — ().
   (not-order-law . order-reversing-involution)
   ; COND Core4: клауза (запит очікувана-відповідь вираз) обирається точним
   ; структурним збігом відповіді; жодного перетворення відповіді на істинність.
   (cond-law . exact-structural-match-of-answer)
   ; «Третього не дано» (a OR NOT a = 1) тримає лише на ступені 1: (0) і (1).
   (excluded-middle-law . grade-1-only)
   ; Зріз (0) () (1) — рівно сильна логіка Кліні K3.
   (kleene-k3-slice . ((0) () (1)))
   (and-or-cond-law . ratified-2026-09-26))

  ; Таблиця термінів: один санскритський термін на ступінь, спільний для
  ; напрямків «так» (1^n) і «ні» (0^n). Українська — первинна, англійська —
  ; допоміжна. Це назви ступенів, а не ймовірності: probability-model лишається forbidden.
  ((terminology . per-grade)
   (languages . (sanskrit uk en))
   (terms .
     ((1 dṛḍha-niścaya "тверда певність" "firm certainty")
      (2 niścaya       "певність"        "certainty")
      (3 nirṇaya       "висновок"        "determination")
      (4 saṃbhāvanā    "правдоподібність" "plausibility")
      (5 saṃśaya       "сумнів"          "doubt")
      (6 aniścaya      "непевність"      "uncertainty")
      (7 ajñāta-sīmā   "межа невідомого" "edge of the unknown")))
   (boundary-term . (ajñāta "невідомо" "unknown")))

  ; Носій відповіді: список двійкових бітів. Кожен біт — окремий токен 0 або 1,
  ; тому немає колізії reader-а ні з числами («00» читається як 0), ні з
  ; 8-бітними функціями СЕНС. Рядки рівнів вище — лише нотація.
  ((carrier . bit-list)
   (bits . (0 1))
   (yes-examples . ((1) (1 1) (1 1 1 1 1 1 1)))
   (no-examples . ((0) (0 0) (0 0 0 0 0 0 0)))
   (unknown . ())
   (max-width . 7)
   (spelling . notation-only)
   (short-bit-symbol-carrier . forbidden)
   (string-carrier . superseded-by-bit-list)
   (number-carrier . forbidden))

  ; Проєкції предикатів Core4 на шкалу. () стоїть вище розрізнення атом/пара,
  ; тому atom? на () відповідає () — «невідомо» (ajñāta).
  ((predicate-projection . core4)
   (atom? . (((structural-kind atom) (1)) ((structural-kind pair) (0)) ((structural-kind empty-list) ())))
   (eq? . (((identity-relation same) (1)) ((identity-relation distinct) (0))))
   (runtime-status . answer-functions-installed)
   (answer-functions .
     ((10110001 answer-not)
      (10110010 answer-and)
      (10110011 answer-or)
      (10110100 answer-weaken)
      (10110101 answer-atom)
      (10110110 answer-eq)))
   (record-predicates . unchanged-callers-migrate-by-file)
   (core1-core3-answer-domain . grade-1-only)
   (core1 . historical-unchanged-overlay-only)
   (core2 . frozen-compatibility)))
