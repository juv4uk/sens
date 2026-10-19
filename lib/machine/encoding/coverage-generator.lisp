; #604 — Lisp-owned encoder coverage authority.
; Inputs are generated, non-semantic machine projections:
;   pinned #175 (extension, ICLASS) index
;   structured Lisp admission -> partial ICLASS projection (#487/#2372)
; The old Rust 32-row classification is migration evidence only.

(визначити encoder-coverage-str+
  (функція аргументи
    (згорнути (функція (накопичене фрагмент) (рядок-додати накопичене фрагмент)) "" аргументи)))

; Coverage authority uses exact D1 PredicateBit for every control decision.
; Deep structural equality is Lisp-owned here and is built only from current
; exact D3 laws: ATOM classifies pair-vs-atom and EQ compares admitted atoms.
; Historical deep-equality carriers do not cross into the authority path.
; Власні D1:0/D1:1 проєкції — ні та так; EQ-маркери не потрібні.
(визначити encoder-coverage-atom-same?
  (функція (left right)
    (тотожне? left right)))

(визначити encoder-coverage-same?
  (функція (left right)
    (за-умовою
      ((атом? left)
       (за-умовою
         ((атом? right)
          (encoder-coverage-atom-same? left right))
         (так
          ні)))
      ((атом? right)
       ні)
      ((encoder-coverage-same? (перше left) (перше right))
       (encoder-coverage-same? (решта left) (решта right)))
      (так
       ні))))

; Traversal needs structural EMPTY, not the broader ATOM classification.
; This preserves the D1:0 != D3:000 distinction and avoids using ATOM as NIL.
(визначити encoder-coverage-empty?
  (функція (value)
    (encoder-coverage-same? value (як-є ()))))

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
    (= двійкова-кількість
       (encoder-coverage-binary-length елементи))))


; Conjunction over already-admitted predicate answers. Structural EMPTY is
; only no-witness/non-selection; no generic T/NIL truthiness is consulted.
(визначити encoder-coverage-all?
  (функція (answers)
    (за-умовою
      ((encoder-coverage-empty? answers)
       так)
      ((перше answers)
       (encoder-coverage-all? (решта answers)))
      (так
       ні))))

(визначити encoder-coverage-pair=?
  (функція (left right)
    (encoder-coverage-same? left right)))
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
  (функція (strings acc)
    (за-умовою
      ((encoder-coverage-empty? strings) (зворот acc))
      ((encoder-coverage-empty? (решта strings))
       (зворот-до acc (список (перше strings))))
      (так
       (encoder-coverage-concat-round
         (решта (решта strings))
         (сполучити
           (рядок-додати (перше strings) (друге strings))
           acc))))))

