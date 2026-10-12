; #803 — Lisp-owned witness for the admitted projection contract.

(load "lib/core.lisp")
(load "lib/bridge/prolog-to-datalog.lisp")

(0011 prolog-datalog-bridge-witness
  (0010 ()
    (110
      ((11110111
         (prolog-substitutions-to-datalog-facts
           (001
             (prolog-substitution-observation
               (source-ref observation-42)
               (variable ancestor)
               (values bob dave carol))))
         (001
           (projection-result
             (projection prolog-substitutions-to-datalog-facts)
             (source-ref observation-42)
             (facts
               ((ancestor bob)
                (ancestor dave)
                (ancestor carol))))))
       (1)
       (001 (prolog-datalog-bridge-witness (status pass))))
      ((11110111
         (prolog-substitutions-to-datalog-facts
           (001
             (prolog-substitution-observation
               (variable ancestor)
               (values bob))))
         (001 (projection-failure missing-source-ref)))
       (1)
       (001 (prolog-datalog-bridge-witness (status pass)))))))

(prolog-datalog-bridge-witness)
