; #604 — Lisp-owned encoder coverage authority.
; Inputs are generated, non-semantic machine projections:
;   pinned #175 (extension, ICLASS) index
;   structured Lisp admission -> partial ICLASS projection (#487/#2372)
; The old Rust 32-row classification is migration evidence only.

(def encoder-coverage-str+
  (lambda args
    (reduce (lambda (acc s) (string-append acc s)) "" args)))

; Render ordinary cardinality Numbers with explicit binary source spelling.
; Radix 2 is intentionally an ordinary Number here: #b10 is the distinct
; BinaryNumber carrier that this serializer is producing, not an arithmetic
; constant to be implicitly mixed into the input Number domain.
(def encoder-coverage-binary-digits-onto
  (lambda (value acc)
    (cond
      ((< value 2)
       (string-append (number->string value) acc))
      (encoder-coverage-d1-yes
       (encoder-coverage-binary-digits-onto
         (quotient value 2)
         (string-append
           (number->string (mod value 2))
           acc))))))

(def encoder-coverage-binary-literal
  (lambda (value)
    (string-append
      "#b"
      (encoder-coverage-binary-digits-onto value ""))))

(def encoder-coverage-count-as-binary
  (lambda (value)
    (car
      (read-all
        (encoder-coverage-binary-literal value)))))


; Coverage authority uses exact D1 PredicateBit for every control decision.
; Deep structural equality is Lisp-owned here and is built only from current
; exact D3 laws: ATOM classifies pair-vs-atom and EQ compares admitted atoms.
; Historical deep-equality carriers do not cross into the authority path.
(def encoder-coverage-d1-yes
  (тотожне? (quote encoder-coverage-yes) (quote encoder-coverage-yes)))

(def encoder-coverage-d1-no
  (тотожне? (quote encoder-coverage-yes) (quote encoder-coverage-no)))

(def encoder-coverage-same?
  (lambda (left right)
    (cond
      ((атом? left)
       (cond
         ((атом? right)
          (тотожне? left right))
         (encoder-coverage-d1-yes
          encoder-coverage-d1-no)))
      ((атом? right)
       encoder-coverage-d1-no)
      ((encoder-coverage-same? (car left) (car right))
       (encoder-coverage-same? (cdr left) (cdr right)))
      (encoder-coverage-d1-yes
       encoder-coverage-d1-no))))

; Traversal needs structural EMPTY, not the broader ATOM classification.
; This preserves the D1:0 != D3:000 distinction and avoids using ATOM as NIL.
(def encoder-coverage-empty?
  (lambda (value)
    (encoder-coverage-same? value (quote ()))))

(def encoder-coverage-count=?
  (lambda (binary-count observed-count)
    (= binary-count
       (encoder-coverage-count-as-binary observed-count))))


; Conjunction over already-admitted predicate answers. Structural EMPTY is
; only no-witness/non-selection; no generic T/NIL truthiness is consulted.
(def encoder-coverage-all?
  (lambda (answers)
    (cond
      ((encoder-coverage-empty? answers)
       encoder-coverage-d1-yes)
      ((car answers)
       (encoder-coverage-all? (cdr answers)))
      (encoder-coverage-d1-yes
       encoder-coverage-d1-no))))

(def encoder-coverage-pair=?
  (lambda (left right)
    (encoder-coverage-same? left right)))
(def encoder-coverage-member?
  (lambda (item values)
    (cond
      ((encoder-coverage-empty? values) encoder-coverage-d1-no)
      ((encoder-coverage-same? item (car values))
       encoder-coverage-d1-yes)
      (encoder-coverage-d1-yes
       (encoder-coverage-member? item (cdr values))))))

; Pairwise rounds form a rope-like balanced concatenation tree. This avoids
; copying an ever-growing ~200 KB accumulator once per emitted coverage row.
(def encoder-coverage-concat-round
  (lambda (strings acc)
    (cond
      ((encoder-coverage-empty? strings) (reverse acc))
      ((encoder-coverage-empty? (cdr strings))
       (reverse-onto acc (list (car strings))))
      (encoder-coverage-d1-yes
       (encoder-coverage-concat-round
         (cdr (cdr strings))
         (cons
           (string-append (car strings) (second strings))
           acc))))))

(def encoder-coverage-balanced-concat
  (lambda (strings)
    (cond
      ((encoder-coverage-empty? strings) "")
      ((encoder-coverage-empty? (cdr strings)) (car strings))
      (encoder-coverage-d1-yes
       (encoder-coverage-balanced-concat
         (encoder-coverage-concat-round
           strings
           (quote ())))))))

(def encoder-coverage-admission-projection-form
  (car
    (read-all
      (read-file
        "lib/machine/encoding/admission-iclass-projection.lisp"))))

(def encoder-coverage-projection-head-count
  (second (second encoder-coverage-admission-projection-form)))

(def encoder-coverage-projection-partial-count
  (second (third encoder-coverage-admission-projection-form)))

(def encoder-coverage-projection-orphan-count
  (second (fourth encoder-coverage-admission-projection-form)))

(def encoder-coverage-partials
  (cdr
    (cdr
      (cdr
        (cdr encoder-coverage-admission-projection-form)))))

(def encoder-coverage-partial-reason
  "derived from structured Lisp admission; at least one admitted form maps to this pinned ICLASS; full XED operand/addressing coverage is not claimed")

(def encoder-coverage-legacy-form
  (car
    (read-all
      (read-file
        "knowledge/encoder-coverage-legacy-parity.lisp"))))

(def encoder-coverage-legacy-count
  (second (second encoder-coverage-legacy-form)))

(def encoder-coverage-legacy-successor-count
  (second (third encoder-coverage-legacy-form)))

(def encoder-coverage-legacy-pairs
  (cdr (cdr (cdr encoder-coverage-legacy-form))))


; Both generated inputs share the same canonical ICLASS/extension order.
; Equality is enough: on mismatch advance the admitted index; an out-of-order
; or stale partial remains unconsumed and fails closed at index exhaustion.
(def encoder-coverage-row-key=?
  (lambda (left right)
    (encoder-coverage-all?
      (list
        (encoder-coverage-same? (second left) (second right))
        (encoder-coverage-same? (third left) (third right))))))

(def encoder-coverage-not-yet-reason
  (lambda (extension)
    (cond
      ((encoder-coverage-member? extension (quote (AVX AVX2 FMA3 BMI1 BMI2 F16C)))
       "VEX-prefix encoding not yet implemented")
      ((encoder-coverage-same? extension (quote X87))
       "x87 stack-register encoding not yet implemented")
      ((encoder-coverage-same? extension (quote MMX))
       "MMX opcode-map encoding not yet implemented")
      ((encoder-coverage-member?
         extension
         (quote (SSE SSE2 SSE3 SSSE3 SSE4.1+SSE4.2)))
       "legacy SSE mandatory-prefix/ModRM encoding not yet implemented")
      ((encoder-coverage-member? extension (quote (AES-NI PCLMULQDQ)))
       "SSE-prefixed crypto encoding not yet implemented")
      ((encoder-coverage-same? extension (quote XSAVE))
       "XSAVE control-state encoding not yet implemented")
      ((encoder-coverage-same? extension (quote MPX))
       "BND-register encoding not yet implemented")
      ((encoder-coverage-same? extension (quote SGX))
       "ENCLS/ENCLU leaf-function encoding not yet implemented")
      ((encoder-coverage-member? extension (quote (RDRAND RDSEED)))
       "0F C7 opcode-map encoding not yet implemented")
      ((encoder-coverage-same? extension (quote CLFLUSHOPT))
       "cache-management opcode encoding not yet implemented")
      ((encoder-coverage-same? extension (quote X86-64))
       "long-mode-specific BASE forms pending family-by-family rollout")
      (encoder-coverage-d1-yes
       "remaining BASE forms pending family-by-family rollout"))))

(def encoder-coverage-render-row
  (lambda (row partial)
    (let* ((extension (second row))
           (iclass (third row))
           (status
             (cond
               ((encoder-coverage-empty? partial) (quote not-yet-implemented))
               (encoder-coverage-d1-yes (quote partial))))
           (reason
             (cond
               ((encoder-coverage-empty? partial)
                (encoder-coverage-not-yet-reason extension))
               (encoder-coverage-d1-yes encoder-coverage-partial-reason))))
      (encoder-coverage-str+
        "  (coverage\n"
        "    (iclass " (write-to-string iclass) ")\n"
        "    (extension " (symbol->string extension) ")\n"
        "    (status " (symbol->string status) ")\n"
        "    (reason " (write-to-string reason) "))\n"))))

; One tail-recursive ordered-subset merge performs classification,
; stale-partial detection, rendering and partial counting.
; Result = (rendered-rows partial-count exact-D1-stale-partial?).
(def encoder-coverage-build-onto
  (lambda (index-rows partials rendered count)
    (cond
      ((encoder-coverage-empty? index-rows)
       (cond
         ((encoder-coverage-empty? partials)
          (list (reverse rendered) count encoder-coverage-d1-no))
         (encoder-coverage-d1-yes
          (list (reverse rendered) count encoder-coverage-d1-yes))))
      ((encoder-coverage-empty? partials)
       (encoder-coverage-build-onto
         (cdr index-rows)
         partials
         (cons
           (encoder-coverage-render-row (car index-rows) (quote ()))
           rendered)
         count))
      (encoder-coverage-d1-yes
       (let ((index-row (car index-rows))
             (partial-row (car partials)))
         (cond
           ((encoder-coverage-row-key=? index-row partial-row)
            (encoder-coverage-build-onto
              (cdr index-rows)
              (cdr partials)
              (cons
                (encoder-coverage-render-row index-row partial-row)
                rendered)
              (+ count 1)))
           (encoder-coverage-d1-yes
            (encoder-coverage-build-onto
              (cdr index-rows)
              partials
              (cons
                (encoder-coverage-render-row index-row (quote ()))
                rendered)
              count))))))))

(def encoder-coverage-index-unique?
  (lambda (rows previous)
    (cond
      ((encoder-coverage-empty? rows) encoder-coverage-d1-yes)
      ((encoder-coverage-empty? previous)
       (encoder-coverage-index-unique?
         (cdr rows)
         (car rows)))
      ((encoder-coverage-row-key=? (car rows) previous)
       encoder-coverage-d1-no)
      (encoder-coverage-d1-yes
       (encoder-coverage-index-unique?
         (cdr rows)
         (car rows))))))

(def encoder-coverage-index-form
  (car
    (read-all
      (read-file
        "lib/machine/encoding/admitted-iclass-index.lisp"))))

(def encoder-coverage-index-count
  (second (second encoder-coverage-index-form)))

(def encoder-coverage-index-rows
  (cdr (cdr encoder-coverage-index-form)))

(def encoder-coverage-form-count
  (length encoder-coverage-index-rows))

(def encoder-coverage-partials-valid?
  (lambda (index-rows partials)
    (cond
      ((encoder-coverage-empty? partials) encoder-coverage-d1-yes)
      ((encoder-coverage-empty? index-rows) encoder-coverage-d1-no)
      (encoder-coverage-d1-yes
       (let ((index-row (car index-rows))
             (partial-row (car partials)))
         (cond
           ((encoder-coverage-row-key=? index-row partial-row)
            (encoder-coverage-partials-valid?
              (cdr index-rows)
              (cdr partials)))
           (encoder-coverage-d1-yes
            (encoder-coverage-partials-valid?
              (cdr index-rows)
              partials))))))))

(def encoder-coverage-index-checks
  (lambda ()
    (list
      (list (quote admitted-head)
        (encoder-coverage-same? (car encoder-coverage-index-form) (quote x86-admitted-iclass-index/2)))
      (list (quote admitted-count)
        (encoder-coverage-count=? encoder-coverage-index-count encoder-coverage-form-count))
      (list (quote admitted-unique)
        (encoder-coverage-index-unique? encoder-coverage-index-rows (quote ())))
      (list (quote projection-head)
        (encoder-coverage-same? (car encoder-coverage-admission-projection-form) (quote x86-admission-iclass-projection/1)))
      (list (quote projection-count)
        (encoder-coverage-count=? encoder-coverage-projection-partial-count (length encoder-coverage-partials)))
      (list (quote projection-orphan-zero)
        (= encoder-coverage-projection-orphan-count #b0))
      (list (quote projection-subset)
        (encoder-coverage-partials-valid? encoder-coverage-index-rows encoder-coverage-partials))
      (list (quote legacy-head)
        (encoder-coverage-same? (car encoder-coverage-legacy-form) (quote encoder-coverage-legacy-parity/1)))
      (list (quote legacy-count)
        (encoder-coverage-count=? encoder-coverage-legacy-count (length encoder-coverage-legacy-pairs)))
      (list (quote legacy-successor-count)
        (encoder-coverage-count=? encoder-coverage-legacy-successor-count (length encoder-coverage-partials)))
      (list (quote legacy-subset)
        (encoder-coverage-partials-valid? encoder-coverage-partials encoder-coverage-legacy-pairs)))))

(def encoder-coverage-index-valid?
  (lambda ()
    (encoder-coverage-all?
      (map second (encoder-coverage-index-checks)))))

(def encoder-coverage-committed-row-matches?
  (lambda (index-row coverage-row partial-row)
    (cond
      ((encoder-coverage-empty? coverage-row) encoder-coverage-d1-no)
      ((encoder-coverage-count=? #b101 (length coverage-row))
       (let* ((expected-status
                (cond
                  ((encoder-coverage-empty? partial-row) (quote not-yet-implemented))
                  (encoder-coverage-d1-yes (quote partial))))
              (expected-reason
                (cond
                  ((encoder-coverage-empty? partial-row) (encoder-coverage-not-yet-reason (second index-row)))
                  (encoder-coverage-d1-yes encoder-coverage-partial-reason))))
         (encoder-coverage-all?
           (list
             (encoder-coverage-same? (car coverage-row) (quote coverage))
             (encoder-coverage-same? (car (second coverage-row)) (quote iclass))
             (encoder-coverage-same? (second (second coverage-row)) (third index-row))
             (encoder-coverage-same? (car (third coverage-row)) (quote extension))
             (encoder-coverage-same? (second (third coverage-row)) (second index-row))
             (encoder-coverage-same? (car (fourth coverage-row)) (quote status))
             (encoder-coverage-same? (second (fourth coverage-row)) expected-status)
             (encoder-coverage-same? (car (fifth coverage-row)) (quote reason))
             (encoder-coverage-same? (second (fifth coverage-row)) expected-reason)))))
      (encoder-coverage-d1-yes encoder-coverage-d1-no))))

(def encoder-coverage-projection-rows-valid?
  (lambda (index-rows coverage-rows partials)
    (cond
      ((encoder-coverage-empty? index-rows)
       (encoder-coverage-all? (list (encoder-coverage-empty? coverage-rows) (encoder-coverage-empty? partials))))
      ((encoder-coverage-empty? coverage-rows) encoder-coverage-d1-no)
      ((encoder-coverage-empty? partials)
       (encoder-coverage-all?
         (list
           (encoder-coverage-committed-row-matches? (car index-rows) (car coverage-rows) (quote ()))
           (encoder-coverage-projection-rows-valid? (cdr index-rows) (cdr coverage-rows) partials))))
      (encoder-coverage-d1-yes
       (let ((index-row (car index-rows))
             (coverage-row (car coverage-rows))
             (partial-row (car partials)))
         (cond
           ((encoder-coverage-row-key=? index-row partial-row)
            (encoder-coverage-all?
              (list
                (encoder-coverage-committed-row-matches? index-row coverage-row partial-row)
                (encoder-coverage-projection-rows-valid? (cdr index-rows) (cdr coverage-rows) (cdr partials)))))
           (encoder-coverage-d1-yes
            (encoder-coverage-all?
              (list
                (encoder-coverage-committed-row-matches? index-row coverage-row (quote ()))
                (encoder-coverage-projection-rows-valid? (cdr index-rows) (cdr coverage-rows) partials))))))))))

(def encoder-coverage-projection-valid?
  (lambda (coverage-form)
    (cond
      ((encoder-coverage-empty? coverage-form) encoder-coverage-d1-no)
      ((encoder-coverage-count=?
         encoder-coverage-index-count
         (length (cdr (cdr (cdr coverage-form)))))
       (encoder-coverage-all?
         (list
           (encoder-coverage-same? (car coverage-form) (quote x86-encoder-coverage/1))
           (encoder-coverage-same? (car (second coverage-form)) (quote form-count))
           (encoder-coverage-count=? (second (second coverage-form)) encoder-coverage-form-count)
           (encoder-coverage-same? (car (third coverage-form)) (quote partial-count))
           (encoder-coverage-count=? (second (third coverage-form)) (length encoder-coverage-partials))
           (encoder-coverage-projection-rows-valid?
             encoder-coverage-index-rows
             (cdr (cdr (cdr coverage-form)))
             encoder-coverage-partials))))
      (encoder-coverage-d1-yes encoder-coverage-d1-no))))

(def encoder-coverage-render
  (lambda ()
    (let* ((build
             (encoder-coverage-build-onto
               encoder-coverage-index-rows
               encoder-coverage-partials
               (quote ())
               0))
           (rendered-rows (car build))
           (partial-count (second build))
           (stale-partial? (third build))
           (prelude
             (encoder-coverage-str+
               "; GENERATED by `sens scripts/generate-encoder-coverage.lisp` -- do not hand-edit.\n"
               "; Sources: pinned #175 admitted ICLASS index + structured Lisp admission projection.\n"
               "; Every pinned (extension, ICLASS) pair appears exactly once. `partial` means at\n"
               "; least one structured admitted form is executable; it does not claim complete\n"
               "; coverage of every XED operand/addressing form. No silent third status (#176/#604).\n"
               "\n"
               "(x86-encoder-coverage/1\n"
               "  (form-count " (encoder-coverage-binary-literal encoder-coverage-form-count) ")\n"
               "  (partial-count " (encoder-coverage-binary-literal partial-count) ")\n")))
      (cond
        (stale-partial?
         (quote ()))
        (encoder-coverage-d1-yes
         (encoder-coverage-str+
           prelude
           (encoder-coverage-balanced-concat rendered-rows)
           ")\n"))))))
