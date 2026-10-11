; #432 research-only runtime witness.
; Fresh payloads are minted at runtime so candidate literals cannot hard-code them.
; This file observes current lower-basis behavior only; it does not define CAR/CDR.

(def car-head-a (gensym "car-head-a-"))
(def car-head-b (gensym "car-head-b-"))
(def car-shared-tail (gensym "car-tail-"))
(def cdr-shared-head (gensym "cdr-head-"))
(def cdr-tail-a (gensym "cdr-tail-a-"))
(def cdr-tail-b (gensym "cdr-tail-b-"))

(def car-input-a (cons car-head-a car-shared-tail))
(def car-input-b (cons car-head-b car-shared-tail))
(def cdr-input-a (cons cdr-shared-head cdr-tail-a))
(def cdr-input-b (cons cdr-shared-head cdr-tail-b))

(def observe-pair-kind
  (lambda (value)
    (cond
      ((atom value) (structural-kind pair) (quote pair-observed))
      ((atom value) (structural-kind empty-list) (quote empty-observed))
      ((atom value) (structural-kind atom) (quote atom-observed)))))

(def preserve-selected-pair
  (lambda (value)
    (cond
      ((atom value) (structural-kind pair) value)
      ((atom value) (structural-kind empty-list) (quote ()))
      ((atom value) (structural-kind atom) value))))

(list
  (quote lower-basis-runtime)
  (list
    (quote car-head-mutation-kind)
    (observe-pair-kind car-input-a)
    (observe-pair-kind car-input-b))
  (list
    (quote cdr-tail-mutation-kind)
    (observe-pair-kind cdr-input-a)
    (observe-pair-kind cdr-input-b))
  (list
    (quote cons-wrapper-kind)
    (observe-pair-kind (cons car-input-a (quote marker)))
    (observe-pair-kind (cons (quote marker) cdr-input-a)))
  (list
    (quote cond-preserves-whole-car-input)
    (equal? (preserve-selected-pair car-input-a) car-input-a)
    (equal? (preserve-selected-pair car-input-b) car-input-b))
  (list
    (quote cond-preserves-whole-cdr-input)
    (equal? (preserve-selected-pair cdr-input-a) cdr-input-a)
    (equal? (preserve-selected-pair cdr-input-b) cdr-input-b)))
