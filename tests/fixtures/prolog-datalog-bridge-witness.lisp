; Prolog→Datalog bridge witness for the admitted projection contract.

(load "lib/core.lisp")
(load "lib/bridge/prolog-to-datalog.lisp")

(визначити prolog-datalog-bridge-witness
  (функція ()
    (за-умовою
      ((однакові?
         (prolog-substitutions-to-datalog-facts
           (як-є
             (prolog-substitution-observation
               (source-ref observation-42)
               (variable ancestor)
               (values bob dave carol))))
         (як-є
           (projection-result
             (projection prolog-substitutions-to-datalog-facts)
             (source-ref observation-42)
             (facts
               ((ancestor bob)
                (ancestor dave)
                (ancestor carol))))))
       (як-є (prolog-datalog-bridge-witness (status pass))))
      ((однакові?
         (prolog-substitutions-to-datalog-facts
           (як-є
             (prolog-substitution-observation
               (variable ancestor)
               (values bob))))
         (як-є (projection-failure missing-source-ref)))
       (як-є (prolog-datalog-bridge-witness (status pass)))))))

(prolog-datalog-bridge-witness)
