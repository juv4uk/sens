; Точне формування звіту покриття машинного кодувальника SENS.
; Джерела: ратифікований перелік машинних інструкцій та проєкція допусків.
; Цей модуль створює дані про перевірену реалізацію, а не мовні функції.
; Керувальні результати мають точні значення D1 «так» і «ні».
; Зіставлення списків визначено мовними операціями D3; числа — десяткові.
; Жодних старих кодів SID8/Sens8 або машинних бітових викличних голів.
; Значення полів ICLASS, extension, status і reason — протокольні дані.
;
(визначити encoder-coverage-str+
  (функція аргументи
    (згорнути (функція (накопичене фрагмент) (рядок-додати накопичене фрагмент)) "" аргументи)))

; Coverage authority uses exact D1 PredicateBit for every control decision.
; Deep structural equality is Lisp-owned here and is built only from current
; exact D3 laws: ATOM classifies pair-vs-atom and EQ compares admitted atoms.
; Historical deep-equality carriers do not cross into the authority path.
; Власні D1:0/D1:1 проєкції — ні та так; EQ-маркери не потрібні.
(визначити encoder-coverage-atom-same?
  (функція (ліве-значення праве-значення)
    (тотожне? ліве-значення праве-значення)))

(визначити encoder-coverage-same?
  (функція (ліве-значення праве-значення)
    (за-умовою
      ((атом? ліве-значення)
       (за-умовою
         ((атом? праве-значення)
          (encoder-coverage-atom-same? ліве-значення праве-значення))
         (так
          ні)))
      ((атом? праве-значення)
       ні)
      ((encoder-coverage-same? (перше ліве-значення) (перше праве-значення))
       (encoder-coverage-same? (решта ліве-значення) (решта праве-значення)))
      (так
       ні))))

; Traversal needs structural EMPTY, not the broader ATOM classification.
; This preserves the D1:0 != D3:000 distinction and avoids using ATOM as NIL.
(визначити encoder-coverage-empty?
  (функція (значення)
    (encoder-coverage-same? значення (як-є ()))))

; Кількість елементів — математичне десяткове число D24+ від першої комірки.
; У вихідній програмі звичайні 0, 1 та 5; фізичне T5M-пакування належить Zig.
(визначити encoder-coverage-binary-length-onto
  (функція (елементи кількість)
    (за-умовою
      ((encoder-coverage-empty? елементи) кількість)
      (так
       (encoder-coverage-binary-length-onto
         (решта елементи)
         (додати кількість 1))))))

(визначити encoder-coverage-binary-length
  (функція (елементи)
    (encoder-coverage-binary-length-onto елементи 0)))

(визначити encoder-coverage-count=?
  (функція (двійкова-кількість елементи)
    (тотожне? двійкова-кількість
       (encoder-coverage-binary-length елементи))))


; Conjunction over already-admitted predicate answers. Structural EMPTY is
; only no-witness/non-selection; no generic T/NIL truthiness is consulted.
(визначити encoder-coverage-all?
  (функція (відповіді)
    (за-умовою
      ((encoder-coverage-empty? відповіді)
       так)
      ((перше відповіді)
       (encoder-coverage-all? (решта відповіді)))
      (так
       ні))))

(визначити encoder-coverage-pair=?
  (функція (ліве-значення праве-значення)
    (encoder-coverage-same? ліве-значення праве-значення)))
(визначити encoder-coverage-member?
  (функція (елемент елементи)
    (за-умовою
      ((encoder-coverage-empty? елементи) ні)
      ((encoder-coverage-same? елемент (перше елементи))
       так)
      (так
       (encoder-coverage-member? елемент (решта елементи))))))

; Pairwise rounds form a rope-like balanced concatenation tree. This avoids
; copying an ever-growing ~200 KB accumulator once per emitted coverage row.
(визначити encoder-coverage-concat-round
  (функція (рядки накопичені-рядки)
    (за-умовою
      ((encoder-coverage-empty? рядки) (зворот накопичені-рядки))
      ((encoder-coverage-empty? (решта рядки))
       (зворот-до накопичені-рядки (список (перше рядки))))
      (так
       (encoder-coverage-concat-round
         (решта (решта рядки))
         (сполучити
           (рядок-додати (перше рядки) (друге рядки))
           накопичені-рядки))))))

