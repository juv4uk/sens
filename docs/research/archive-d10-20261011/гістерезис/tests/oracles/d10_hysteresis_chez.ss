#!r6rs
(import (rnrs))

;; Independently executable Chez Scheme reference for the D10
;; hysteretic Boolean step, over exact rationals. NOT SENS binary execution.
(define (step prior low high sample)
  (unless (< low high)
    (assertion-violation 'step "low must be < high"))
  (cond
    ((<= sample low) #f)
    ((>= sample high) #t)
    (else prior)))

;; Separate monotone Boolean formulation; no three-way interval case split.
(define (boolean-oracle prior low high sample)
  (if prior
      (> sample low)
      (>= sample high)))

(define checks 0)
(define (require observation expectation)
  (unless (eqv? observation expectation)
    (assertion-violation 'hysteresis-check "unequal witness"
                         observation expectation))
  (set! checks (+ checks 1)))

(define rational-samples
  '(-5 -4 -3 -2 -3/2 -4/3 -1 -2/3 -1/2 -1/3 0
    1/3 1/2 2/3 1 4/3 3/2 2 3 4 5))

(for-each
 (lambda (low)
   (for-each
    (lambda (high)
      (when (< low high)
        (for-each
         (lambda (sample)
           (for-each
            (lambda (prior)
              (let ((result (step prior low high sample)))
                (require result (boolean-oracle prior low high sample))
                (require (step result low high sample) result)
                (when (and (< low sample) (< sample high))
                  (require result prior))
                (when (<= sample low)
                  (require result #f))
                (when (>= sample high)
                  (require result #t))))
            '(#f #t)))
         rational-samples)))
    rational-samples))
 rational-samples)

(require (step #f 0 2 1) #f)
(require (step #t 0 2 1) #t)
(require (step #f 0 2 2) #t)
(require (step #t 0 2 0) #f)

(display "D10-HYSTERESIS-CHEZ: PASS independent exact-rational checks=")
(display checks)
(newline)
