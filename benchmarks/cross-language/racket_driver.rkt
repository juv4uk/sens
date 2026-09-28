#lang racket/base
;; #1548: matched Racket CS phase driver for the shared cross-language harness.
;;
;; Source files are plain named modules.  The phases mirror the CPython driver:
;;   load   = read + compile module, do not instantiate it;
;;   ready  = load + instantiate definitions, do not call bench;
;;   repeat = ready + call bench N times;
;;   full   = ready + call bench once and print the result.

(define argv (current-command-line-arguments))

(unless (or (= (vector-length argv) 2)
            (= (vector-length argv) 3))
  (error 'racket-driver
         "usage: racket_driver.rkt PROGRAM.rkt load|ready|full|repeat [REPEATS]"))

(define path (vector-ref argv 0))
(define mode (vector-ref argv 1))

(define (compile-module source-path ns)
  (parameterize ([current-namespace ns])
    (call-with-input-file source-path
      (lambda (in)
        (compile (read-syntax source-path in))))))

(define (prepare source-path)
  (define ns (make-base-namespace))
  (define compiled (compile-module source-path ns))
  (values ns compiled))

(define-values (ns compiled) (prepare path))

(cond
  [(string=? mode "load")
   (void compiled)]

  [else
   (parameterize ([current-namespace ns])
     ;; Evaluating a compiled module declaration registers it in this namespace.
     (eval compiled)
     ;; Instantiation runs definitions but not bench.
     (dynamic-require ''sens-cross-bench #f)

     (cond
       [(string=? mode "ready")
        (void)]

       [(string=? mode "full")
        (define bench (dynamic-require ''sens-cross-bench 'bench))
        (displayln (bench))]

       [(string=? mode "repeat")
        (unless (= (vector-length argv) 3)
          (error 'racket-driver "repeat mode requires REPEATS"))
        (define repeats
          (string->number (vector-ref argv 2)))
        (unless (and (exact-integer? repeats) (> repeats 0))
          (error 'racket-driver "REPEATS must be a positive integer"))
        (define bench (dynamic-require ''sens-cross-bench 'bench))
        (define sink #f)
        (for ([i (in-range repeats)])
          (set! sink (bench)))
        (void sink)]

       [else
        (error 'racket-driver "unknown mode: ~a" mode)]))])
