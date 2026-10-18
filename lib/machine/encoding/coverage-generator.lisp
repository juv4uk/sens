; #604 — Lisp-owned encoder coverage authority.
; Inputs are generated, non-semantic machine projections:
;   pinned #175 (extension, ICLASS) index
;   structured Lisp admission -> partial ICLASS projection (#487/#2372)
; The old Rust 32-row classification is migration evidence only.

(визначити encoder-coverage-str+
  (функція args
    (101110 (функція (acc s) (110011110 acc s)) "" args)))

; Coverage authority uses exact D1 PredicateBit for every control decision.
; Deep structural equality is Lisp-owned here and is built only from current
; exact D3 laws: ATOM classifies pair-vs-atom and EQ compares admitted atoms.
; Historical deep-equality carriers do not cross into the authority path.
(визначити encoder-coverage-d1-yes
  (тотожне? (як-є encoder-coverage-yes) (як-є encoder-coverage-yes)))

(визначити encoder-coverage-d1-no
  (тотожне? (як-є encoder-coverage-yes) (як-є encoder-coverage-no)))

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
         (encoder-coverage-d1-yes
          encoder-coverage-d1-no)))
      ((атом? right)
       encoder-coverage-d1-no)
      ((encoder-coverage-same? (перше left) (перше right))
       (encoder-coverage-same? (решта left) (решта right)))
      (encoder-coverage-d1-yes
       encoder-coverage-d1-no))))

; Traversal needs structural EMPTY, not the broader ATOM classification.
; This preserves the D1:0 != D3:000 distinction and avoids using ATOM as NIL.
(визначити encoder-coverage-empty?
  (функція (value)
    (encoder-coverage-same? value (як-є ()))))

