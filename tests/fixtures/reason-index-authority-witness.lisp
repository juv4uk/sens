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

(00001001 reason-index-authority-witness
  (00001000 ()
    (10011101 ((parity-rules
             (00000001
               (((seed a))
                ((noise one))
                ((path (var x) left) (seed (var x)))
                ((noise two))
                ((path (var x) right) (seed (var x)))
                ((reachable (var x)) (path (var x) (var side))))))
           (indexed (10000101 (00000001 (reachable a)) parity-rules))
           (linear
             (10000000
               (00000001 (reachable a))
               parity-rules
               (00000001 ())
               (reason-index-linear parity-rules)
               0))
           (parity-relation (00100010 indexed linear))

           (old-rules
             (00000001
               (((seed a))
                ((reachable (var x)) (seed (var x))))))
           (prepared (reason-make-index old-rules))
           (newer-rules
             (00101001 old-rules (00000001 (((later yes))))))
           (snapshot-relation
             (00100010
               (10000101 (00000001 (reachable a)) old-rules)
               (10000101 (00000001 (reachable a)) prepared)))
           (prepared-later-empty
             (00100010 (10000101 (00000001 (later yes)) prepared) (00000001 ())))
           (rebuilt-later-count
             (00100010 (00101000 (10000101 (00000001 (later yes)) newer-rules)) 1))

           (recursive-rules
             (00000001
               (((parent alice bob))
                ((parent bob carol))
                ((ancestor (var x) (var y)) (parent (var x) (var y)))
                ((ancestor (var x) (var y))
                  (parent (var x) (var z))
                  (ancestor (var z) (var y)))
                ((safe (var x)) (not? (blocked (var x))))
                ((noise irrelevant)))))
           (goal (00000001 (ancestor alice carol)))
           (recursive-indexed (10000101 goal recursive-rules))
           (recursive-linear
             (10000000
               goal
               recursive-rules
               (00000001 ())
               (reason-index-linear recursive-rules)
               0))
           (recursive-relation (00100010 recursive-indexed recursive-linear))
           (negation-relation
             (00100010
               (10000101 (00000001 (safe alice)) recursive-rules)
               (10000000
                 (00000001 (safe alice))
                 recursive-rules
                 (00000001 ())
                 (reason-index-linear recursive-rules)
                 0))))
      (00000111
        (parity-relation
          (00000111
            (snapshot-relation
              (00000111
                (prepared-later-empty
                  (00000111
                    (rebuilt-later-count
                      (00000111
                        (recursive-relation
                          (00000111
                            (negation-relation
                              (00000001
                                (reason-index-authority-witness
                                  (status pass)
                                  (laws
                                    indexed-linear-parity
                                    immutable-prepared-snapshot
                                    recursion-negation-parity))))
                            ((00100010 negation-relation (00100010 (00000001 d1-no-left) (00000001 d1-no-right)))
                              (00000001
                                (reason-index-authority-witness
                                  (status fail)
                                  (law recursion-negation-parity))))))
                        ((00100010 recursive-relation (00100010 (00000001 d1-no-left) (00000001 d1-no-right)))
                          (00000001
                            (reason-index-authority-witness
                              (status fail)
                              (law recursion-parity))))))
                    ((00100010 rebuilt-later-count (00100010 (00000001 d1-no-left) (00000001 d1-no-right)))
                      (00000001
                        (reason-index-authority-witness
                          (status fail)
                          (law rebuilt-snapshot-sees-new-rule))))))
                ((00100010 prepared-later-empty (00100010 (00000001 d1-no-left) (00000001 d1-no-right)))
                  (00000001
                    (reason-index-authority-witness
                      (status fail)
                      (law prepared-snapshot-is-immutable))))))
            ((00100010 snapshot-relation (00100010 (00000001 d1-no-left) (00000001 d1-no-right)))
              (00000001
                (reason-index-authority-witness
                  (status fail)
                  (law prepared-snapshot-preserves-old-result))))))
        ((00100010 parity-relation (00100010 (00000001 d1-no-left) (00000001 d1-no-right)))
          (00000001
            (reason-index-authority-witness
              (status fail)
              (law indexed-linear-parity))))))))

(reason-index-authority-witness)
