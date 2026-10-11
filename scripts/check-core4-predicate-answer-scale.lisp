; #1391 — executable witness for the Core4 15-state answer scale.

(0011 pas-contract
  (100 (110101001 (110110111 "contracts/core4-predicate-answer-scale.lisp"))))
(0011 pas-schema (100 pas-contract))
(0011 pas-sections (011 pas-contract))

(0011 pas-field
  (0010 (section name)
    (011 (11100 name section))))

(0011 pas-meta (100 pas-sections))
(0011 pas-no (1001 pas-sections))
(0011 pas-boundary (10011 pas-sections))
(0011 pas-yes (100111 pas-sections))
(0011 pas-algebra (110110101 pas-sections))

(0011 pas-terminology (000100 5 pas-sections))
(0011 pas-carrier (000100 6 pas-sections))
(0011 pas-predicates (000100 7 pas-sections))

; Таблиця функцій: рядок (код (en ім'я) (ук …) …).
(0011 pas-registry
  (100 (110101001 (110110111 "lib/surface/semantic-registry.lisp"))))

; (код ім'я) з контракту -> (код ім'я-з-таблиці-функцій).
(0011 pas-registry-row
  (0010 (entry)
    (1110 (100 entry)
          (1001 (11100 (001 en) (011 (11100 (100 entry) pas-registry)))))))

(0011 pas-no-levels (pas-field pas-no (001 levels)))
(0011 pas-yes-levels (pas-field pas-yes (001 levels)))
(0011 pas-terms (pas-field pas-terminology (001 terms)))

; Рядок рівня: (бітовий-запис ступінь санскрит) -> (ступінь санскрит).
(0011 pas-grade-and-sanskrit
  (0010 (level) (011 level)))

; Рядок термінів: (ступінь санскрит uk en) -> (ступінь санскрит).
(0011 pas-term-grade-and-sanskrit
  (0010 (term) (1110 (100 term) (1001 term))))

(0011 pas-observed
  (1110
    pas-schema
    (pas-field pas-meta (001 answer-count))
    (pas-field pas-meta (001 answer-grammar))
    (pas-field pas-meta (001 sens-function-space))
    pas-no-levels
    (pas-field pas-boundary (001 boundary))
    (pas-field pas-boundary (001 sanskrit))
    (pas-field pas-boundary (001 direction))
    (pas-field pas-boundary (001 sens-function))
    (pas-field pas-boundary (001 convergence-functions))
    (pas-field pas-boundary (001 function-result))
    pas-yes-levels
    (01010 (000000 pas-no-levels) (000000 pas-yes-levels) 1)
    (pas-field pas-algebra (001 not-law))
    (pas-field pas-algebra (001 weakening-law))
    (pas-field pas-algebra (001 boundary-law))
    (pas-field pas-algebra (001 eighth-bit-law))
    (pas-field pas-algebra (001 function-convergence-law))
    (pas-field pas-boundary (001 meaning-uk))
    (pas-field pas-boundary (001 meaning-en))
    (pas-field pas-terminology (001 languages))
    pas-terms
    (11110111 (101000 pas-term-grade-and-sanskrit pas-terms)
            (101000 pas-grade-and-sanskrit pas-no-levels))
    (11110111 (101000 pas-term-grade-and-sanskrit pas-terms)
            (101000 pas-grade-and-sanskrit pas-yes-levels))
    (pas-field pas-terminology (001 boundary-term))
    (pas-field pas-algebra (001 truth-order))
    (pas-field pas-algebra (001 and-law))
    (pas-field pas-algebra (001 or-law))
    (pas-field pas-algebra (001 de-morgan-law))
    (pas-field pas-algebra (001 not-order-law))
    (pas-field pas-algebra (001 cond-law))
    (pas-field pas-algebra (001 excluded-middle-law))
    (pas-field pas-algebra (001 kleene-k3-slice))
    (pas-field pas-algebra (001 and-or-cond-law))
    pas-carrier
    pas-predicates
    (000000 pas-sections)
    (11110111 (101000 pas-registry-row (pas-field pas-predicates (001 answer-functions)))
            (pas-field pas-predicates (001 answer-functions)))
    ; Runtime відповідає рівно так, як записано в проєкціях контракту.
    (11110111 (1110 (111000000 (001 x)) (111000000 (001 (a))) (111000000 (001 ())))
            (101000 second (pas-field pas-predicates (001 atom?))))
    (11110111 (1110 (110110001 (001 a) (001 a)) (110110001 (001 a) (001 b)))
            (101000 second (pas-field pas-predicates (001 eq?))))
    ; Самі примітиви мови відповідають тією ж шкалою.
    (11110111 (1110 (010 (001 x)) (010 (001 (a))) (010 (001 ())))
            (101000 second (pas-field pas-predicates (001 atom?))))
    (11110111 (1110 (101 (001 a) (001 a)) (101 (001 a) (001 b)))
            (101000 second (pas-field pas-predicates (001 eq?))))))

(0011 pas-expected
  (1110
    (001 core4-predicate-answer-scale/3)
    15
    "0^n | 1^n | (), n=1..7"
    (001 separate-00000000-through-11111111)
    (001
      (("0"       1 dṛḍha-niścaya)
       ("00"      2 niścaya)
       ("000"     3 nirṇaya)
       ("0000"    4 saṃbhāvanā)
       ("00000"   5 saṃśaya)
       ("000000"  6 aniścaya)
       ("0000000" 7 ajñāta-sīmā)))
    (001 ())
    (001 ajñāta)
    (001 none)
    (001 none)
    (001 (00000000 11111111))
    (001 ())
    (001
      (("1"       1 dṛḍha-niścaya)
       ("11"      2 niścaya)
       ("111"     3 nirṇaya)
       ("1111"    4 saṃbhāvanā)
       ("11111"   5 saṃśaya)
       ("111111"  6 aniścaya)
       ("1111111" 7 ajñāta-sīmā)))
    15
    (001 same-width-bit-inversion)
    (001 append-same-bit)
    (001 seven-directed-grades-converge-to-empty-list)
    (001 belongs-to-sens-function-space)
    (001 distinct-functions-same-empty-result)
    "невідомо"
    "unknown"
    (001 (sanskrit uk en))
    (001
      ((1 dṛḍha-niścaya "тверда певність" "firm certainty")
       (2 niścaya       "певність"        "certainty")
       (3 nirṇaya       "висновок"        "determination")
       (4 saṃbhāvanā    "правдоподібність" "plausibility")
       (5 saṃśaya       "сумнів"          "doubt")
       (6 aniścaya      "непевність"      "uncertainty")
       (7 ajñāta-sīmā   "межа невідомого" "edge of the unknown")))
    (001 (1))
    (001 (1))
    (001 (ajñāta "невідомо" "unknown"))
    "0 < 00 < 000 < 0000 < 00000 < 000000 < 0000000 < () < 1111111 < 111111 < 11111 < 1111 < 111 < 11 < 1"
    (001 meet-on-truth-order)
    (001 join-on-truth-order)
    (001 or-is-not-of-and-of-nots)
    (001 order-reversing-involution)
    (001 exact-structural-match-of-answer)
    (001 grade-1-only)
    (001 ((0) () (1)))
    (001 ratified-2026-09-26)
    (001
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
    (001
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
    (001 (1))
    (001 (1))
    (001 (1))
    (001 (1))
    (001 (1))))

(110
  ((11110111 pas-observed pas-expected)
   (001 (core4-predicate-answer-scale-ok)))
  ((010 (001 ()))
   (1110 (001 core4-predicate-answer-scale-mismatch)
         pas-expected
         pas-observed)))
