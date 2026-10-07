; #604 — Lisp-owned encoder coverage authority.
; Inputs are generated, non-semantic machine projections:
;   pinned #175 (extension, ICLASS) index
;   structured Lisp admission -> partial ICLASS projection (#487/#2372)
; The old Rust 32-row classification is migration evidence only.

(0011 encoder-coverage-str+
  (0010 args
    (101110 (0010 (acc s) (110011110 acc s)) "" args)))

; Coverage authority uses exact D1 PredicateBit for every control decision.
; Deep structural equality is Lisp-owned here and is built only from current
; exact D3 laws: ATOM classifies pair-vs-atom and EQ compares admitted atoms.
; Historical deep-equality carriers do not cross into the authority path.
(0011 encoder-coverage-d1-yes
  (101 (001 encoder-coverage-yes) (001 encoder-coverage-yes)))

(0011 encoder-coverage-d1-no
  (101 (001 encoder-coverage-yes) (001 encoder-coverage-no)))

(0011 encoder-coverage-atom-same?
  (0010 (left right)
    (101 left right)))

(0011 encoder-coverage-same?
  (0010 (left right)
    (110
      ((010 left)
       (110
         ((010 right)
          (encoder-coverage-atom-same? left right))
         (encoder-coverage-d1-yes
          encoder-coverage-d1-no)))
      ((010 right)
       encoder-coverage-d1-no)
      ((encoder-coverage-same? (100 left) (100 right))
       (encoder-coverage-same? (011 left) (011 right)))
      (encoder-coverage-d1-yes
       encoder-coverage-d1-no))))

; Traversal needs structural EMPTY, not the broader ATOM classification.
; This preserves the D1:0 != D3:000 distinction and avoids using ATOM as NIL.
(0011 encoder-coverage-empty?
  (0010 (value)
    (encoder-coverage-same? value (001 ()))))

; Cardinality stays in canonical BinaryNumber from the first cell to the last.
; No ordinary Number -> BinaryNumber coercion exists or is needed.
(0011 encoder-coverage-binary-length-onto
  (0010 (values count)
    (110
      ((encoder-coverage-empty? values) count)
      (encoder-coverage-d1-yes
       (encoder-coverage-binary-length-onto
         (011 values)
         (01010 count #b1))))))

(0011 encoder-coverage-binary-length
  (0010 (values)
    (encoder-coverage-binary-length-onto values #b0)))

(0011 encoder-coverage-count=?
  (0010 (binary-count values)
    (= binary-count
       (encoder-coverage-binary-length values))))


; Conjunction over already-admitted predicate answers. Structural EMPTY is
; only no-witness/non-selection; no generic T/NIL truthiness is consulted.
(0011 encoder-coverage-all?
  (0010 (answers)
    (110
      ((encoder-coverage-empty? answers)
       encoder-coverage-d1-yes)
      ((100 answers)
       (encoder-coverage-all? (011 answers)))
      (encoder-coverage-d1-yes
       encoder-coverage-d1-no))))

(0011 encoder-coverage-pair=?
  (0010 (left right)
    (encoder-coverage-same? left right)))
(0011 encoder-coverage-member?
  (0010 (item values)
    (110
      ((encoder-coverage-empty? values) encoder-coverage-d1-no)
      ((encoder-coverage-same? item (100 values))
       encoder-coverage-d1-yes)
      (encoder-coverage-d1-yes
       (encoder-coverage-member? item (011 values))))))

; Pairwise rounds form a rope-like balanced concatenation tree. This avoids
; copying an ever-growing ~200 KB accumulator once per emitted coverage row.
(0011 encoder-coverage-concat-round
  (0010 (strings acc)
    (110
      ((encoder-coverage-empty? strings) (10100 acc))
      ((encoder-coverage-empty? (011 strings))
       (10101 acc (1110 (100 strings))))
      (encoder-coverage-d1-yes
       (encoder-coverage-concat-round
         (011 (011 strings))
         (111
           (110011110 (100 strings) (1001 strings))
           acc))))))

(0011 encoder-coverage-balanced-concat
  (0010 (strings)
    (110
      ((encoder-coverage-empty? strings) "")
      ((encoder-coverage-empty? (011 strings)) (100 strings))
      (encoder-coverage-d1-yes
       (encoder-coverage-balanced-concat
         (encoder-coverage-concat-round
           strings
           (001 ())))))))

(0011 encoder-coverage-admission-projection-form
  (100
    (110101001
      (110110111
        "lib/machine/encoding/admission-iclass-projection.lisp"))))

(0011 encoder-coverage-projection-head-count
  (1001 (1001 encoder-coverage-admission-projection-form)))

(0011 encoder-coverage-projection-partial-count
  (1001 (10011 encoder-coverage-admission-projection-form)))

(0011 encoder-coverage-projection-orphan-count
  (1001 (100111 encoder-coverage-admission-projection-form)))

(0011 encoder-coverage-partials
  (011
    (011
      (011
        (011 encoder-coverage-admission-projection-form)))))

(0011 encoder-coverage-partial-reason
  "derived from structured Lisp admission; at least one admitted form maps to this pinned ICLASS; full XED operand/addressing coverage is not claimed")

(0011 encoder-coverage-legacy-form
  (100
    (110101001
      (110110111
        "knowledge/encoder-coverage-legacy-parity.lisp"))))

(0011 encoder-coverage-legacy-count
  (1001 (1001 encoder-coverage-legacy-form)))

(0011 encoder-coverage-legacy-successor-count
  (1001 (10011 encoder-coverage-legacy-form)))

(0011 encoder-coverage-legacy-pairs
  (011 (011 (011 encoder-coverage-legacy-form))))


; Both generated inputs share the same canonical ICLASS/extension order.
; Equality is enough: on mismatch advance the admitted index; an out-of-order
; or stale partial remains unconsumed and fails closed at index exhaustion.
(0011 encoder-coverage-row-key=?
  (0010 (left right)
    (encoder-coverage-all?
      (1110
        (encoder-coverage-same? (1001 left) (1001 right))
        (encoder-coverage-same? (10011 left) (10011 right))))))

(0011 encoder-coverage-not-yet-reason
  (0010 (extension)
    (110
      ((encoder-coverage-member? extension (001 (AVX AVX2 FMA3 BMI1 BMI2 F16C)))
       "VEX-prefix encoding not yet implemented")
      ((encoder-coverage-same? extension (001 X87))
       "x87 stack-register encoding not yet implemented")
      ((encoder-coverage-same? extension (001 MMX))
       "MMX opcode-map encoding not yet implemented")
      ((encoder-coverage-member?
         extension
         (001 (SSE SSE2 SSE3 SSSE3 SSE4.1+SSE4.2)))
       "legacy SSE mandatory-prefix/ModRM encoding not yet implemented")
      ((encoder-coverage-member? extension (001 (AES-NI PCLMULQDQ)))
       "SSE-prefixed crypto encoding not yet implemented")
      ((encoder-coverage-same? extension (001 XSAVE))
       "XSAVE control-state encoding not yet implemented")
      ((encoder-coverage-same? extension (001 MPX))
       "BND-register encoding not yet implemented")
      ((encoder-coverage-same? extension (001 SGX))
       "ENCLS/ENCLU leaf-function encoding not yet implemented")
      ((encoder-coverage-member? extension (001 (RDRAND RDSEED)))
       "0F C7 opcode-map encoding not yet implemented")
      ((encoder-coverage-same? extension (001 CLFLUSHOPT))
       "cache-management opcode encoding not yet implemented")
      ((encoder-coverage-same? extension (001 X86-64))
       "long-mode-specific BASE forms pending family-by-family rollout")
      (encoder-coverage-d1-yes
       "remaining BASE forms pending family-by-family rollout"))))

(0011 encoder-coverage-render-row
  (0010 (row partial)
    (001001 ((extension (1001 row))
           (iclass (10011 row))
           (status
             (110
               ((encoder-coverage-empty? partial) (001 not-yet-implemented))
               (encoder-coverage-d1-yes (001 partial))))
           (підстава
             (110
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
(0011 encoder-coverage-build-onto
  (0010 (index-rows partials rendered count)
    (110
      ((encoder-coverage-empty? index-rows)
       (110
         ((encoder-coverage-empty? partials)
          (1110 (10100 rendered) count encoder-coverage-d1-no))
         (encoder-coverage-d1-yes
          (1110 (10100 rendered) count encoder-coverage-d1-yes))))
      ((encoder-coverage-empty? partials)
       (encoder-coverage-build-onto
         (011 index-rows)
         partials
         (111
           (encoder-coverage-render-row (100 index-rows) (001 ()))
           rendered)
         count))
      (encoder-coverage-d1-yes
       (001000 ((index-row (100 index-rows))
             (partial-row (100 partials)))
         (110
           ((encoder-coverage-row-key=? index-row partial-row)
            (encoder-coverage-build-onto
              (011 index-rows)
              (011 partials)
              (111
                (encoder-coverage-render-row index-row partial-row)
                rendered)
              (01010 count #b1)))
           (encoder-coverage-d1-yes
            (encoder-coverage-build-onto
              (011 index-rows)
              partials
              (111
                (encoder-coverage-render-row index-row (001 ()))
                rendered)
              count))))))))

(0011 encoder-coverage-index-unique?
  (0010 (rows previous)
    (110
      ((encoder-coverage-empty? rows) encoder-coverage-d1-yes)
      ((encoder-coverage-empty? previous)
       (encoder-coverage-index-unique?
         (011 rows)
         (100 rows)))
      ((encoder-coverage-row-key=? (100 rows) previous)
       encoder-coverage-d1-no)
      (encoder-coverage-d1-yes
       (encoder-coverage-index-unique?
         (011 rows)
         (100 rows))))))

(0011 encoder-coverage-index-form
  (100
    (110101001
      (110110111
        "lib/machine/encoding/admitted-iclass-index.lisp"))))

(0011 encoder-coverage-index-count
  (1001 (1001 encoder-coverage-index-form)))

(0011 encoder-coverage-index-rows
  (011 (011 encoder-coverage-index-form)))

(0011 encoder-coverage-form-count
  (encoder-coverage-binary-length encoder-coverage-index-rows))

(0011 encoder-coverage-partials-valid?
  (0010 (index-rows partials)
    (110
      ((encoder-coverage-empty? partials) encoder-coverage-d1-yes)
      ((encoder-coverage-empty? index-rows) encoder-coverage-d1-no)
      (encoder-coverage-d1-yes
       (001000 ((index-row (100 index-rows))
             (partial-row (100 partials)))
         (110
           ((encoder-coverage-row-key=? index-row partial-row)
            (encoder-coverage-partials-valid?
              (011 index-rows)
              (011 partials)))
           (encoder-coverage-d1-yes
            (encoder-coverage-partials-valid?
              (011 index-rows)
              partials))))))))

(0011 encoder-coverage-index-checks
  (0010 ()
    (1110
      (1110 (001 admitted-head)
        (encoder-coverage-same? (100 encoder-coverage-index-form) (001 x86-admitted-iclass-index/2)))
      (1110 (001 admitted-count)
        (encoder-coverage-count=? encoder-coverage-index-count encoder-coverage-index-rows))
      (1110 (001 admitted-unique)
        (encoder-coverage-index-unique? encoder-coverage-index-rows (001 ())))
      (1110 (001 projection-head)
        (encoder-coverage-same? (100 encoder-coverage-admission-projection-form) (001 x86-admission-iclass-projection/1)))
      (1110 (001 projection-count)
        (encoder-coverage-count=? encoder-coverage-projection-partial-count encoder-coverage-partials))
      (1110 (001 projection-orphan-zero)
        (= encoder-coverage-projection-orphan-count #b0))
      (1110 (001 projection-subset)
        (encoder-coverage-partials-valid? encoder-coverage-index-rows encoder-coverage-partials))
      (1110 (001 legacy-head)
        (encoder-coverage-same? (100 encoder-coverage-legacy-form) (001 encoder-coverage-legacy-parity/1)))
      (1110 (001 legacy-count)
        (encoder-coverage-count=? encoder-coverage-legacy-count encoder-coverage-legacy-pairs))
      (1110 (001 legacy-successor-count)
        (encoder-coverage-count=? encoder-coverage-legacy-successor-count encoder-coverage-partials))
      (1110 (001 legacy-subset)
        (encoder-coverage-partials-valid? encoder-coverage-partials encoder-coverage-legacy-pairs)))))

(0011 encoder-coverage-index-valid?
  (0010 ()
    (encoder-coverage-all?
      (101000 1001 (encoder-coverage-index-checks)))))

(0011 encoder-coverage-committed-row-matches?
  (0010 (index-row coverage-row partial-row)
    (110
      ((encoder-coverage-empty? coverage-row) encoder-coverage-d1-no)
      ((encoder-coverage-count=? #b101 coverage-row)
       (001001 ((expected-status
                (110
                  ((encoder-coverage-empty? partial-row) (001 not-yet-implemented))
                  (encoder-coverage-d1-yes (001 partial))))
              (expected-reason
                (110
                  ((encoder-coverage-empty? partial-row) (encoder-coverage-not-yet-reason (1001 index-row)))
                  (encoder-coverage-d1-yes encoder-coverage-partial-reason))))
         (encoder-coverage-all?
           (1110
             (encoder-coverage-same? (100 coverage-row) (001 coverage))
             (encoder-coverage-same? (100 (1001 coverage-row)) (001 iclass))
             (encoder-coverage-same? (1001 (1001 coverage-row)) (10011 index-row))
             (encoder-coverage-same? (100 (10011 coverage-row)) (001 extension))
             (encoder-coverage-same? (1001 (10011 coverage-row)) (1001 index-row))
             (encoder-coverage-same? (100 (100111 coverage-row)) (001 status))
             (encoder-coverage-same? (1001 (100111 coverage-row)) expected-status)
             (encoder-coverage-same? (100 (110110101 coverage-row)) (100 (110101001 "reason")))
             (encoder-coverage-same? (1001 (110110101 coverage-row)) expected-reason)))))
      (encoder-coverage-d1-yes encoder-coverage-d1-no))))

(0011 encoder-coverage-projection-rows-valid?
  (0010 (index-rows coverage-rows partials)
    (110
      ((encoder-coverage-empty? index-rows)
       (110
         ((encoder-coverage-empty? coverage-rows)
          (110
            ((encoder-coverage-empty? partials)
             encoder-coverage-d1-yes)
            (encoder-coverage-d1-yes
             encoder-coverage-d1-no)))
         (encoder-coverage-d1-yes
          encoder-coverage-d1-no)))
      ((encoder-coverage-empty? coverage-rows)
       encoder-coverage-d1-no)
      ((encoder-coverage-empty? partials)
       (110
         ((encoder-coverage-committed-row-matches?
            (100 index-rows)
            (100 coverage-rows)
            (001 ()))
          (encoder-coverage-projection-rows-valid?
            (011 index-rows)
            (011 coverage-rows)
            partials))
         (encoder-coverage-d1-yes
          encoder-coverage-d1-no)))
      (encoder-coverage-d1-yes
       (001000 ((index-row (100 index-rows))
             (coverage-row (100 coverage-rows))
             (partial-row (100 partials)))
         (110
           ((encoder-coverage-row-key=? index-row partial-row)
            (110
              ((encoder-coverage-committed-row-matches?
                 index-row
                 coverage-row
                 partial-row)
               (encoder-coverage-projection-rows-valid?
                 (011 index-rows)
                 (011 coverage-rows)
                 (011 partials)))
              (encoder-coverage-d1-yes
               encoder-coverage-d1-no)))
           (encoder-coverage-d1-yes
            (110
              ((encoder-coverage-committed-row-matches?
                 index-row
                 coverage-row
                 (001 ()))
               (encoder-coverage-projection-rows-valid?
                 (011 index-rows)
                 (011 coverage-rows)
                 partials))
              (encoder-coverage-d1-yes
               encoder-coverage-d1-no)))))))))

(0011 encoder-coverage-projection-valid?
  (0010 (coverage-form)
    (110
      ((encoder-coverage-empty? coverage-form) encoder-coverage-d1-no)
      ((encoder-coverage-count=?
         encoder-coverage-index-count
         (011 (011 (011 coverage-form))))
       (encoder-coverage-all?
         (1110
           (encoder-coverage-same? (100 coverage-form) (001 x86-encoder-coverage/1))
           (encoder-coverage-same? (100 (1001 coverage-form)) (001 form-count))
           (= (1001 (1001 coverage-form)) encoder-coverage-form-count)
           (encoder-coverage-same? (100 (10011 coverage-form)) (001 partial-count))
           (= (1001 (10011 coverage-form)) encoder-coverage-projection-partial-count)
           (encoder-coverage-projection-rows-valid?
             encoder-coverage-index-rows
             (011 (011 (011 coverage-form)))
             encoder-coverage-partials))))
      (encoder-coverage-d1-yes encoder-coverage-d1-no))))

(0011 encoder-coverage-render
  (0010 ()
    (001001 ((build
             (encoder-coverage-build-onto
               encoder-coverage-index-rows
               encoder-coverage-partials
               (001 ())
               #b0))
           (rendered-rows (100 build))
           (partial-count (1001 build))
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
      (110
        (stale-partial?
         (001 ()))
        (encoder-coverage-d1-yes
         (encoder-coverage-str+
           prelude
           (encoder-coverage-balanced-concat rendered-rows)
           ")\n"))))))
