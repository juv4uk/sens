;;; R6RS Chez Scheme independent donor for bounded integer congruence lift.
;;; External source-grade mathematical oracle; NOT binary SENS runtime.
(import (rnrs))

(define checks 0)
(define (check label ok)
  (assert ok)
  (set! checks (+ checks 1))
  (display "OBS") (display #\tab) (display label)
  (display #\tab) (display "PASS") (newline))

(define (bounded-lift M r lo hi)
  (assert (and (integer? M) (exact? M) (>= M 2)))
  (assert (and (integer? r) (exact? r) (<= 0 r) (< r M)))
  (assert (and (integer? lo) (exact? lo)))
  (assert (and (integer? hi) (exact? hi) (<= lo hi)))
  (let* ((kmin (- (div (- r lo) M)))
         (kmax (div (- hi r) M))
         (count (max 0 (+ 1 (- kmax kmin)))))
    (cond
      ((= count 0) (list 'NONE 0))
      ((= count 1) (list 'UNIQUE (+ r (* M kmin))))
      (else (let ((first (+ r (* M kmin))))
              (list 'AMBIGUOUS count first (+ first M)))))))

(define (raises? thunk)
  (guard (ex (else #t))
    (thunk) #f))

(check "AS5600_WRAP_UNIQUE"
  (equal? (bounded-lift 4096 2 4090 4100) '(UNIQUE 4098)))
(check "AS5600_NO_MATCH"
  (equal? (bounded-lift 4096 2 3 4097) '(NONE 0)))
(check "AS5600_MULTI_TURN_ALIAS"
  (equal? (bounded-lift 4096 2 0 8194) '(AMBIGUOUS 3 2 4098)))
(check "NEGATIVE_TURNS_AMBIG"
  (equal? (bounded-lift 7 6 -10 -1) '(AMBIGUOUS 2 -8 -1)))
(check "NEGATIVE_BOUNDARY_UNIQUE"
  (equal? (bounded-lift 5 2 -3 -3) '(UNIQUE -3)))
(check "NONE_BETWEEN_CYCLES"
  (equal? (bounded-lift 7 0 1 6) '(NONE 0)))
(check "INCLUSIVE_ENDPOINT_TWICE"
  (equal? (bounded-lift 7 0 0 7) '(AMBIGUOUS 2 0 7)))
(check "NEGATIVE_SINGLE"
  (equal? (bounded-lift 11 1 -10 -10) '(UNIQUE -10)))
(check "SHIFTED_INTERVAL_UNIQUE"
  (equal? (bounded-lift 7 4 10 11) '(UNIQUE 11)))
(check "LENGTH_PERIOD_PLUS_ONE_AMBIG"
  (equal? (bounded-lift 9 6 6 15) '(AMBIGUOUS 2 6 15)))
(check "BAD_MODULUS"
  (raises? (lambda () (bounded-lift 1 0 0 3))))
(check "BAD_RESIDUE"
  (raises? (lambda () (bounded-lift 7 7 0 9))))
(check "BAD_NEGATIVE_RESIDUE"
  (raises? (lambda () (bounded-lift 7 -1 0 9))))
(check "BAD_REVERSED_INTERVAL"
  (raises? (lambda () (bounded-lift 7 1 10 0))))
(check "BAD_FRACTIONAL_BOUND"
  (raises? (lambda () (bounded-lift 7 1 1/2 10))))
(check "INTEGER_NOT_REAL_FLOAT"
  (raises? (lambda () (bounded-lift 7 1 0.0 10))))

(display "SUMMARY") (display #\tab)
(display "UNIQUE-BOUNDED-MODULAR-LIFT-CHEZ-V1") (display #\tab)
(display checks) (newline)
