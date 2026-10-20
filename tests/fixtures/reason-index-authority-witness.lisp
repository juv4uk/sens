; #305 — retire stale Rust truth-sentinel oracles from reason_index.rs.
; The semantic verdicts for reason-index parity belong to Lisp.
; Ukrainian projection only.

(load "lib/unify.lisp")
(load "lib/reason.lisp")

(визначити reason-index-authority-witness
  (функція ()
    (нехай ((parity-rules
             (як-є
               (((seed a))
                ((noise one))
                ((path (var x) left) (seed (var x)))
                ((noise two))
                ((path (var x) right) (seed (var x)))
                ((reachable (var x)) (path (var x) (var side))))))
           (indexed (міркувати-за-індексом (як-є (reachable a)) parity-rules))
           (linear
             (міркувати-лінійно
               (як-є (reachable a))
               parity-rules
               (як-є ())
               (лінійний-індекс-міркування parity-rules)
               0))
           (parity-relation (однакові? indexed linear))

           (old-rules
             (як-є
               (((seed a))
                ((reachable (var x)) (seed (var x))))))
           (prepared (побудувати-індекс-міркування old-rules))
           (newer-rules
             (додати-в-кінець old-rules (як-є (((later yes))))))
           (snapshot-relation
             (однакові?
               (міркувати-за-індексом (як-є (reachable a)) old-rules)
               (міркувати-за-індексом (як-є (reachable a)) prepared)))
           (prepared-later-empty
             (однакові? (міркувати-за-індексом (як-є (later yes)) prepared) (як-є ())))
           (rebuilt-later-count
             (однакові? (довжина (міркувати-за-індексом (як-є (later yes)) newer-rules)) 1))

           (recursive-rules
             (як-є
               (((parent alice bob))
                ((parent bob carol))
                ((ancestor (var x) (var y)) (parent (var x) (var y)))
                ((ancestor (var x) (var y))
                  (parent (var x) (var z))
                  (ancestor (var z) (var y)))
                ((safe (var x)) (not? (blocked (var x))))
                ((noise irrelevant)))))
           (goal (як-є (ancestor alice carol)))
           (recursive-indexed (міркувати-за-індексом goal recursive-rules))
           (recursive-linear
             (міркувати-лінійно
               goal
               recursive-rules
               (як-є ())
               (лінійний-індекс-міркування recursive-rules)
               0))
           (recursive-parity (однакові? recursive-indexed recursive-linear))
           (negation-goal (як-є (safe alice)))
           (negation-indexed (міркувати-за-індексом negation-goal recursive-rules))
           (negation-linear
             (міркувати-лінійно
               negation-goal
               recursive-rules
               (як-є ())
               (лінійний-індекс-міркування recursive-rules)
               0))
           (negation-parity (однакові? negation-indexed negation-linear)))
      (за-умовою
        (parity-relation
          (за-умовою
            (snapshot-relation
              (за-умовою
                (prepared-later-empty
                  (за-умовою
                    (rebuilt-later-count
                      (за-умовою
                        (recursive-parity
                          (за-умовою
                            (negation-parity
                              (як-є (reason-index-authority-witness
                                      (status pass)
                                      (laws
                                        indexed-linear-parity
                                        prepared-snapshot-preserves-old-result
                                        prepared-snapshot-is-immutable
                                        rebuilt-snapshot-sees-new-rule
                                        recursive-parity
                                        negation-parity))))
                            (так (як-є (reason-index-authority-witness
                                        (status fail)
                                        (law negation-parity))))))
                        (так (як-є (reason-index-authority-witness
                                    (status fail)
                                    (law recursive-parity))))))
                    (так (як-є (reason-index-authority-witness
                                (status fail)
                                (law rebuilt-snapshot-sees-new-rule))))))
                (так (як-є (reason-index-authority-witness
                            (status fail)
                            (law prepared-snapshot-is-immutable))))))
            (так (як-є (reason-index-authority-witness
                        (status fail)
                        (law prepared-snapshot-preserves-old-result))))))
        (так (як-є (reason-index-authority-witness
                    (status fail)
                    (law indexed-linear-parity))))))))

(reason-index-authority-witness)
