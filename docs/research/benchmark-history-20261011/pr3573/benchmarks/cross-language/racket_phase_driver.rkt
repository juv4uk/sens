#lang racket/base
;; #1548 phase driver for Racket CS source compile/instantiate.

(define argv (current-command-line-arguments))
(unless (or (= (vector-length argv) 2) (= (vector-length argv) 3))
  (error 'usage "racket_phase_driver.rkt PROGRAM load|ready|repeat|full [REPEATS]"))

(define path (vector-ref argv 0))
(define mode (vector-ref argv 1))
(define repeats
  (if (= (vector-length argv) 3)
      (string->number (vector-ref argv 2))
      1))

(define (read-program p)
  (call-with-input-file p
    (lambda (in)
      (let loop ([forms '()])
        (define form (read in))
        (if (eof-object? form)
            (reverse forms)
            (loop (cons form forms)))))))

(define ns (make-base-namespace))

(define (compile-program p)
  (define forms (read-program p))
  (parameterize ([current-namespace ns])
    (compile `(begin ,@forms))))

(define compiled (compile-program path))

(cond
  [(equal? mode "load")
   (void compiled)]
  [else
   (parameterize ([current-namespace ns])
     (eval compiled))
   (cond
     [(equal? mode "ready") (void)]
     [(equal? mode "full")
      (define result (parameterize ([current-namespace ns]) (eval '(bench))))
      (displayln result)]
     [(equal? mode "repeat")
      (unless (and (exact-integer? repeats) (positive? repeats))
        (error 'repeat "REPEATS must be >= 1"))
      (define bench-proc (parameterize ([current-namespace ns]) (eval 'bench)))
      (define result
        (for/fold ([value #f]) ([i (in-range repeats)])
          (bench-proc)))
      (void result)]
     [else (error 'mode "unknown mode: ~a" mode)])])
