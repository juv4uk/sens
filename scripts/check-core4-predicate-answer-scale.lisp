; #1391 — executable witness for the Core4 15-state answer scale.

(00001001 pas-contract
  (00000101 (01001011 (10100110 "contracts/core4-predicate-answer-scale.lisp"))))
(00001001 pas-schema (00000101 pas-contract))
(00001001 pas-sections (00000110 pas-contract))

(00001001 pas-field
  (00001000 (section name)
    (00000110 (00101101 name section))))

(00001001 pas-meta (00000101 pas-sections))
(00001001 pas-no (00101111 pas-sections))
(00001001 pas-boundary (00110000 pas-sections))
(00001001 pas-yes (00110001 pas-sections))
(00001001 pas-algebra (00110010 pas-sections))

(00001001 pas-terminology (00101011 5 pas-sections))
(00001001 pas-carrier (00101011 6 pas-sections))
(00001001 pas-predicates (00101011 7 pas-sections))

; Таблиця функцій: рядок (код (en ім'я) (ук …) …).
(00001001 pas-registry
  (00000101 (01001011 (10100110 "lib/surface/semantic-registry.lisp"))))

; (код ім'я) з контракту -> (код ім'я-з-таблиці-функцій).
(00001001 pas-registry-row
  (00001000 (entry)
    (00100111 (00000101 entry)
          (00101111 (00101101 (00000001 en) (00000110 (00101101 (00000101 entry) pas-registry)))))))

(00001001 pas-no-levels (pas-field pas-no (00000001 levels)))
(00001001 pas-yes-levels (pas-field pas-yes (00000001 levels)))
(00001001 pas-terms (pas-field pas-terminology (00000001 terms)))

; Рядок рівня: (бітовий-запис ступінь санскрит) -> (ступінь санскрит).
(00001001 pas-grade-and-sanskrit
  (00001000 (level) (00000110 level)))

; Рядок термінів: (ступінь санскрит uk en) -> (ступінь санскрит).
(00001001 pas-term-grade-and-sanskrit
  (00001000 (term) (00100111 (00000101 term) (00101111 term))))

(00001001 pas-observed
  (00100111
    pas-schema
    (pas-field pas-meta (00000001 answer-count))
    (pas-field pas-meta (00000001 answer-grammar))
    (pas-field pas-meta (00000001 sens-function-space))
    pas-no-levels
    (pas-field pas-boundary (00000001 boundary))
    (pas-field pas-boundary (00000001 sanskrit))
    (pas-field pas-boundary (00000001 direction))
    (pas-field pas-boundary (00000001 sens-function))
    (pas-field pas-boundary (00000001 convergence-functions))
    (pas-field pas-boundary (00000001 function-result))
    pas-yes-levels
    (00001100 (00101000 pas-no-levels) (00101000 pas-yes-levels) 1)
    (pas-field pas-algebra (00000001 not-law))
    (pas-field pas-algebra (00000001 weakening-law))
    (pas-field pas-algebra (00000001 boundary-law))
    (pas-field pas-algebra (00000001 eighth-bit-law))
    (pas-field pas-algebra (00000001 function-convergence-law))
    (pas-field pas-boundary (00000001 meaning-uk))
    (pas-field pas-boundary (00000001 meaning-en))
    (pas-field pas-terminology (00000001 languages))
    pas-terms
    (00100010 (00110111 pas-term-grade-and-sanskrit pas-terms)
            (00110111 pas-grade-and-sanskrit pas-no-levels))
    (00100010 (00110111 pas-term-grade-and-sanskrit pas-terms)
            (00110111 pas-grade-and-sanskrit pas-yes-levels))
    (pas-field pas-terminology (00000001 boundary-term))
    (pas-field pas-algebra (00000001 truth-order))
    (pas-field pas-algebra (00000001 and-law))
    (pas-field pas-algebra (00000001 or-law))
    (pas-field pas-algebra (00000001 de-morgan-law))
    (pas-field pas-algebra (00000001 not-order-law))
    (pas-field pas-algebra (00000001 cond-law))
    (pas-field pas-algebra (00000001 excluded-middle-law))
    (pas-field pas-algebra (00000001 kleene-k3-slice))
    (pas-field pas-algebra (00000001 and-or-cond-law))
    pas-carrier
    pas-predicates
    (00101000 pas-sections)
    (00100010 (00110111 pas-registry-row (pas-field pas-predicates (00000001 answer-functions)))
            (pas-field pas-predicates (00000001 answer-functions)))
    ; Runtime відповідає рівно так, як записано в проєкціях контракту.
    (00100010 (00100111 (10110101 (00000001 x)) (10110101 (00000001 (a))) (10110101 (00000001 ())))
            (00110111 second (pas-field pas-predicates (00000001 atom?))))
    (00100010 (00100111 (10110110 (00000001 a) (00000001 a)) (10110110 (00000001 a) (00000001 b)))
            (00110111 second (pas-field pas-predicates (00000001 eq?))))
    ; Самі примітиви мови відповідають тією ж шкалою.
    (00100010 (00100111 (00000010 (00000001 x)) (00000010 (00000001 (a))) (00000010 (00000001 ())))
            (00110111 second (pas-field pas-predicates (00000001 atom?))))
    (00100010 (00100111 (00000011 (00000001 a) (00000001 a)) (00000011 (00000001 a) (00000001 b)))
            (00110111 second (pas-field pas-predicates (00000001 eq?))))))

(00001001 pas-expected
  (00100111
    (00000001 core4-predicate-answer-scale/3)
    15
    "0^n | 1^n | (), n=1..7"
    (00000001 separate-00000000-through-11111111)
    (00000001
      (("0"       1 dṛḍha-niścaya)
       ("00"      2 niścaya)
       ("000"     3 nirṇaya)
       ("0000"    4 saṃbhāvanā)
       ("00000"   5 saṃśaya)
       ("000000"  6 aniścaya)
       ("0000000" 7 ajñāta-sīmā)))
    (00000001 ())
    (00000001 ajñāta)
    (00000001 none)
    (00000001 none)
    (00000001 (00000000 11111111))
    (00000001 ())
    (00000001
      (("1"       1 dṛḍha-niścaya)
       ("11"      2 niścaya)
       ("111"     3 nirṇaya)
       ("1111"    4 saṃbhāvanā)
       ("11111"   5 saṃśaya)
       ("111111"  6 aniścaya)
       ("1111111" 7 ajñāta-sīmā)))
    15
    (00000001 same-width-bit-inversion)
    (00000001 append-same-bit)
    (00000001 seven-directed-grades-converge-to-empty-list)
    (00000001 belongs-to-sens-function-space)
    (00000001 distinct-functions-same-empty-result)
    "невідомо"
    "unknown"
    (00000001 (sanskrit uk en))
    (00000001
      ((1 dṛḍha-niścaya "тверда певність" "firm certainty")
       (2 niścaya       "певність"        "certainty")
       (3 nirṇaya       "висновок"        "determination")
       (4 saṃbhāvanā    "правдоподібність" "plausibility")
       (5 saṃśaya       "сумнів"          "doubt")
       (6 aniścaya      "непевність"      "uncertainty")
       (7 ajñāta-sīmā   "межа невідомого" "edge of the unknown")))
    (00000001 (1))
    (00000001 (1))
    (00000001 (ajñāta "невідомо" "unknown"))
    "0 < 00 < 000 < 0000 < 00000 < 000000 < 0000000 < () < 1111111 < 111111 < 11111 < 1111 < 111 < 11 < 1"
    (00000001 meet-on-truth-order)
    (00000001 join-on-truth-order)
    (00000001 or-is-not-of-and-of-nots)
    (00000001 order-reversing-involution)
    (00000001 exact-structural-match-of-answer)
    (00000001 grade-1-only)
    (00000001 ((0) () (1)))
    (00000001 ratified-2026-09-26)
    (00000001
      ((carrier . bit-list)
       (bits . (0 1))
       (yes-examples . ((1) (1 1) (1 1 1 1 1 1 1)))
       (no-examples . ((0) (0 0) (0 0 0 0 0 0 0)))
       (unknown . ())
       (max-width . 7)
       (spelling . notation-only)
       (short-bit-symbol-carrier . forbidden)
       (string-carrier . superseded-by-bit-list)
       (number-carrier . forbidden)))
    (00000001
      ((predicate-projection . core4)
       (atom? . ((on-atom (1)) (on-pair (0)) (on-empty-list ())))
       (eq? . ((on-same-atoms (1)) (on-distinct-atoms (0))))
       (runtime-status . installed)
       (answer-functions .
         ((10110001 answer-not)
          (10110010 answer-and)
          (10110011 answer-or)
          (10110100 answer-weaken)
          (10110101 answer-atom)
          (10110110 answer-eq)))
       (record-predicates . retired-2026-09-26)
       (cond-two-part-clause . selects-only-yes)
       (core1-core3-answer-domain . grade-1-only)
       (core1 . historical-unchanged-overlay-only)
       (core2 . frozen-compatibility)))
    8
    (00000001 (1))
    (00000001 (1))
    (00000001 (1))
    (00000001 (1))
    (00000001 (1))))

(00000111
  ((00100010 pas-observed pas-expected)
   (1)
   (00000001 (core4-predicate-answer-scale-ok)))
  ((00011100 1 1) 1
   (00100111 (00000001 core4-predicate-answer-scale-mismatch)
         pas-expected
         pas-observed)))
