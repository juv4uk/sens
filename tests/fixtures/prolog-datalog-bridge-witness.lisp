; #803 — Lisp-owned witness for the admitted projection contract.

(load "lib/core.lisp")
(load "lib/bridge/prolog-to-datalog.lisp")

(def prolog-datalog-bridge-witness
  (lambda ()
    (cond
      ((equal?
         (prolog-substitutions-to-datalog-facts
           (quote
             (prolog-substitution-observation
               (source-ref observation-42)
               (variable ancestor)
               (values bob dave carol))))
         (quote
           (projection-result
             (projection prolog-substitutions-to-datalog-facts)
             (source-ref observation-42)
             (facts
               ((ancestor bob)
                (ancestor dave)
                (ancestor carol))))))
       (1)
       (quote (prolog-datalog-bridge-witness (status pass))))
      ((equal?
         (prolog-substitutions-to-datalog-facts
           (quote
             (prolog-substitution-observation
               (variable ancestor)
               (values bob))))
         (quote (projection-failure missing-source-ref)))
       (1)
       (quote (prolog-datalog-bridge-witness (status pass)))))))

(prolog-datalog-bridge-witness)
