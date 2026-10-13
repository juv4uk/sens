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
    (110
      
      ((0100 (010 values))
       (111 (1110 role (100 values))
             (prolog-values-to-datalog-facts role (011 values)))))))

(0011 prolog-substitutions-to-datalog-facts
  (0010 (observation)
    ((0010 (source-ref-row variable-row values-row)
      (110
        ((0100 (010 source-ref-row))
         (1110 (001 projection-failure) (001 missing-source-ref)))
        ((010 source-ref-row) 
         (1110 (001 projection-failure) (001 malformed-source-ref)))
        ((0100 (010 source-ref-row))
         (110
           ((0100 (010 variable-row))
            (1110 (001 projection-failure) (001 missing-variable-role)))
           ((010 variable-row) 
            (1110 (001 projection-failure) (001 malformed-variable-role)))
           ((0100 (010 variable-row))
            (110
              ((0100 (010 values-row))
               (1110 (001 projection-failure) (001 missing-values)))
              ((010 values-row) 
               (1110 (001 projection-failure) (001 malformed-values)))
              ((0100 (010 values-row))
               (1110
                 (001 projection-result)
                 (1110 (001 projection)
                       (001 prolog-substitutions-to-datalog-facts))
                 (1110 (001 source-ref)
                       (100 (011 source-ref-row)))
                 (1110 (001 facts)
                       (prolog-values-to-datalog-facts
                         (100 (011 variable-row))
                         (011 values-row)))))))))))
     (11100 (001 source-ref) (011 observation))
     (11100 (001 variable) (011 observation))
     (11100 (001 values) (011 observation)))))
