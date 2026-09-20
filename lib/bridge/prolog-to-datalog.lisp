; #803 — first admitted cross-island projection.
;
; Semantic authority lives here: this file decides which source fields are
; preserved and what ordinary Datalog fact data is emitted. The host may decode
; bounded Prolog wire syntax into ordinary source data, but must not invent the
; mapping.
;
; Input:
;   (prolog-substitution-observation
;     (source-ref REF)
;     (variable ROLE)
;     (values VALUE ...))
;
; Output:
;   (projection-result
;     (projection prolog-substitutions-to-datalog-facts)
;     (source-ref REF)
;     (facts (ROLE VALUE) ...))
;
; Failure is named data, never ()/false.

(def prolog-values-to-datalog-facts
  (lambda (role values)
    (cond
      ((atom values) (structural-kind empty-list) (quote ()))
      ((atom values) (structural-kind pair)
       (cons (list role (car values))
             (prolog-values-to-datalog-facts role (cdr values)))))))

(def prolog-substitutions-to-datalog-facts
  (lambda (observation)
    (let ((source-ref-row (assoc (quote source-ref) (cdr observation)))
          (variable-row (assoc (quote variable) (cdr observation)))
          (values-row (assoc (quote values) (cdr observation))))
      (cond
        ((atom source-ref-row) (structural-kind empty-list)
         (list (quote projection-failure) (quote missing-source-ref)))
        ((atom source-ref-row) (structural-kind pair)
         (cond
           ((atom variable-row) (structural-kind empty-list)
            (list (quote projection-failure) (quote missing-variable-role)))
           ((atom variable-row) (structural-kind pair)
            (cond
              ((atom values-row) (structural-kind empty-list)
               (list (quote projection-failure) (quote missing-values)))
              ((atom values-row) (structural-kind pair)
               (list
                 (quote projection-result)
                 (list (quote projection)
                       (quote prolog-substitutions-to-datalog-facts))
                 (list (quote source-ref) (cdr source-ref-row))
                 (list (quote facts)
                       (prolog-values-to-datalog-facts
                         (cdr variable-row)
                         (cdr values-row)))))))))))))
