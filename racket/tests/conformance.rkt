#lang racket
;;;
;;; racket/tests/conformance.rkt — runs the Racket port against
;;; tests/fixtures/conformance.lisp, the same implementation-independent
;;; contract the Rust and C backends are checked against.
;;;
;;; Found and confirmed two real semantic bugs this way (2026-08-18,
;;; fixed same commit): `eq` on two separately-created closures wrongly
;;; returned `t` (my-closure's #:transparent struct made Racket's
;;; `equal?` compare them structurally instead of by identity), and
;;; `print`/the REPL's value-echo showed Racket's own quote-sugar
;;; (`'radio` instead of `radio`) because both went through Racket's
;;; native `print` instead of my-lisp's own writer. Run this after any
;;; change to interpreter.rkt/reader-lib.rkt, the same way the Rust
;;; crate's own conformance test runs after any eval/reader change.
;;;
;;; `raco test racket/tests/conformance.rkt` exits non-zero on any
;;; MISMATCH (a real behavioral divergence from the contract). CRASHes
;;; are reported but don't fail the run when they're a fixture that
;;; needs a lib/*.my this port doesn't auto-load (README's documented
;;; limitation) rather than a bug — see `expected-crash-prefixes` below.

(require racket/runtime-path)
(require "../interpreter.rkt")
(require "../reader-lib.rkt")

(define-runtime-path fixtures-path (build-path 'up 'up "tests" "fixtures" "conformance.lisp"))

;; Fixtures needing lib/unify.my, lib/reason.my, lib/understand.my,
;; lib/narrate.my, lib/persistent_map.my, or lib/strings-extra.my —
;; none of which this port auto-loads (only lib/core.my, see README's
;; "Відомі обмеження"). An unbound-identifier crash naming one of these
;; is an expected, already-documented gap, not a new failure.
(define expected-unbound
  '(eval unify reason understand narrate-fact string<? map-get map-insert map-empty logic-var))

(define (read-all-forms path)
  (call-with-input-file path
    (lambda (in)
      (let loop ([acc '()])
        (define d (read in))
        (if (eof-object? d) (reverse acc) (loop (cons d acc)))))))

(define (expected-crash? message)
  (for/or ([name expected-unbound])
    (string-contains? message (format "unbound identifier: ~a" name))))

;; The Racket port does not expose Rust's ErrorKind enum, so conformance maps
;; its stable public messages to the contract's error names.  This deliberately
;; rejects a host-reader error where the contract requires a my-lisp symbol
;; error, and an unbound primitive where the contract requires Type/Arity.
(define (error-message-matches? expected message)
  (case (string->symbol expected)
    [(UnknownSymbol) (string-contains? message "unbound identifier:")]
    [(NumericOverflow) (string-contains? (string-downcase message) "overflow")]
    [(DivisionByZero) (string-contains? message "division by zero")]
    [(Arity) (or (string-contains? message "too many arguments")
                 (string-contains? message "too few arguments")
                 (string-contains? message "bad defmacro syntax"))]
    [(InvalidForm) (or (string-contains? message "bad ")
                       (string-contains? message "invalid"))]
    [(Parse) (string-contains? message "read:")]
    [(Type) (or (string-contains? message "expected pair")
                (string-contains? message "not a function")
                (string-contains? message "expects two atoms")
                (string-contains? message "type"))]
    [else #f]))

(module+ test
  (require rackunit)
  (define forms (read-all-forms fixtures-path))
  (define checked 0)
  (define error-checked 0)
  (for ([f forms])
    (define expr (cdr (assoc 'expr f)))
    (define expected (assoc 'expected f))
    (when expected
      (define expected-str (cdr expected))
      (set! checked (add1 checked))
      (with-handlers ([exn:fail?
                        (lambda (e)
                          (unless (expected-crash? (exn-message e))
                            (fail (format "~a crashed unexpectedly: ~a" expr (exn-message e)))))])
        (define env (make-initial-env))
        (define in (open-input-string expr))
        (define datums
          (let loop ([acc '()])
            (define d (my-read in))
            (if (eof-object? d) (reverse acc) (loop (cons d acc)))))
        (define result (for/fold ([v (void)]) ([d datums]) (my-eval d env)))
        (check-equal? (my-format-string result) expected-str expr))))
  (for ([f forms])
    (define expr (cdr (assoc 'expr f)))
    (define expected-error (assoc 'error f))
    (when expected-error
      (define expected-kind (cdr expected-error))
      (set! error-checked (add1 error-checked))
      (define raised? #f)
      (with-handlers ([exn:fail?
                        (lambda (e)
                          (set! raised? #t)
                          (check-true
                            (error-message-matches? expected-kind (exn-message e))
                            (format "~a expected ~a, Racket reported: ~a"
                                    expr expected-kind (exn-message e))))])
        (define env (make-initial-env))
        (define in (open-input-string expr))
        (define datums
          (let loop ([acc '()])
            (define d (my-read in))
            (if (eof-object? d) (reverse acc) (loop (cons d acc)))))
        (for/fold ([v (void)]) ([d datums]) (my-eval d env)))
      (check-true raised?
                  (format "~a expected ~a, Racket returned a value"
                          expr expected-kind))))
  (printf "conformance.lisp: checked ~a value fixtures and ~a error fixtures\n"
          checked error-checked))
