; #305 — retire stale Rust truth-sentinel oracles from reason_index.rs.
; The semantic verdicts for reason-index parity belong to Lisp. Rust may keep
; observing index order, mode and finite bounds, but it must not freeze the
; result of `equal?` as historical `t`.
;
; Laws preserved here before the Rust assertions are deleted:
;   1. indexed and forced-linear backward reasoning are structurally equal;
;   2. an explicitly prepared reason-index/1 is an immutable snapshot;
;   3. indexed recursion and negation match the forced-linear path.

(load "lib/unify.lisp")
(load "lib/reason.lisp")

(def reason-index-authority-witness
  (lambda ()
    (let* ((parity-rules
             (quote
               (((seed a))
                ((noise one))
                ((path (var x) left) (seed (var x)))
                ((noise two))
                ((path (var x) right) (seed (var x)))
                ((reachable (var x)) (path (var x) (var side))))))
           (indexed (reason (quote (reachable a)) parity-rules))
           (linear
             (prove-goal
               (quote (reachable a))
               parity-rules
               (quote ())
               (reason-index-linear parity-rules)
               0))
           (parity-relation (equal? indexed linear))

           (old-rules
             (quote
               (((seed a))
                ((reachable (var x)) (seed (var x))))))
           (prepared (reason-make-index old-rules))
           (newer-rules
             (append old-rules (quote (((later yes))))))
           (snapshot-relation
             (equal?
               (reason (quote (reachable a)) old-rules)
               (reason (quote (reachable a)) prepared)))
           (prepared-later-empty
             (equal? (reason (quote (later yes)) prepared) (quote ())))
           (rebuilt-later-count
             (equal? (length (reason (quote (later yes)) newer-rules)) 1))

           (recursive-rules
             (quote
               (((parent alice bob))
                ((parent bob carol))
                ((ancestor (var x) (var y)) (parent (var x) (var y)))
                ((ancestor (var x) (var y))
                  (parent (var x) (var z))
                  (ancestor (var z) (var y)))
                ((safe (var x)) (not? (blocked (var x))))
                ((noise irrelevant)))))
           (goal (quote (ancestor alice carol)))
           (recursive-indexed (reason goal recursive-rules))
           (recursive-linear
             (prove-goal
               goal
               recursive-rules
               (quote ())
               (reason-index-linear recursive-rules)
               0))
           (recursive-relation (equal? recursive-indexed recursive-linear))
           (negation-relation
             (equal?
               (reason (quote (safe alice)) recursive-rules)
               (prove-goal
                 (quote (safe alice))
                 recursive-rules
                 (quote ())
                 (reason-index-linear recursive-rules)
                 0))))
      (cond
        (parity-relation (1)
          (cond
            (snapshot-relation (1)
              (cond
                (prepared-later-empty (1)
                  (cond
                    (rebuilt-later-count (1)
                      (cond
                        (recursive-relation (1)
                          (cond
                            (negation-relation (1)
                              (quote
                                (reason-index-authority-witness
                                  (status pass)
                                  (laws
                                    indexed-linear-parity
                                    immutable-prepared-snapshot
                                    recursion-negation-parity))))
                            (negation-relation (0)
                              (quote
                                (reason-index-authority-witness
                                  (status fail)
                                  (law recursion-negation-parity))))))
                        (recursive-relation (0)
                          (quote
                            (reason-index-authority-witness
                              (status fail)
                              (law recursion-parity))))))
                    (rebuilt-later-count (0)
                      (quote
                        (reason-index-authority-witness
                          (status fail)
                          (law rebuilt-snapshot-sees-new-rule))))))
                (prepared-later-empty (0)
                  (quote
                    (reason-index-authority-witness
                      (status fail)
                      (law prepared-snapshot-is-immutable))))))
            (snapshot-relation (0)
              (quote
                (reason-index-authority-witness
                  (status fail)
                  (law prepared-snapshot-preserves-old-result))))))
        (parity-relation (0)
          (quote
            (reason-index-authority-witness
              (status fail)
              (law indexed-linear-parity))))))))

(reason-index-authority-witness)