(визначити encoder-coverage-balanced-concat
  (функція (рядки)
    (за-умовою
      ((encoder-coverage-empty? рядки) "")
      ((encoder-coverage-empty? (решта рядки)) (перше рядки))
      (так
       (encoder-coverage-balanced-concat
         (encoder-coverage-concat-round
           рядки
           (як-є ())))))))

(визначити encoder-coverage-admission-projection-form
  (перше
    (читати-всі
      (читати-файл
        "lib/machine/encoding/admission-iclass-projection.lisp"))))

(визначити encoder-coverage-projection-head-count
  (друге (друге encoder-coverage-admission-projection-form)))

(визначити encoder-coverage-projection-partial-count
  (друге (третє encoder-coverage-admission-projection-form)))

(визначити encoder-coverage-projection-orphan-count
  (друге (четверте encoder-coverage-admission-projection-form)))

(визначити encoder-coverage-partials
  (решта
    (решта
      (решта
        (решта encoder-coverage-admission-projection-form)))))

(визначити encoder-coverage-partial-reason
  "derived from structured Lisp admission; at least one admitted form maps to this pinned ICLASS; full XED operand/addressing coverage is not claimed")

(визначити encoder-coverage-legacy-form
  (перше
    (читати-всі
      (читати-файл
        "knowledge/encoder-coverage-legacy-parity.lisp"))))

(визначити encoder-coverage-legacy-count
  (друге (друге encoder-coverage-legacy-form)))

(визначити encoder-coverage-legacy-successor-count
  (друге (третє encoder-coverage-legacy-form)))

(визначити encoder-coverage-legacy-pairs
  (решта (решта (решта encoder-coverage-legacy-form))))


; Both generated inputs share the same canonical ICLASS/extension order.
; Equality is enough: on mismatch advance the admitted index; an out-of-order
; or stale partial remains unconsumed and fails closed at index exhaustion.
(визначити encoder-coverage-row-key=?
  (функція (ліве-значення праве-значення)
    (encoder-coverage-all?
      (список
        (encoder-coverage-same? (друге ліве-значення) (друге праве-значення))
        (encoder-coverage-same? (третє ліве-значення) (третє праве-значення))))))

(визначити encoder-coverage-not-yet-reason
  (функція (розширення)
    (за-умовою
      ((encoder-coverage-member? розширення (як-є (AVX AVX2 FMA3 BMI1 BMI2 F16C)))
       "VEX-prefix encoding not yet implemented")
      ((encoder-coverage-same? розширення (як-є X87))
       "x87 stack-register encoding not yet implemented")
      ((encoder-coverage-same? розширення (як-є MMX))
       "MMX opcode-map encoding not yet implemented")
      ((encoder-coverage-member?
         розширення
         (як-є (SSE SSE2 SSE3 SSSE3 SSE4.1+SSE4.2)))
       "legacy SSE mandatory-prefix/ModRM encoding not yet implemented")
      ((encoder-coverage-member? розширення (як-є (AES-NI PCLMULQDQ)))
       "SSE-prefixed crypto encoding not yet implemented")
      ((encoder-coverage-same? розширення (як-є XSAVE))
       "XSAVE control-state encoding not yet implemented")
      ((encoder-coverage-same? розширення (як-є MPX))
       "BND-register encoding not yet implemented")
      ((encoder-coverage-same? розширення (як-є SGX))
       "ENCLS/ENCLU leaf-function encoding not yet implemented")
      ((encoder-coverage-member? розширення (як-є (RDRAND RDSEED)))
       "0F C7 opcode-map encoding not yet implemented")
      ((encoder-coverage-same? розширення (як-є CLFLUSHOPT))
       "cache-management opcode encoding not yet implemented")
      ((encoder-coverage-same? розширення (як-є X86-64))
       "long-mode-specific BASE forms pending family-by-family rollout")
      (так
       "remaining BASE forms pending family-by-family rollout"))))

