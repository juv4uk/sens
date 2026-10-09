#!r6rs
(import (rnrs))

;; Independent R6RS donor oracle. This does NOT execute SENS or mint D10 words.
(define observed 0)
(define (must label truth)
  (if truth
      (begin (set! observed (+ observed 1))
             (display "PASS ")
             (display label)
             (newline))
      (assertion-violation 'd10-r6rs-oracle label)))

(define src (make-eqv-hashtable))
(hashtable-set! src 1 'one)
(hashtable-set! src 2 'two)
(must "source mutable" (hashtable-mutable? src))
(must "source contains two associations" (= (hashtable-size src) 2))

(define frozen (hashtable-copy src))
(must "default copy immutable" (not (hashtable-mutable? frozen)))
(must "default copy preserves source entry one"
      (eq? (hashtable-ref frozen 1 'missing) 'one))
(must "default copy preserves source entry two"
      (eq? (hashtable-ref frozen 2 'missing) 'two))
(must "default copy has two associations" (= (hashtable-size frozen) 2))
(must "immutable copy rejects attempted mutation"
      (guard (condition
              [(assertion-violation? condition) #t]
              [else #f])
        (hashtable-set! frozen 3 'three)
        #f))
(must "failed immutable mutation has no effect"
      (= (hashtable-size frozen) 2))

(define frozen-explicit (hashtable-copy src #f))
(must "explicit false copy immutable"
      (not (hashtable-mutable? frozen-explicit)))
(must "explicit false preserves association"
      (eq? (hashtable-ref frozen-explicit 1 'missing) 'one))

(define mutable-copy (hashtable-copy src #t))
(must "explicit true copy mutable" (hashtable-mutable? mutable-copy))
(must "mutable copy starts with equal associations"
      (and (= (hashtable-size mutable-copy) (hashtable-size src))
           (eq? (hashtable-ref mutable-copy 2 'missing) 'two)))
(hashtable-set! mutable-copy 1 'changed)
(must "mutable copy can be updated"
      (eq? (hashtable-ref mutable-copy 1 'missing) 'changed))
(must "source not changed through copy"
      (eq? (hashtable-ref src 1 'missing) 'one))
(must "immutable copy not changed through independent mutation"
      (eq? (hashtable-ref frozen 1 'missing) 'one))
(hashtable-delete! mutable-copy 2)
(must "deletion on copy does not remove source association"
      (and (= (hashtable-size mutable-copy) 1)
           (= (hashtable-size src) 2)
           (eq? (hashtable-ref src 2 'missing) 'two)))

(define empty (make-eqv-hashtable))
(define empty-copy (hashtable-copy empty))
(must "empty table copy is immutable and still empty"
      (and (not (hashtable-mutable? empty-copy))
           (= (hashtable-size empty-copy) 0)))

(display "D10-R6RS-DONOR-ORACLE PASS observations=")
(display observed)
(newline)
