; #803 — Lisp-owned witness for the admitted projection contract.

(load "lib/core.lisp")
(load "lib/bridge/prolog-to-datalog.lisp")

(00001001 prolog-datalog-bridge-witness
  (00001000 ()
    (00000111
      ((00100010
         (prolog-substitutions-to-datalog-facts
           (00000001
             (prolog-substitution-observation
               (source-ref observation-42)
               (variable ancestor)
               (values bob dave carol))))
         (00000001
           (projection-result
             (projection prolog-substitutions-to-datalog-facts)
             (source-ref observation-42)
             (facts
               ((ancestor bob)
                (ancestor dave)
                (ancestor carol))))))
       (1)
       (00000001 (prolog-datalog-bridge-witness (status pass))))
      ((00100010
         (prolog-substitutions-to-datalog-facts
           (00000001
             (prolog-substitution-observation
               (variable ancestor)
               (values bob))))
         (00000001 (projection-failure missing-source-ref)))
       (1)
       (00000001 (prolog-datalog-bridge-witness (status pass)))))))

(prolog-datalog-bridge-witness)