(визначити encoder-coverage-render-row
  (функція (рядок-покриття частковий-запис)
    (нехай-послідовно ((розширення (друге рядок-покриття))
           (клас-інструкції (третє рядок-покриття))
           (стан-покриття
             (за-умовою
               ((encoder-coverage-empty? частковий-запис) (як-є not-yet-implemented))
               (так (як-є partial))))
           (підстава
             (за-умовою
               ((encoder-coverage-empty? частковий-запис)
                (encoder-coverage-not-yet-reason розширення))
               (так encoder-coverage-partial-reason))))
      (encoder-coverage-str+
        "  (coverage\n"
        "    (iclass " (значення-у-текст клас-інструкції) ")\n"
        "    (extension " (символ-у-текст розширення) ")\n"
        "    (status " (символ-у-текст стан-покриття) ")\n"
        "    (reason " (значення-у-текст підстава) "))\n"))))

; One tail-recursive ordered-subset merge performs classification,
; stale-partial detection, rendering and partial counting.
; Result = (rendered-rows partial-count exact-D1-stale-partial?).
(визначити encoder-coverage-build-onto
  (функція (рядки-індексу часткові-записи побудовані-рядки кількість)
    (за-умовою
      ((encoder-coverage-empty? рядки-індексу)
       (за-умовою
         ((encoder-coverage-empty? часткові-записи)
          (список (зворот побудовані-рядки) кількість ні))
         (так
          (список (зворот побудовані-рядки) кількість так))))
      ((encoder-coverage-empty? часткові-записи)
       (encoder-coverage-build-onto
         (решта рядки-індексу)
         часткові-записи
         (сполучити
           (encoder-coverage-render-row (перше рядки-індексу) (як-є ()))
           побудовані-рядки)
         кількість))
      (так
       (нехай ((рядок-індексу (перше рядки-індексу))
             (рядок-часткового-покриття (перше часткові-записи)))
         (за-умовою
           ((encoder-coverage-row-key=? рядок-індексу рядок-часткового-покриття)
            (encoder-coverage-build-onto
              (решта рядки-індексу)
              (решта часткові-записи)
              (сполучити
                (encoder-coverage-render-row рядок-індексу рядок-часткового-покриття)
                побудовані-рядки)
              (додати кількість 1)))
           (так
            (encoder-coverage-build-onto
              (решта рядки-індексу)
              часткові-записи
              (сполучити
                (encoder-coverage-render-row рядок-індексу (як-є ()))
                побудовані-рядки)
              кількість))))))))

(визначити encoder-coverage-index-unique?
  (функція (rows попередній-рядок)
    (за-умовою
      ((encoder-coverage-empty? rows) так)
      ((encoder-coverage-empty? попередній-рядок)
       (encoder-coverage-index-unique?
         (решта rows)
         (перше rows)))
      ((encoder-coverage-row-key=? (перше rows) попередній-рядок)
       ні)
      (так
       (encoder-coverage-index-unique?
         (решта rows)
         (перше rows))))))

(визначити encoder-coverage-index-form
  (перше
    (читати-всі
      (читати-файл
        "lib/machine/encoding/admitted-iclass-index.lisp"))))

(визначити encoder-coverage-index-count
  (друге (друге encoder-coverage-index-form)))

(визначити encoder-coverage-index-rows
  (решта (решта encoder-coverage-index-form)))

(визначити encoder-coverage-form-count
  (encoder-coverage-binary-length encoder-coverage-index-rows))