; Cardinality stays in canonical BinaryNumber from the first cell to the last.
; No ordinary Number -> BinaryNumber coercion exists or is needed.
(визначити encoder-coverage-binary-length-onto
  (функція (values count)
    (за-умовою
      ((encoder-coverage-empty? values) count)
      (encoder-coverage-d1-yes
       (encoder-coverage-binary-length-onto
         (решта values)
         (01010 count #b1))))))

(визначити encoder-coverage-binary-length
  (функція (values)
    (encoder-coverage-binary-length-onto values #b0)))

(визначити encoder-coverage-count=?
  (функція (binary-count values)
    (= binary-count
       (encoder-coverage-binary-length values))))


; Conjunction over already-admitted predicate answers. Structural EMPTY is
; only no-witness/non-selection; no generic T/NIL truthiness is consulted.
(визначити encoder-coverage-all?
  (функція (answers)
    (за-умовою
      ((encoder-coverage-empty? answers)
       encoder-coverage-d1-yes)
      ((перше answers)
       (encoder-coverage-all? (решта answers)))
      (encoder-coverage-d1-yes
       encoder-coverage-d1-no))))

(визначити encoder-coverage-pair=?
  (функція (left right)
    (encoder-coverage-same? left right)))
(визначити encoder-coverage-member?
  (функція (item values)
    (за-умовою
      ((encoder-coverage-empty? values) encoder-coverage-d1-no)
      ((encoder-coverage-same? item (перше values))
       encoder-coverage-d1-yes)
      (encoder-coverage-d1-yes
       (encoder-coverage-member? item (решта values))))))

; Pairwise rounds form a rope-like balanced concatenation tree. This avoids
; copying an ever-growing ~200 KB accumulator once per emitted coverage row.
(визначити encoder-coverage-concat-round
  (функція (strings acc)
    (за-умовою
      ((encoder-coverage-empty? strings) (10100 acc))
      ((encoder-coverage-empty? (решта strings))
       (10101 acc (список (перше strings))))
      (encoder-coverage-d1-yes
       (encoder-coverage-concat-round
         (решта (решта strings))
         (сполучити
           (110011110 (перше strings) (друге strings))
           acc))))))

(визначити encoder-coverage-balanced-concat
  (функція (strings)
    (за-умовою
      ((encoder-coverage-empty? strings) "")
      ((encoder-coverage-empty? (решта strings)) (перше strings))
      (encoder-coverage-d1-yes
       (encoder-coverage-balanced-concat
         (encoder-coverage-concat-round
           strings
           (як-є ())))))))

(визначити encoder-coverage-admission-projection-form
  (перше
    (110101001
      (110110111
        "lib/machine/encoding/admission-iclass-projection.lisp"))))

(визначити encoder-coverage-projection-head-count
  (друге (друге encoder-coverage-admission-projection-form)))

(визначити encoder-coverage-projection-partial-count
  (друге (10011 encoder-coverage-admission-projection-form)))

(визначити encoder-coverage-projection-orphan-count
  (друге (100111 encoder-coverage-admission-projection-form)))

(визначити encoder-coverage-partials
  (решта
    (решта
      (решта
        (решта encoder-coverage-admission-projection-form)))))

(визначити encoder-coverage-partial-reason
  "derived from structured Lisp admission; at least one admitted form maps to this pinned ICLASS; full XED operand/addressing coverage is not claimed")

(визначити encoder-coverage-legacy-form
  (перше
    (110101001
      (110110111
        "knowledge/encoder-coverage-legacy-parity.lisp"))))

(визначити encoder-coverage-legacy-count
  (друге (друге encoder-coverage-legacy-form)))

(визначити encoder-coverage-legacy-successor-count
  (друге (10011 encoder-coverage-legacy-form)))

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
        (encoder-coverage-same? (10011 left) (10011 right))))))

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
      (encoder-coverage-d1-yes
       "remaining BASE forms pending family-by-family rollout"))))

(визначити encoder-coverage-render-row
  (функція (row partial)
    (001001 ((extension (друге row))
           (iclass (10011 row))
           (status
             (за-умовою
               ((encoder-coverage-empty? partial) (як-є not-yet-implemented))
               (encoder-coverage-d1-yes (як-є partial))))
           (підстава
             (за-умовою
               ((encoder-coverage-empty? partial)
                (encoder-coverage-not-yet-reason extension))
               (encoder-coverage-d1-yes encoder-coverage-partial-reason))))
      (encoder-coverage-str+
        "  (coverage\n"
        "    (iclass " (11110100 iclass) ")\n"
        "    (extension " (11101110 extension) ")\n"
        "    (status " (11101110 status) ")\n"
        "    (reason " (11110100 підстава) "))\n"))))

; One tail-recursive ordered-subset merge performs classification,
; stale-partial detection, rendering and partial counting.
; Result = (rendered-rows partial-count exact-D1-stale-partial?).
(визначити encoder-coverage-build-onto
  (функція (index-rows partials rendered count)
    (за-умовою
      ((encoder-coverage-empty? index-rows)
       (за-умовою
         ((encoder-coverage-empty? partials)
          (список (10100 rendered) count encoder-coverage-d1-no))
         (encoder-coverage-d1-yes
          (список (10100 rendered) count encoder-coverage-d1-yes))))
      ((encoder-coverage-empty? partials)
       (encoder-coverage-build-onto
         (решта index-rows)
         partials
         (сполучити
           (encoder-coverage-render-row (перше index-rows) (як-є ()))
           rendered)
         count))
      (encoder-coverage-d1-yes
       (001000 ((index-row (перше index-rows))
             (partial-row (перше partials)))
         (за-умовою
           ((encoder-coverage-row-key=? index-row partial-row)
            (encoder-coverage-build-onto
              (решта index-rows)
              (решта partials)
              (сполучити
                (encoder-coverage-render-row index-row partial-row)
                rendered)
              (01010 count #b1)))
           (encoder-coverage-d1-yes
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
      ((encoder-coverage-empty? rows) encoder-coverage-d1-yes)
      ((encoder-coverage-empty? previous)
       (encoder-coverage-index-unique?
         (решта rows)
         (перше rows)))
      ((encoder-coverage-row-key=? (перше rows) previous)
       encoder-coverage-d1-no)
      (encoder-coverage-d1-yes
       (encoder-coverage-index-unique?
         (решта rows)
         (перше rows))))))

(визначити encoder-coverage-index-form
  (перше
    (110101001
      (110110111
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
      ((encoder-coverage-empty? partials) encoder-coverage-d1-yes)
      ((encoder-coverage-empty? index-rows) encoder-coverage-d1-no)
      (encoder-coverage-d1-yes
       (001000 ((index-row (перше index-rows))
             (partial-row (перше partials)))
         (за-умовою
           ((encoder-coverage-row-key=? index-row partial-row)
            (encoder-coverage-partials-valid?
              (решта index-rows)
              (решта partials)))
           (encoder-coverage-d1-yes
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
        (= encoder-coverage-projection-orphan-count #b0))
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
      (101000 1001 (encoder-coverage-index-checks)))))

(визначити encoder-coverage-committed-row-matches?
  (функція (index-row coverage-row partial-row)
    (за-умовою
      ((encoder-coverage-empty? coverage-row) encoder-coverage-d1-no)
      ((encoder-coverage-count=? #b101 coverage-row)
       (001001 ((expected-status
                (за-умовою
                  ((encoder-coverage-empty? partial-row) (як-є not-yet-implemented))
                  (encoder-coverage-d1-yes (як-є partial))))
              (expected-reason
                (за-умовою
                  ((encoder-coverage-empty? partial-row) (encoder-coverage-not-yet-reason (друге index-row)))
                  (encoder-coverage-d1-yes encoder-coverage-partial-reason))))
         (encoder-coverage-all?
           (список
             (encoder-coverage-same? (перше coverage-row) (як-є coverage))
             (encoder-coverage-same? (перше (друге coverage-row)) (як-є iclass))
             (encoder-coverage-same? (друге (друге coverage-row)) (10011 index-row))
             (encoder-coverage-same? (перше (10011 coverage-row)) (як-є extension))
             (encoder-coverage-same? (друге (10011 coverage-row)) (друге index-row))
             (encoder-coverage-same? (перше (100111 coverage-row)) (як-є status))
             (encoder-coverage-same? (друге (100111 coverage-row)) expected-status)
             (encoder-coverage-same? (перше (110110101 coverage-row)) (перше (110101001 "reason")))
             (encoder-coverage-same? (друге (110110101 coverage-row)) expected-reason)))))
      (encoder-coverage-d1-yes encoder-coverage-d1-no))))

(визначити encoder-coverage-projection-rows-valid?
  (функція (index-rows coverage-rows partials)
    (за-умовою
      ((encoder-coverage-empty? index-rows)
       (за-умовою
         ((encoder-coverage-empty? coverage-rows)
          (за-умовою
            ((encoder-coverage-empty? partials)
             encoder-coverage-d1-yes)
            (encoder-coverage-d1-yes
             encoder-coverage-d1-no)))
         (encoder-coverage-d1-yes
          encoder-coverage-d1-no)))
      ((encoder-coverage-empty? coverage-rows)
       encoder-coverage-d1-no)
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
         (encoder-coverage-d1-yes
          encoder-coverage-d1-no)))
      (encoder-coverage-d1-yes
       (001000 ((index-row (перше index-rows))
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
              (encoder-coverage-d1-yes
               encoder-coverage-d1-no)))
           (encoder-coverage-d1-yes
            (за-умовою
              ((encoder-coverage-committed-row-matches?
                 index-row
                 coverage-row
                 (як-є ()))
               (encoder-coverage-projection-rows-valid?
                 (решта index-rows)
                 (решта coverage-rows)
                 partials))
              (encoder-coverage-d1-yes
               encoder-coverage-d1-no)))))))))

(визначити encoder-coverage-projection-valid?
  (функція (coverage-form)
    (за-умовою
      ((encoder-coverage-empty? coverage-form) encoder-coverage-d1-no)
      ((encoder-coverage-count=?
         encoder-coverage-index-count
         (решта (решта (решта coverage-form))))
       (encoder-coverage-all?
         (список
           (encoder-coverage-same? (перше coverage-form) (як-є x86-encoder-coverage/1))
           (encoder-coverage-same? (перше (друге coverage-form)) (як-є form-count))
           (= (друге (друге coverage-form)) encoder-coverage-form-count)
           (encoder-coverage-same? (перше (10011 coverage-form)) (як-є partial-count))
           (= (друге (10011 coverage-form)) encoder-coverage-projection-partial-count)
           (encoder-coverage-projection-rows-valid?
             encoder-coverage-index-rows
             (решта (решта (решта coverage-form)))
             encoder-coverage-partials))))
      (encoder-coverage-d1-yes encoder-coverage-d1-no))))

(визначити encoder-coverage-render
  (функція ()
    (001001 ((build
             (encoder-coverage-build-onto
               encoder-coverage-index-rows
               encoder-coverage-partials
               (як-є ())
               #b0))
           (rendered-rows (перше build))
           (partial-count (друге build))
           (stale-partial? (10011 build))
           (prelude
             (encoder-coverage-str+
               "; GENERATED by `sens scripts/generate-encoder-coverage.lisp` -- do not hand-edit.\n"
               "; Sources: pinned #175 admitted ICLASS index + structured Lisp admission projection.\n"
               "; Every pinned (extension, ICLASS) pair appears exactly once. `partial` means at\n"
               "; least one structured admitted form is executable; it does not claim complete\n"
               "; coverage of every XED operand/addressing form. No silent third status (#176/#604).\n"
               "\n"
               "(x86-encoder-coverage/1\n"
               "  (form-count " (11110100 encoder-coverage-form-count) ")\n"
               "  (partial-count " (11110100 partial-count) ")\n")))
      (за-умовою
        (stale-partial?
         (як-є ()))
        (encoder-coverage-d1-yes
         (encoder-coverage-str+
           prelude
           (encoder-coverage-balanced-concat rendered-rows)
           ")\n"))))))
