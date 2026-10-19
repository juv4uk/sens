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

(визначити prolog-values-to-datalog-facts
  (функція (role values)
    (за-умовою
      
      ((хибне? (атом? values))
       (сполучити (список role (перше values))
             (перетворити-значення-пролог-на-факти-даталог role (решта values)))))))

(визначити prolog-substitutions-to-datalog-facts
  (функція (observation)
    ((функція (source-ref-row variable-row values-row)
      (за-умовою
        ((хибне? (атом? source-ref-row))
         (список (як-є projection-failure) (як-є missing-source-ref)))
        ((атом? source-ref-row) 
         (список (як-є projection-failure) (як-є malformed-source-ref)))
        ((хибне? (атом? source-ref-row))
         (за-умовою
           ((хибне? (атом? variable-row))
            (список (як-є projection-failure) (як-є missing-variable-role)))
           ((атом? variable-row) 
            (список (як-є projection-failure) (як-є malformed-variable-role)))
           ((хибне? (атом? variable-row))
            (за-умовою
              ((хибне? (атом? values-row))
               (список (як-є projection-failure) (як-є missing-values)))
              ((атом? values-row) 
               (список (як-є projection-failure) (як-є malformed-values)))
              ((хибне? (атом? values-row))
               (список
                 (як-є projection-result)
                 (список (як-є projection)
                       (як-є prolog-substitutions-to-datalog-facts))
                 (список (як-є source-ref)
                       (перше (решта source-ref-row)))
                 (список (як-є facts)
                       (перетворити-значення-пролог-на-факти-даталог
                         (перше (решта variable-row))
                         (решта values-row)))))))))))
     (знайти-за-ключем (як-є source-ref) (решта observation))
     (знайти-за-ключем (як-є variable) (решта observation))
     (знайти-за-ключем (як-є values) (решта observation)))))
