#!r6rs
(import (rnrs))

(define checks 0)
(define (ensure label ok)
  (unless ok
    (assertion-violation 'gray-donor label))
  (set! checks (+ checks 1)))

(define (range-ok? w x)
  (and (integer? w) (>= w 0) (integer? x) (>= x 0)
       (< x (expt 2 w))))

(define (gray-encode w n)
  (unless (range-ok? w n) (assertion-violation 'gray-encode "invalid rank/width"))
  (bitwise-xor n (bitwise-arithmetic-shift-right n 1)))

(define (gray-decode w g)
  (unless (range-ok? w g) (assertion-violation 'gray-decode "invalid word/width"))
  (let loop ((m g) (b 0))
    (if (= m 0) b
        (loop (bitwise-arithmetic-shift-right m 1)
              (bitwise-xor b m)))))

(define (popcount n)
  (let loop ((v n) (s 0))
    (if (= v 0) s
        (loop (bitwise-arithmetic-shift-right v 1)
              (+ s (bitwise-and v 1))))))

(ensure 'rank7-to-gray4 (= (gray-encode 4 7) 4))
(ensure 'rank11-to-gray14 (= (gray-encode 4 11) 14))
(ensure 'gray4-to-rank7 (= (gray-decode 4 4) 7))
(ensure 'gray14-to-rank11 (= (gray-decode 4 14) 11))
(ensure 'zero-width (= (gray-decode 0 (gray-encode 0 0)) 0))
(ensure 'reject-negative
  (guard (e (else #t)) (gray-encode 4 -1) #f))
(ensure 'reject-width-overflow
  (guard (e (else #t)) (gray-decode 4 16) #f))

(do ((w 0 (+ w 1))) ((> w 10))
  (do ((n 0 (+ n 1))) ((>= n (expt 2 w)))
    (ensure 'decode-encode-identity
      (= (gray-decode w (gray-encode w n)) n))
    (ensure 'encode-decode-identity
      (= (gray-encode w (gray-decode w n)) n))
    (when (>= w 1)
      (ensure 'one-bit-neighbor
        (= (popcount (bitwise-xor
          (gray-encode w n)
          (gray-encode w (mod (+ n 1) (expt 2 w))))) 1)))))

(display "PASS REAL-CHEZ-R6RS GRAY word reversible cyclic bounded exhaustive ")
(display checks)
(newline)
