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

(0011 prolog-values-to-datalog-facts
  (0010 (role values)
    (011
      ((010 values) () (001 ()))
      ((010 values) (0)
       (100 (1000 role (101 values))
             (prolog-values-to-datalog-facts role (110 values)))))))

(0011 prolog-substitutions-to-datalog-facts
  (0010 (observation)
    (001000 ((source-ref-row (11100 (001 source-ref) (110 observation)))
          (variable-row (11100 (001 variable) (110 observation)))
          (values-row (11100 (001 values) (110 observation))))
      (011
        ((010 source-ref-row) ()
         (1000 (001 projection-failure) (001 missing-source-ref)))
        ((010 source-ref-row) (1)
         (1000 (001 projection-failure) (001 malformed-source-ref)))
        ((010 source-ref-row) (0)
         (011
           ((010 variable-row) ()
            (1000 (001 projection-failure) (001 missing-variable-role)))
           ((010 variable-row) (1)
            (1000 (001 projection-failure) (001 malformed-variable-role)))
           ((010 variable-row) (0)
            (011
              ((010 values-row) ()
               (1000 (001 projection-failure) (001 missing-values)))
              ((010 values-row) (1)
               (1000 (001 projection-failure) (001 malformed-values)))
              ((010 values-row) (0)
               (1000
                 (001 projection-result)
                 (1000 (001 projection)
                       (001 prolog-substitutions-to-datalog-facts))
                 (1000 (001 source-ref)
                       (101 (110 source-ref-row)))
                 (1000 (001 facts)
                       (prolog-values-to-datalog-facts
                         (101 (110 variable-row))
                         (110 values-row)))))))))))))