(визначити encoder-coverage-partials-valid?
  (функція (рядки-індексу часткові-записи)
    (за-умовою
      ((encoder-coverage-empty? часткові-записи) так)
      ((encoder-coverage-empty? рядки-індексу) ні)
      (так
       (нехай ((рядок-індексу (перше рядки-індексу))
             (рядок-часткового-покриття (перше часткові-записи)))
         (за-умовою
           ((encoder-coverage-row-key=? рядок-індексу рядок-часткового-покриття)
            (encoder-coverage-partials-valid?
              (решта рядки-індексу)
              (решта часткові-записи)))
           (так
            (encoder-coverage-partials-valid?
              (решта рядки-індексу)
              часткові-записи))))))))

(визначити encoder-coverage-index-checks
  (функція ()
    (список
      (список (як-є admitted-head)
        (encoder-coverage-same? (перше encoder-coverage-index-form) (як-є x86-admitted-iclass-index/2)))
      (список (як-є admitted-count)
        (encoder-coverage-count=? encoder-coverage-index-count encoder-coverage-index-rows))
      (список (як-є admitted-unique)
        (encoder-coverage-index-unique? encoder-coverage-index-rows (як-є ())))
      (список (як-є projection-head)
        (encoder-coverage-same? (перше encoder-coverage-admission-projection-form) (як-є x86-admission-iclass-projection/1)))
      (список (як-є projection-count)
        (encoder-coverage-count=? encoder-coverage-projection-partial-count encoder-coverage-partials))
      (список (як-є projection-orphan-zero)
        (тотожне? encoder-coverage-projection-orphan-count 0))
      (список (як-є projection-subset)
        (encoder-coverage-partials-valid? encoder-coverage-index-rows encoder-coverage-partials))
      (список (як-є legacy-head)
        (encoder-coverage-same? (перше encoder-coverage-legacy-form) (як-є encoder-coverage-legacy-parity/1)))
      (список (як-є legacy-count)
        (encoder-coverage-count=? encoder-coverage-legacy-count encoder-coverage-legacy-pairs))
      (список (як-є legacy-successor-count)
        (encoder-coverage-count=? encoder-coverage-legacy-successor-count encoder-coverage-partials))
      (список (як-є legacy-subset)
        (encoder-coverage-partials-valid? encoder-coverage-partials encoder-coverage-legacy-pairs)))))

(визначити encoder-coverage-index-valid?
  (функція ()
    (encoder-coverage-all?
      (відобразити
        (функція (перевірка)
          (друге перевірка))
        (encoder-coverage-index-checks)))))

(визначити encoder-coverage-committed-row-matches?
  (функція (рядок-індексу запис-покриття рядок-часткового-покриття)
    (за-умовою
      ((encoder-coverage-empty? запис-покриття) ні)
      ((encoder-coverage-count=? 5 запис-покриття)
       (нехай-послідовно ((очікуваний-стан
                (за-умовою
                  ((encoder-coverage-empty? рядок-часткового-покриття) (як-є not-yet-implemented))
                  (так (як-є partial))))
              (очікувана-підстава
                (за-умовою
                  ((encoder-coverage-empty? рядок-часткового-покриття) (encoder-coverage-not-yet-reason (друге рядок-індексу)))
                  (так encoder-coverage-partial-reason))))
         (encoder-coverage-all?
           (список
             (encoder-coverage-same? (перше запис-покриття) (як-є coverage))
             (encoder-coverage-same? (перше (друге запис-покриття)) (як-є iclass))
             (encoder-coverage-same? (друге (друге запис-покриття)) (третє рядок-індексу))
             (encoder-coverage-same? (перше (третє запис-покриття)) (як-є extension))
             (encoder-coverage-same? (друге (третє запис-покриття)) (друге рядок-індексу))
             (encoder-coverage-same? (перше (четверте запис-покриття)) (як-є status))
             (encoder-coverage-same? (друге (четверте запис-покриття)) очікуваний-стан)
             (encoder-coverage-same? (перше (перше (решта (решта (решта (решта запис-покриття)))))) (перше (читати-всі "reason")))
             (encoder-coverage-same? (друге (перше (решта (решта (решта (решта запис-покриття)))))) очікувана-підстава)))))
      (так ні))))