(визначити encoder-coverage-balanced-concat
  (функція (strings)
    (за-умовою
      ((encoder-coverage-empty? strings) "")
      ((encoder-coverage-empty? (решта strings)) (перше strings))
      (так
       (encoder-coverage-balanced-concat
         (encoder-coverage-concat-round
           strings
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
  (функція (left right)
    (encoder-coverage-all?
      (список
        (encoder-coverage-same? (друге left) (друге right))
        (encoder-coverage-same? (третє left) (третє right))))))

(визначити encoder-coverage-not-yet-reason
  (функція (extension)
    (за-умовою
      ((encoder-coverage-member? extension (як-є (AVX AVX2 FMA3 BMI1 BMI2 F16C)))
       "VEX-prefix encoding not yet implemented")
      ((encoder-coverage-same? extension (як-є X87))
       "x87 stack-register encoding not yet implemented")
      ((encoder-coverage-same? extension (як-є MMX))
       "MMX opcode-map encoding not yet implemented")
      ((encoder-coverage-member?
         extension
         (як-є (SSE SSE2 SSE3 SSSE3 SSE4.1+SSE4.2)))
       "legacy SSE mandatory-prefix/ModRM encoding not yet implemented")
      ((encoder-coverage-member? extension (як-є (AES-NI PCLMULQDQ)))
       "SSE-prefixed crypto encoding not yet implemented")
      ((encoder-coverage-same? extension (як-є XSAVE))
       "XSAVE control-state encoding not yet implemented")
      ((encoder-coverage-same? extension (як-є MPX))
       "BND-register encoding not yet implemented")
      ((encoder-coverage-same? extension (як-є SGX))
       "ENCLS/ENCLU leaf-function encoding not yet implemented")
      ((encoder-coverage-member? extension (як-є (RDRAND RDSEED)))
       "0F C7 opcode-map encoding not yet implemented")
      ((encoder-coverage-same? extension (як-є CLFLUSHOPT))
       "cache-management opcode encoding not yet implemented")
      ((encoder-coverage-same? extension (як-є X86-64))
       "long-mode-specific BASE forms pending family-by-family rollout")
      (так
       "remaining BASE forms pending family-by-family rollout"))))

(визначити encoder-coverage-render-row
  (функція (row partial)
    (нехай-послідовно ((extension (друге row))
           (iclass (третє row))
           (status
             (за-умовою
               ((encoder-coverage-empty? partial) (як-є not-yet-implemented))
               (так (як-є partial))))
           (підстава
             (за-умовою
               ((encoder-coverage-empty? partial)
                (encoder-coverage-not-yet-reason extension))
               (так encoder-coverage-partial-reason))))
      (encoder-coverage-str+
        "  (coverage\n"
        "    (iclass " (значення-у-текст iclass) ")\n"
        "    (extension " (символ-у-текст extension) ")\n"
        "    (status " (символ-у-текст status) ")\n"
        "    (reason " (значення-у-текст підстава) "))\n"))))

; One tail-recursive ordered-subset merge performs classification,
; stale-partial detection, rendering and partial counting.
; Result = (rendered-rows partial-count exact-D1-stale-partial?).
(визначити encoder-coverage-build-onto
  (функція (index-rows partials rendered count)
    (за-умовою
      ((encoder-coverage-empty? index-rows)
       (за-умовою
         ((encoder-coverage-empty? partials)
          (список (зворот rendered) count ні))
         (так
          (список (зворот rendered) count так))))
      ((encoder-coverage-empty? partials)
       (encoder-coverage-build-onto
         (решта index-rows)
         partials
         (сполучити
           (encoder-coverage-render-row (перше index-rows) (як-є ()))
           rendered)
         count))
      (так
       (нехай ((index-row (перше index-rows))
             (partial-row (перше partials)))
         (за-умовою
           ((encoder-coverage-row-key=? index-row partial-row)
            (encoder-coverage-build-onto
              (решта index-rows)
              (решта partials)
              (сполучити
                (encoder-coverage-render-row index-row partial-row)
                rendered)
              (додати count 1)))
           (так
            (encoder-coverage-build-onto
              (решта index-rows)
              partials
              (сполучити
                (encoder-coverage-render-row index-row (як-є ()))
                rendered)
              count))))))))

(визначити encoder-coverage-index-unique?
  (функція (rows previous)
    (за-умовою
      ((encoder-coverage-empty? rows) так)
      ((encoder-coverage-empty? previous)
       (encoder-coverage-index-unique?
         (решта rows)
         (перше rows)))
      ((encoder-coverage-row-key=? (перше rows) previous)
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
  (функція (index-rows partials)
    (за-умовою
      ((encoder-coverage-empty? partials) так)
      ((encoder-coverage-empty? index-rows) ні)
      (так
       (нехай ((index-row (перше index-rows))
             (partial-row (перше partials)))
         (за-умовою
           ((encoder-coverage-row-key=? index-row partial-row)
            (encoder-coverage-partials-valid?
              (решта index-rows)
              (решта partials)))
           (так
            (encoder-coverage-partials-valid?
              (решта index-rows)
              partials))))))))

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
        (= encoder-coverage-projection-orphan-count 0))
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
      (відобразити 1001 (encoder-coverage-index-checks)))))

(визначити encoder-coverage-committed-row-matches?
  (функція (index-row coverage-row partial-row)
    (за-умовою
      ((encoder-coverage-empty? coverage-row) ні)
      ((encoder-coverage-count=? 5 coverage-row)
       (нехай-послідовно ((expected-status
                (за-умовою
                  ((encoder-coverage-empty? partial-row) (як-є not-yet-implemented))
                  (так (як-є partial))))
              (expected-reason
                (за-умовою
                  ((encoder-coverage-empty? partial-row) (encoder-coverage-not-yet-reason (друге index-row)))
                  (так encoder-coverage-partial-reason))))
         (encoder-coverage-all?
           (список
             (encoder-coverage-same? (перше coverage-row) (як-є coverage))
             (encoder-coverage-same? (перше (друге coverage-row)) (як-є iclass))
             (encoder-coverage-same? (друге (друге coverage-row)) (третє index-row))
             (encoder-coverage-same? (перше (третє coverage-row)) (як-є extension))
             (encoder-coverage-same? (друге (третє coverage-row)) (друге index-row))
             (encoder-coverage-same? (перше (четверте coverage-row)) (як-є status))
             (encoder-coverage-same? (друге (четверте coverage-row)) expected-status)
             (encoder-coverage-same? (перше (перше (решта (решта (решта (решта coverage-row)))))) (перше (читати-всі "reason")))
             (encoder-coverage-same? (друге (перше (решта (решта (решта (решта coverage-row)))))) expected-reason)))))
      (так ні))))

(визначити encoder-coverage-projection-rows-valid?
  (функція (index-rows coverage-rows partials)
    (за-умовою
      ((encoder-coverage-empty? index-rows)
       (за-умовою
         ((encoder-coverage-empty? coverage-rows)
          (за-умовою
            ((encoder-coverage-empty? partials)
             так)
            (так
             ні)))
         (так
          ні)))
      ((encoder-coverage-empty? coverage-rows)
       ні)
      ((encoder-coverage-empty? partials)
       (за-умовою
         ((encoder-coverage-committed-row-matches?
            (перше index-rows)
            (перше coverage-rows)
            (як-є ()))
          (encoder-coverage-projection-rows-valid?
            (решта index-rows)
            (решта coverage-rows)
            partials))
         (так
          ні)))
      (так
       (нехай ((index-row (перше index-rows))
             (coverage-row (перше coverage-rows))
             (partial-row (перше partials)))
         (за-умовою
           ((encoder-coverage-row-key=? index-row partial-row)
            (за-умовою
              ((encoder-coverage-committed-row-matches?
                 index-row
                 coverage-row
                 partial-row)
               (encoder-coverage-projection-rows-valid?
                 (решта index-rows)
                 (решта coverage-rows)
                 (решта partials)))
              (так
               ні)))
           (так
            (за-умовою
              ((encoder-coverage-committed-row-matches?
                 index-row
                 coverage-row
                 (як-є ()))
               (encoder-coverage-projection-rows-valid?
                 (решта index-rows)
                 (решта coverage-rows)
                 partials))
              (так
               ні)))))))))

(визначити encoder-coverage-projection-valid?
  (функція (coverage-form)
    (за-умовою
      ((encoder-coverage-empty? coverage-form) ні)
      ((encoder-coverage-count=?
         encoder-coverage-index-count
         (решта (решта (решта coverage-form))))
       (encoder-coverage-all?
         (список
           (encoder-coverage-same? (перше coverage-form) (як-є x86-encoder-coverage/1))
           (encoder-coverage-same? (перше (друге coverage-form)) (як-є form-count))
           (= (друге (друге coverage-form)) encoder-coverage-form-count)
           (encoder-coverage-same? (перше (третє coverage-form)) (як-є partial-count))
           (= (друге (третє coverage-form)) encoder-coverage-projection-partial-count)
           (encoder-coverage-projection-rows-valid?
             encoder-coverage-index-rows
             (решта (решта (решта coverage-form)))
             encoder-coverage-partials))))
      (так ні))))

(визначити encoder-coverage-render
  (функція ()
    (нехай-послідовно ((build
             (encoder-coverage-build-onto
               encoder-coverage-index-rows
               encoder-coverage-partials
               (як-є ())
               0))
           (rendered-rows (перше build))
           (partial-count (друге build))
           (stale-partial? (третє build))
           (prelude
             (encoder-coverage-str+
               "; GENERATED by `sens scripts/generate-encoder-coverage.lisp` -- do not hand-edit.\n"
               "; Sources: pinned #175 admitted ICLASS index + structured Lisp admission projection.\n"
               "; Every pinned (extension, ICLASS) pair appears exactly once. `partial` means at\n"
               "; least one structured admitted form is executable; it does not claim complete\n"
               "; coverage of every XED operand/addressing form. No silent third status (#176/#604).\n"
               "\n"
               "(x86-encoder-coverage/1\n"
               "  (form-count " (значення-у-текст encoder-coverage-form-count) ")\n"
               "  (partial-count " (значення-у-текст partial-count) ")\n")))
      (за-умовою
        (stale-partial?
         (як-є ()))
        (так
         (encoder-coverage-str+
           prelude
           (encoder-coverage-balanced-concat rendered-rows)
           ")\n"))))))
