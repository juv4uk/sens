; #218 STRUCTURAL-QUERY-1 — Lisp-owned inventory completeness witness.
;
; Rust may transport the two source documents into these bindings:
;   structural-query-inventory-document
;   public-surface-inventory-document
; but the coverage/classification verdict stays in Lisp.
;
; The witness deliberately derives the predicate surface set from
; lib/surface/uk-inventory.lisp instead of copying the 17 names here.

(def sqi-field
  (lambda (key row)
    (let ((entry (assoc key row)))
      (cond
        ((atom? entry) () (quote ()))
        ((atom? entry) (1) (quote ()))
        (t (cdr entry))))))

(def sqi-find-tag
  (lambda (tag entries)
    (cond
      ((atom? entries) () (quote ()))
      ((atom? entries) (1) (quote ()))
      ((and (not? (atom? (car entries)))
            (eq? (car (car entries)) tag))
       (car entries))
      (t (sqi-find-tag tag (cdr entries))))))

(def sqi-public-predicates
  (lambda ()
    (let ((entry (sqi-find-tag (quote public-predicates)
                               (cdr public-surface-inventory-document))))
      (cond
        ((atom? entry) () (quote ()))
        ((atom? entry) (1) (quote ()))
        (t (car (cdr entry)))))))

(def sqi-rows
  (lambda ()
    (cdr structural-query-inventory-document)))

(def sqi-count-surface
  (lambda (surface rows)
    (cond
      ((atom? rows) () 0)
      ((atom? rows) (1) 0)
      ((eq? (sqi-field (quote surface) (car rows)) surface)
       (+ 1 (sqi-count-surface surface (cdr rows))))
      (t
       (sqi-count-surface surface (cdr rows))))))

(def sqi-required-row?
  (lambda (row)
    (and
      (not? (atom? (assoc (quote identity) row)))
      (not? (atom? (assoc (quote surface) row)))
      (not? (atom? (assoc (quote producer) row)))
      (not? (atom? (assoc (quote current-result) row)))
      (not? (atom? (assoc (quote question-domain) row)))
      (not? (atom? (assoc (quote mathematical-binary?) row)))
      (not? (atom? (assoc (quote owner) row)))
      (not? (atom? (assoc (quote consumer-class) row)))
      (not? (atom? (assoc (quote compatibility-impact) row)))
      (not? (atom? (assoc (quote migration) row))))))

(def sqi-all-public-covered-once?
  (lambda (predicates rows)
    (cond
      ((atom? predicates) () t)
      ((atom? predicates) (1) t)
      ((eq? (sqi-count-surface (car predicates) rows) 1)
       (sqi-all-public-covered-once? (cdr predicates) rows))
      (t (quote ())))))

(def sqi-no-extra-surfaces?
  (lambda (rows predicates)
    (cond
      ((atom? rows) () t)
      ((atom? rows) (1) t)
      ((and (sqi-required-row? (car rows))
            (member? (sqi-field (quote surface) (car rows)) predicates))
       (sqi-no-extra-surfaces? (cdr rows) predicates))
      (t (quote ())))))

(def sqi-math-delegation-valid?
  (lambda (rows)
    (cond
      ((atom? rows) () t)
      ((atom? rows) (1) t)
      (t
       (let ((row (car rows)))
         (cond
           ((eq? (sqi-field (quote mathematical-binary?) row) (quote yes-domain-bounded))
            (cond
              ((eq? (sqi-field (quote owner) row) (quote exact-q-decision-216))
               (sqi-math-delegation-valid? (cdr rows)))
              (t (quote ()))))
           (t (sqi-math-delegation-valid? (cdr rows)))))))))

(def structural-query-inventory-witness
  (lambda ()
    (let ((predicates (sqi-public-predicates))
          (rows (sqi-rows)))
      (cond
        ((and (eq? (length predicates) 17)
              (eq? (length rows) 17)
              (sqi-all-public-covered-once? predicates rows)
              (sqi-no-extra-surfaces? rows predicates)
              (sqi-math-delegation-valid? rows))
         (list (quote structural-query-inventory-witness)
               (list (quote status) (quote pass))
               (list (quote public-predicate-count) (length predicates))
               (list (quote classified-row-count) (length rows))))
        (t
         (list (quote structural-query-inventory-witness)
               (list (quote status) (quote fail))
               (list (quote public-predicate-count) (length predicates))
               (list (quote classified-row-count) (length rows))))))))
