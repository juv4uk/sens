; #1391 — executable witness for the Core4 15-state answer scale.

(визначити pas-contract
  (100 (110101001 (110110111 "contracts/core4-predicate-answer-scale.lisp"))))
(визначити pas-schema (перше pas-contract))
(визначити pas-sections (решта pas-contract))

(визначити pas-field
  (функція (section name)
    (011 (11100 name section))))

(визначити pas-meta (перше pas-sections))
(визначити pas-no (друге pas-sections))
(0011 pas-boundary (10011 pas-sections))
(0011 pas-yes (100111 pas-sections))
(0011 pas-algebra (110110101 pas-sections))

(0011 pas-terminology (000100 5 pas-sections))
(0011 pas-carrier (000100 6 pas-sections))
(0011 pas-predicates (000100 7 pas-sections))

; Таблиця функцій: рядок (код (en ім'я) (ук …) …).
(визначити pas-registry
  (100 (110101001 (110110111 "lib/surface/semantic-registry.lisp"))))

; (код ім'я) з контракту -> (код ім'я-з-таблиці-функцій).
(визначити pas-registry-row
  (функція (entry)
    (список (перше entry)
          (1001 (11100 (001 en) (011 (11100 (100 entry) pas-registry)))))))

(визначити pas-no-levels (pas-field pas-no (як-є levels)))
(визначити pas-yes-levels (pas-field pas-yes (як-є levels)))
(визначити pas-terms (pas-field pas-terminology (як-є terms)))

; Рядок рівня: (бітовий-запис ступінь санскрит) -> (ступінь санскрит).
(визначити pas-grade-and-sanskrit
  (функція (level) (решта level)))

; Рядок термінів: (ступінь санскрит uk en) -> (ступінь санскрит).
(визначити pas-term-grade-and-sanskrit
  (функція (term) (список (перше term) (друге term))))

(визначити pas-observed
  (список
    pas-schema
    (pas-field pas-meta (як-є answer-count))
    (pas-field pas-meta (як-є answer-grammar))
    (pas-field pas-meta (як-є sens-function-space))
    pas-no-levels
    (pas-field pas-boundary (як-є boundary))
    (pas-field pas-boundary (як-є sanskrit))
    (pas-field pas-boundary (як-є direction))
    (pas-field pas-boundary (як-є sens-function))
    (pas-field pas-boundary (як-є convergence-functions))
    (pas-field pas-boundary (як-є function-result))
    pas-yes-levels
    (01010 (000000 pas-no-levels) (000000 pas-yes-levels) 1)
    (pas-field pas-algebra (як-є not-law))
    (pas-field pas-algebra (як-є weakening-law))
    (pas-field pas-algebra (як-є boundary-law))
    (pas-field pas-algebra (як-є eighth-bit-law))
    (pas-field pas-algebra (як-є function-convergence-law))
    (pas-field pas-boundary (як-є meaning-uk))
    (pas-field pas-boundary (як-є meaning-en))
    (pas-field pas-terminology (як-є languages))
    pas-terms
    (11110111 (101000 pas-term-grade-and-sanskrit pas-terms)
            (101000 pas-grade-and-sanskrit pas-no-levels))
    (11110111 (101000 pas-term-grade-and-sanskrit pas-terms)
            (101000 pas-grade-and-sanskrit pas-yes-levels))
    (pas-field pas-terminology (як-є boundary-term))
    (pas-field pas-algebra (як-є truth-order))
    (pas-field pas-algebra (як-є and-law))
    (pas-field pas-algebra (як-є or-law))
    (pas-field pas-algebra (як-є de-morgan-law))
    (pas-field pas-algebra (як-є not-order-law))
    (pas-field pas-algebra (як-є cond-law))
    (pas-field pas-algebra (як-є excluded-middle-law))
    (pas-field pas-algebra (як-є kleene-k3-slice))
    (pas-field pas-algebra (як-є and-or-cond-law))
    pas-carrier
    pas-predicates
    (000000 pas-sections)
    (11110111 (101000 pas-registry-row (pas-field pas-predicates (001 answer-functions)))
            (pas-field pas-predicates (як-є answer-functions)))
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

(визначити pas-expected
  (список
    (як-є core4-predicate-answer-scale/3)
    15
    "0^n | 1^n | (), n=1..7"
    (як-є separate-00000000-through-11111111)
    (як-є
      (("0"       1 dṛḍha-niścaya)
       ("00"      2 niścaya)
       ("000"     3 nirṇaya)
       ("0000"    4 saṃbhāvanā)
       ("00000"   5 saṃśaya)
       ("000000"  6 aniścaya)
       ("0000000" 7 ajñāta-sīmā)))
    (як-є ())
    (як-є ajñāta)
    (як-є none)
    (як-є none)
    (001 (00000000 11111111))
    (як-є ())
    (як-є
      (("1"       1 dṛḍha-niścaya)
       ("11"      2 niścaya)
       ("111"     3 nirṇaya)
       ("1111"    4 saṃbhāvanā)
       ("11111"   5 saṃśaya)
       ("111111"  6 aniścaya)
       ("1111111" 7 ajñāta-sīmā)))
    15
    (як-є same-width-bit-inversion)
    (як-є append-same-bit)
    (як-є seven-directed-grades-converge-to-empty-list)
    (як-є belongs-to-sens-function-space)
    (як-є distinct-functions-same-empty-result)
    "невідомо"
    "unknown"
    (як-є (sanskrit uk en))
    (як-є
      ((1 dṛḍha-niścaya "тверда певність" "firm certainty")
       (2 niścaya       "певність"        "certainty")
       (3 nirṇaya       "висновок"        "determination")
       (4 saṃbhāvanā    "правдоподібність" "plausibility")
       (5 saṃśaya       "сумнів"          "doubt")
       (6 aniścaya      "непевність"      "uncertainty")
       (7 ajñāta-sīmā   "межа невідомого" "edge of the unknown")))
    (001 (1))
    (001 (1))
    (як-є (ajñāta "невідомо" "unknown"))
    "0 < 00 < 000 < 0000 < 00000 < 000000 < 0000000 < () < 1111111 < 111111 < 11111 < 1111 < 111 < 11 < 1"
    (як-є meet-on-truth-order)
    (як-є join-on-truth-order)
    (як-є or-is-not-of-and-of-nots)
    (як-є order-reversing-involution)
    (як-є exact-structural-match-of-answer)
    (як-є grade-1-only)
    (001 ((0) () (1)))
    (як-є ratified-2026-09-26)
    (як-є
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
    (як-є
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

(за-умовою
  ((11110111 pas-observed pas-expected)
   (як-є (core4-predicate-answer-scale-ok)))
  ((010 (001 ()))
   (список (як-є core4-predicate-answer-scale-mismatch)
         pas-expected
         pas-observed)))
