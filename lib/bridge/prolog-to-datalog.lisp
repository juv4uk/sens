; #803 — admitted Prolog substitution -> Datalog fact projection.
;
; Semantic authority lives in Lisp data/code here. The host may preserve and
; transport native Prolog observations, but this function alone decides which
; fields are admitted into ordinary Datalog fact data.
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
;     (facts ((ROLE VALUE) ...)))
;
; Failure is named data, never ()/false.

(00001001 prolog-values-to-datalog-facts
  (00001000 (role values)
    (00000111
      ((00000010 values)
       (00000001 ()))
      ((00000010 (00000001 ()))
       (00000100
         (00100111 role (00000101 values))
         (prolog-values-to-datalog-facts role (00000110 values)))))))

(00001001 prolog-substitutions-to-datalog-facts
  (00001000 (observation)
    (10011100 ((source-ref-row (00101101 (00000001 source-ref) (00000110 observation)))
          (variable-row (00101101 (00000001 variable) (00000110 observation)))
          (values-row (00101101 (00000001 values) (00000110 observation))))
      (00000111
        ((00000010 source-ref-row)
         (00000111
           ((00000011 source-ref-row (00000001 ()))
            (00100111 (00000001 projection-failure) (00000001 missing-source-ref)))
           ((00000010 (00000001 ()))
            (00100111 (00000001 projection-failure) (00000001 malformed-source-ref)))))
        ((00000010 (00000001 ()))
         (00000111
           ((00000010 variable-row)
            (00000111
              ((00000011 variable-row (00000001 ()))
               (00100111 (00000001 projection-failure) (00000001 missing-variable-role)))
              ((00000010 (00000001 ()))
               (00100111 (00000001 projection-failure) (00000001 malformed-variable-role)))))
           ((00000010 (00000001 ()))
            (00000111
              ((00000010 values-row)
               (00000111
                 ((00000011 values-row (00000001 ()))
                  (00100111 (00000001 projection-failure) (00000001 missing-values)))
                 ((00000010 (00000001 ()))
                  (00100111 (00000001 projection-failure) (00000001 malformed-values)))))
              ((00000010 (00000001 ()))
               (00100111
                 (00000001 projection-result)
                 (00100111 (00000001 projection)
                       (00000001 prolog-substitutions-to-datalog-facts))
                 (00100111 (00000001 source-ref)
                       (00000101 (00000110 source-ref-row)))
                 (00100111 (00000001 facts)
                       (prolog-values-to-datalog-facts
                         (00000101 (00000110 variable-row))
                         (00000110 values-row)))))))))))))
