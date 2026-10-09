;;; External R6RS Chez Scheme donor model, not executable SENS.
;;; NIST SP 1065: section 5.2.8 Hadamard variance and 5.2.9 overlapping form.
;;; No D10 coordinates or ratification.
(import (rnrs))

(define observations 0)
(define (observe label predicate)
  (assert predicate)
  (set! observations (+ observations 1))
  (display "OBS") (display #\tab) (display label)
  (display #\tab) (display "PASS") (newline))

(define (mean-span values start n)
  (let loop ((k 0) (acc 0))
    (if (= k n)
        (/ acc n)
        (loop (+ k 1)
              (+ acc (list-ref values (+ start k)))))))

(define (hadamard-variance frequency m)
  (assert (and (integer? m) (positive? m)))
  (let* ((n (length frequency))
         (count (+ 1 (- n (* 3 m)))))
    (assert (positive? count))
    (let loop ((i 0) (sum 0))
      (if (= i count)
          (/ sum (* 6 count))
          (let* ((a (mean-span frequency i m))
                 (b (mean-span frequency (+ i m) m))
                 (c (mean-span frequency (+ i (* 2 m)) m))
                 (d (+ a (* -2 b) c)))
            (loop (+ i 1) (+ sum (* d d))))))))

(define (signals-error? thunk)
  (guard (ex (else #t))
    (thunk)
    #f))

(define (translate xs k)
  (map (lambda (v) (+ v k)) xs))
(define (add-linear-drift xs k)
  (let loop ((rest xs) (index 0))
    (if (null? rest)
        '()
        (cons (+ (car rest) (* k index))
              (loop (cdr rest) (+ index 1))))))

(observe "THREE_ZERO_VARIANCE"
  (= 0 (hadamard-variance '(0 0 0) 1)))
(observe "UNIT_IMPULSE"
  (= 1/6 (hadamard-variance '(0 0 1) 1)))
(observe "NEGATIVE_SECOND_DIFF"
  (= 2/3 (hadamard-variance '(0 1 0) 1)))
(observe "EXACT_RATIONAL_RESULT"
  (= 5/18 (hadamard-variance '(0 0 0 1 0) 1)))
(observe "LINEAR_FREQ_DRIFT_REJECTED"
  (= 0 (hadamard-variance '(1 2 3 4 5 6) 1)))
(observe "QUADRATIC_FREQ_TREND_NONZERO"
  (= 2/3 (hadamard-variance '(0 1 4 9 16) 1)))
(observe "INVARIANT_UNDER_CONSTANT_OFFSET"
  (= (hadamard-variance '(0 0 1 1 0 0) 2)
     (hadamard-variance (translate '(0 0 1 1 0 0) 100) 2)))
(observe "INVARIANT_UNDER_LINEAR_DRIFT"
  (= (hadamard-variance '(0 0 1 1 0 0) 2)
     (hadamard-variance (add-linear-drift '(0 0 1 1 0 0) 3) 2)))
(observe "M2_BLOCK_MEANS"
  (= 2/3 (hadamard-variance '(0 0 1 1 0 0) 2)))
(observe "EXACT_HOMOGENEITY"
  (= (* 4 (hadamard-variance '(0 0 1 1 0 0) 2))
     (hadamard-variance '(0 0 2 2 0 0) 2)))
(observe "TOO_FEW_SAMPLES_REJECTED"
  (signals-error? (lambda () (hadamard-variance '(1 2) 1))))
(observe "M_ZERO_REJECTED"
  (signals-error? (lambda () (hadamard-variance '(0 1 2) 0))))
(observe "M_NEGATIVE_REJECTED"
  (signals-error? (lambda () (hadamard-variance '(0 1 2) -1))))
(observe "M_TOO_LARGE_REJECTED"
  (signals-error? (lambda () (hadamard-variance '(0 0 1 1 0 0) 3))))
(observe "INTEGER_M_REQUIRED"
  (signals-error? (lambda () (hadamard-variance '(0 0 1 1 0 0) 1/2))))

(display "SUMMARY") (display #\tab)
(display "HADAMARD-VARIANCE-CHEZ-V1") (display #\tab)
(display observations) (newline)
