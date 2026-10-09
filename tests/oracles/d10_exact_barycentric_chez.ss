;;; Independent Chez Scheme R6RS exact interpolation witness, NOT SENS.
;;; (role research-only)
;;; (semantic-authority-change none)
;;; Source: https://dlmf.nist.gov/3.3 §3.3(i).
(import (rnrs))

(define observations 0)
(define (observe label condition)
  (assert condition)
  (set! observations (+ observations 1))
  (display "OBS") (display #\tab) (display label)
  (display #\tab) (display "PASS") (newline))

(define (distinct-xs? pts)
  (or (null? pts)
      (and (not (exists (lambda (q) (= (caar pts) (car q))) (cdr pts)))
           (distinct-xs? (cdr pts)))))

(define (weight pair pts)
  (/ 1 (fold-left
         (lambda (p q)
           (if (= (car pair) (car q))
               p
               (* p (- (car pair) (car q)))))
         1 pts)))

(define (bary pts x)
  (assert (and (pair? pts) (number? x) (exact? x)))
  (assert (for-all (lambda (q) (and (pair? q)
                                     (number? (car q)) (number? (cdr q))
                                     (exact? (car q)) (exact? (cdr q))))
                   pts))
  (assert (distinct-xs? pts))
  (let ((node (find (lambda (q) (= (car q) x)) pts)))
    (if node
        (cdr node)
        (let* ((terms
                (map (lambda (q) (/ (weight q pts) (- x (car q)))) pts))
               (denominator (apply + terms))
               (numerator
                (apply + (map (lambda (t q) (* t (cdr q))) terms pts))))
          (assert (not (= denominator 0)))
          (/ numerator denominator)))))

(define (raises? thunk)
  (guard (ex (else #t))
    (thunk)
    #f))

(define quad '((0 . 0) (1 . 1) (2 . 4)))
(define lin '((-1 . 1) (1 . 5)))
(define constant '((0 . 5) (1 . 5) (2 . 5)))
(observe "QUAD_NODE" (= 4 (bary quad 2)))
(observe "QUAD_HALF" (= 1/4 (bary quad 1/2)))
(observe "QUAD_EXTRAP" (= 9 (bary quad 3)))
(observe "LINEAR_MID" (= 3 (bary lin 0)))
(observe "SINGLE_CONSTANT" (= 7 (bary '((1 . 7)) 5/2)))
(observe "THREE_CONSTANT" (= 5 (bary constant 3/2)))
(observe "REVERSE_ORDER" (= (bary quad 3/2) (bary (reverse quad) 3/2)))
(observe "EXACT_NEGATIVE" (= 1 (bary quad -1)))
(observe "EXACT_NODE" (= 1 (bary quad 1)))
(observe "VALUE_SHIFT"
  (= (+ 7 (bary quad 1/2))
     (bary (map (lambda (q) (cons (car q) (+ (cdr q) 7))) quad) 1/2)))
(observe "VALUE_SCALE"
  (= (* -2 (bary quad 1/2))
     (bary (map (lambda (q) (cons (car q) (* -2 (cdr q)))) quad) 1/2)))
(observe "DUPLICATE_REJECT"
  (raises? (lambda () (bary '((0 . 0) (0 . 2)) 1))))
(observe "EMPTY_REJECT"
  (raises? (lambda () (bary '() 0))))
(observe "INEXACT_NODE_REJECT"
  (raises? (lambda () (bary '((0.0 . 0) (1 . 1)) 1/2))))
(observe "INEXACT_QUERY_REJECT"
  (raises? (lambda () (bary quad 0.5))))

(display "SUMMARY") (display #\tab)
(display "D10-EXACT-BARYCENTRIC-CHEZ-V1") (display #\tab)
(display observations) (newline)