(визначити encoder-coverage-projection-rows-valid?
  (функція (рядки-індексу записи-покриття часткові-записи)
    (за-умовою
      ((encoder-coverage-empty? рядки-індексу)
       (за-умовою
         ((encoder-coverage-empty? записи-покриття)
          (за-умовою
            ((encoder-coverage-empty? часткові-записи)
             так)
            (так
             ні)))
         (так
          ні)))
      ((encoder-coverage-empty? записи-покриття)
       ні)
      ((encoder-coverage-empty? часткові-записи)
       (за-умовою
         ((encoder-coverage-committed-row-matches?
            (перше рядки-індексу)
            (перше записи-покриття)
            (як-є ()))
          (encoder-coverage-projection-rows-valid?
            (решта рядки-індексу)
            (решта записи-покриття)
            часткові-записи))
         (так
          ні)))
      (так
       (нехай ((рядок-індексу (перше рядки-індексу))
             (запис-покриття (перше записи-покриття))
             (рядок-часткового-покриття (перше часткові-записи)))
         (за-умовою
           ((encoder-coverage-row-key=? рядок-індексу рядок-часткового-покриття)
            (за-умовою
              ((encoder-coverage-committed-row-matches?
                 рядок-індексу
                 запис-покриття
                 рядок-часткового-покриття)
               (encoder-coverage-projection-rows-valid?
                 (решта рядки-індексу)
                 (решта записи-покриття)
                 (решта часткові-записи)))
              (так
               ні)))
           (так
            (за-умовою
              ((encoder-coverage-committed-row-matches?
                 рядок-індексу
                 запис-покриття
                 (як-є ()))
               (encoder-coverage-projection-rows-valid?
                 (решта рядки-індексу)
                 (решта записи-покриття)
                 часткові-записи))
              (так
               ні)))))))))

(визначити encoder-coverage-projection-valid?
  (функція (форма-покриття)
    (за-умовою
      ((encoder-coverage-empty? форма-покриття) ні)
      ((encoder-coverage-count=?
         encoder-coverage-index-count
         (решта (решта (решта форма-покриття))))
       (encoder-coverage-all?
         (список
           (encoder-coverage-same? (перше форма-покриття) (як-є x86-encoder-coverage/1))
           (encoder-coverage-same? (перше (друге форма-покриття)) (як-є form-count))
           (тотожне? (друге (друге форма-покриття)) encoder-coverage-form-count)
           (encoder-coverage-same? (перше (третє форма-покриття)) (як-є partial-count))
           (тотожне? (друге (третє форма-покриття)) encoder-coverage-projection-partial-count)
           (encoder-coverage-projection-rows-valid?
             encoder-coverage-index-rows
             (решта (решта (решта форма-покриття)))
             encoder-coverage-partials))))
      (так ні))))

(визначити encoder-coverage-render
  (функція ()
    (нехай-послідовно ((побудова
             (encoder-coverage-build-onto
               encoder-coverage-index-rows
               encoder-coverage-partials
               (як-є ())
               0))
           (рядки-результату (перше побудова))
           (кількість-часткових (друге побудова))
           (застарілі-часткові? (третє побудова))
           (заголовок
             (encoder-coverage-str+
               "; GENERATED by `sens scripts/generate-encoder-coverage.lisp` -- do not hand-edit.\n"
               "; Sources: pinned #175 admitted ICLASS index + structured Lisp admission projection.\n"
               "; Every pinned (extension, ICLASS) pair appears exactly once. `partial` means at\n"
               "; least one structured admitted form is executable; it does not claim complete\n"
               "; coverage of every XED operand/addressing form. No silent third status (#176/#604).\n"
               "\n"
               "(x86-encoder-coverage/1\n"
               "  (form-count " (значення-у-текст encoder-coverage-form-count) ")\n"
               "  (partial-count " (значення-у-текст кількість-часткових) ")\n")))
      (за-умовою
        (застарілі-часткові?
         (як-є ()))
        (так
         (encoder-coverage-str+
           заголовок
           (encoder-coverage-balanced-concat рядки-результату)
           ")\n"))))))
