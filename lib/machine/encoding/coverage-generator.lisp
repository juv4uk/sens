; #604 — Lisp-owned encoder coverage authority.
; Inputs are generated, non-semantic machine projections:
;   pinned #175 (extension, ICLASS) index
;   structured Lisp admission -> partial ICLASS projection (#487/#2372)
; The old Rust 32-row classification is migration evidence only.

(def encoder-coverage-str+
  (lambda args
    (reduce (lambda (acc s) (string-append acc s)) "" args)))

; Render metadata counts with explicit binary source spelling.
(def encoder-coverage-binary-digits-onto
  (lambda (value acc)
    (cond
      ((< value #b10)
       (string-append (number->string value) acc))
      (t
       (encoder-coverage-binary-digits-onto
         (quotient value #b10)
         (string-append
           (number->string (mod value #b10))
           acc))))))

(def encoder-coverage-binary-literal
  (lambda (value)
    (string-append
      "#b"
      (encoder-coverage-binary-digits-onto value ""))))

; equal? is already the canonical Core4 structural predicate: (1) for YES,
; (0) for NO.  Keep the helper only as a local name; do not reintroduce the
; retired structural-relation/t compatibility layer.
(def encoder-coverage-same?
  (lambda (left right)
    ; equal? owns structural/deep equality and returns the historical
    ; one-bit answer list (1)/(0). Strict current D3 COND must not consume
    ; that compatibility list directly. Re-ask atom identity about its bit
    ; so this helper returns exact D1 PredicateBit.
    (eq? (car (equal? left right))
         (car (quote (1))))))

(def encoder-coverage-pair=?
  (lambda (left right)
    (encoder-coverage-same? left right)))

; Pairwise rounds form a rope-like balanced concatenation tree. This avoids
; copying an ever-growing ~200 KB accumulator once per emitted coverage row.
(def encoder-coverage-concat-round
  (lambda (strings acc)
    (cond
      ((atom strings) (reverse acc))
      ((atom (cdr strings))
       (reverse-onto acc (list (car strings))))
      (t
       (encoder-coverage-concat-round
         (cdr (cdr strings))
         (cons
           (string-append (car strings) (second strings))
           acc))))))

(def encoder-coverage-balanced-concat
  (lambda (strings)
    (cond
      ((atom strings) "")
      ((atom (cdr strings)) (car strings))
      (t
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


; Both index rows and partial rows use positions:
;   tag, extension, ICLASS, ...
; Compare by ICLASS first, then extension, matching the legacy coverage order.
(def encoder-coverage-row-key<?
  (lambda (left right)
    (let ((left-iclass (third left))
          (right-iclass (third right)))
      (cond
        ((string<? left-iclass right-iclass) t)
        ((encoder-coverage-same? left-iclass right-iclass)
         (string<?
           (symbol->string (second left))
           (symbol->string (second right))))
        (t (quote ()))))))

(def encoder-coverage-row-key=?
  (lambda (left right)
    (and
      (encoder-coverage-same? (second left) (second right))
      (encoder-coverage-same? (third left) (third right)))))

(def encoder-coverage-not-yet-reason
  (lambda (extension)
    (cond
      ((member? extension (quote (AVX AVX2 FMA3 BMI1 BMI2 F16C)))
       "VEX-prefix encoding not yet implemented")
      ((encoder-coverage-same? extension (quote X87))
       "x87 stack-register encoding not yet implemented")
      ((encoder-coverage-same? extension (quote MMX))
       "MMX opcode-map encoding not yet implemented")
      ((member?
         extension
         (quote (SSE SSE2 SSE3 SSSE3 SSE4.1+SSE4.2)))
       "legacy SSE mandatory-prefix/ModRM encoding not yet implemented")
      ((member? extension (quote (AES-NI PCLMULQDQ)))
       "SSE-prefixed crypto encoding not yet implemented")
      ((encoder-coverage-same? extension (quote XSAVE))
       "XSAVE control-state encoding not yet implemented")
      ((encoder-coverage-same? extension (quote MPX))
       "BND-register encoding not yet implemented")
      ((encoder-coverage-same? extension (quote SGX))
       "ENCLS/ENCLU leaf-function encoding not yet implemented")
      ((member? extension (quote (RDRAND RDSEED)))
       "0F C7 opcode-map encoding not yet implemented")
      ((encoder-coverage-same? extension (quote CLFLUSHOPT))
       "cache-management opcode encoding not yet implemented")
      ((encoder-coverage-same? extension (quote X86-64))
       "long-mode-specific BASE forms pending family-by-family rollout")
      (t
       "remaining BASE forms pending family-by-family rollout"))))

(def encoder-coverage-render-row
  (lambda (row partial)
    (let* ((extension (second row))
           (iclass (third row))
           (status
             (cond
               ((atom partial) (quote not-yet-implemented))
               (t (quote partial))))
           (reason
             (cond
               ((atom partial)
                (encoder-coverage-not-yet-reason extension))
               (t encoder-coverage-partial-reason))))
      (encoder-coverage-str+
        "  (coverage\n"
        "    (iclass " (write-to-string iclass) ")\n"
        "    (extension " (symbol->string extension) ")\n"
        "    (status " (symbol->string status) ")\n"
        "    (reason " (write-to-string reason) "))\n"))))

; One tail-recursive merge performs classification, stale-partial detection,
; rendering and partial counting. No 1175×32 repeated lookup remains.
; Result = (rendered-rows partial-count stale-partial?).
(def encoder-coverage-build-onto
  (lambda (index-rows partials rendered count)
    (cond
      ((atom index-rows)
       (cond
         ((atom partials)
          (list (reverse rendered) count (quote ())))
         (t
          (list (reverse rendered) count t))))
      ((atom partials)
       (encoder-coverage-build-onto
         (cdr index-rows)
         partials
         (cons
           (encoder-coverage-render-row (car index-rows) (quote ()))
           rendered)
         count))
      (t
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
              (+ count #b1)))
           ((encoder-coverage-row-key<? partial-row index-row)
            ; A claimed partial sorts before the next admitted row: it is
            ; absent/stale or the partial inventory is non-deterministic.
            (list (reverse rendered) count t))
           (t
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
      ((atom rows) t)
      ((atom previous)
       (encoder-coverage-index-unique?
         (cdr rows)
         (car rows)))
      ((encoder-coverage-row-key=? (car rows) previous)
       (quote ()))
      (t
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
      ((atom partials) t)
      ((atom index-rows) (quote ()))
      (t
       (let ((index-row (car index-rows))
             (partial-row (car partials)))
         (cond
           ((encoder-coverage-row-key=? index-row partial-row)
            (encoder-coverage-partials-valid?
              (cdr index-rows)
              (cdr partials)))
           ((encoder-coverage-row-key<? partial-row index-row)
            (quote ()))
           (t
            (encoder-coverage-partials-valid?
              (cdr index-rows)
              partials))))))))

(def encoder-coverage-index-valid?
  (and
    (encoder-coverage-same?
      (car encoder-coverage-index-form)
      (quote x86-admitted-iclass-index/2))
    (encoder-coverage-same?
      encoder-coverage-form-count
      encoder-coverage-index-count)
    (encoder-coverage-index-unique?
      encoder-coverage-index-rows
      (quote ()))
    (encoder-coverage-same?
      (car encoder-coverage-admission-projection-form)
      (quote x86-admission-iclass-projection/1))
    (encoder-coverage-same?
      encoder-coverage-projection-partial-count
      (length encoder-coverage-partials))
    (encoder-coverage-same?
      encoder-coverage-projection-orphan-count
      #b0)
    (encoder-coverage-partials-valid?
      encoder-coverage-index-rows
      encoder-coverage-partials)
    (encoder-coverage-same?
      (car encoder-coverage-legacy-form)
      (quote encoder-coverage-legacy-parity/1))
    (encoder-coverage-same?
      encoder-coverage-legacy-count
      (length encoder-coverage-legacy-pairs))
    (encoder-coverage-same?
      encoder-coverage-legacy-successor-count
      (length encoder-coverage-partials))
    (encoder-coverage-partials-valid?
      encoder-coverage-partials
      encoder-coverage-legacy-pairs)))

(def encoder-coverage-committed-row-matches?
  (lambda (index-row coverage-row partial-row)
    (cond
      ((atom coverage-row) (quote ()))
      ((equal? (length coverage-row) #b101)
       (let* ((expected-status
                (cond
                  ((atom partial-row) (quote not-yet-implemented))
                  (t (quote partial))))
              (expected-reason
                (cond
                  ((atom partial-row)
                   (encoder-coverage-not-yet-reason
                     (second index-row)))
                  (t encoder-coverage-partial-reason))))
         (and
           (encoder-coverage-same?
             (car coverage-row)
             (quote coverage))
           (encoder-coverage-same?
             (car (second coverage-row))
             (quote iclass))
           (encoder-coverage-same?
             (second (second coverage-row))
             (third index-row))
           (encoder-coverage-same?
             (car (third coverage-row))
             (quote extension))
           (encoder-coverage-same?
             (second (third coverage-row))
             (second index-row))
           (encoder-coverage-same?
             (car (fourth coverage-row))
             (quote status))
           (encoder-coverage-same?
             (second (fourth coverage-row))
             expected-status)
           (encoder-coverage-same?
             (car (fifth coverage-row))
             (quote reason))
           (encoder-coverage-same?
             (second (fifth coverage-row))
             expected-reason))))
      (t (quote ())))))

(def encoder-coverage-projection-rows-valid?
  (lambda (index-rows coverage-rows partials)
    (cond
      ((atom index-rows)
       (and (atom coverage-rows) (atom partials)))
      ((atom coverage-rows)
       (quote ()))
      ((atom partials)
       (and
         (encoder-coverage-committed-row-matches?
           (car index-rows)
           (car coverage-rows)
           (quote ()))
         (encoder-coverage-projection-rows-valid?
           (cdr index-rows)
           (cdr coverage-rows)
           partials)))
      (t
       (let ((index-row (car index-rows))
             (coverage-row (car coverage-rows))
             (partial-row (car partials)))
         (cond
           ((encoder-coverage-row-key=? index-row partial-row)
            (and
              (encoder-coverage-committed-row-matches?
                index-row
                coverage-row
                partial-row)
              (encoder-coverage-projection-rows-valid?
                (cdr index-rows)
                (cdr coverage-rows)
                (cdr partials))))
           ((encoder-coverage-row-key<? partial-row index-row)
            (quote ()))
           (t
            (and
              (encoder-coverage-committed-row-matches?
                index-row
                coverage-row
                (quote ()))
              (encoder-coverage-projection-rows-valid?
                (cdr index-rows)
                (cdr coverage-rows)
                partials)))))))))

(def encoder-coverage-projection-valid?
  (lambda (coverage-form)
    (cond
      ((atom coverage-form) (quote ()))
      ((equal? (length coverage-form) (+ encoder-coverage-form-count #b11))
       (and
         (encoder-coverage-same?
           (car coverage-form)
           (quote x86-encoder-coverage/1))
         (encoder-coverage-same?
           (car (second coverage-form))
           (quote form-count))
         (encoder-coverage-same?
           (second (second coverage-form))
           encoder-coverage-form-count)
         (encoder-coverage-same?
           (car (third coverage-form))
           (quote partial-count))
         (encoder-coverage-same?
           (second (third coverage-form))
           (length encoder-coverage-partials))
         (encoder-coverage-projection-rows-valid?
           encoder-coverage-index-rows
           (cdr (cdr (cdr coverage-form)))
           encoder-coverage-partials)))
      (t (quote ())))))

(def encoder-coverage-render
  (lambda ()
    (let* ((build
             (encoder-coverage-build-onto
               encoder-coverage-index-rows
               encoder-coverage-partials
               (quote ())
               #b0))
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
        ((encoder-coverage-same? stale-partial? t)
         (quote ()))
        (t
         (encoder-coverage-str+
           prelude
           (encoder-coverage-balanced-concat rendered-rows)
           ")\n"))))))
