; #114/#220/#275 — Lisp owns the semantic relation verdicts used by the
; content-store regression evidence. Rust observes serialization and cardinality,
; but does not decide equality.
;
; Use nested LET forms rather than LET*: the current macro path is not a
; reliable runtime dependency for this proof. Two-part COND clauses consume
; exact D1 predicate results directly.
(00001001 content-store-no?
  (00001000 (value)
    (00100010 value
      (00100010 (00000001 d1-no-left) (00000001 d1-no-right)))))

(00001001 content-store-authority-witness
  (00001000 ()
    (let
      ((value (00000001 (lambda (x) x))))
      (let
        ((written (fs-write (fs-empty) "code" value)))
        (let
          ((fs (00000101 written)))
          (let
            ((root-a (fs-serialize-root fs))
             (root-b (fs-serialize-root fs))
             (object-a (fs-serialize-object value))
             (object-b (fs-serialize-object value))
             (direct
               (world-tell
                 (empty-world)
                 (00000001 zoo)
                 (00000001 ((has-fur cat)))))
             (retold
               (world-tell
                 (world-retract
                   (world-tell
                     (empty-world)
                     (00000001 zoo)
                     (00000001 ((has-fur cat))))
                   (00000001 zoo)
                   (00000001 ((has-fur cat))))
                 (00000001 zoo)
                 (00000001 ((has-fur cat)))))
            (let
              ((root-relation (00100010 root-a root-b))
               (object-relation (00100010 object-a object-b))
               (projection-relation
                 (00100010
                   (world-clauses direct (00000001 zoo))
                   (world-clauses retold (00000001 zoo)))))
              (00000111
                (root-relation
                  (00000111
                    (object-relation
                      (00000111
                        (projection-relation
                          (00000001
                            (content-store-authority-witness
                              (status pass)
                              (laws root-image-deterministic
                                    object-image-deterministic
                                    equal-current-projection))))
                        ((content-store-no? projection-relation)
                          (00000001
                            (content-store-authority-witness
                              (status fail)
                              (law equal-current-projection))))))
                    ((content-store-no? object-relation)
                      (00000001
                        (content-store-authority-witness
                          (status fail)
                          (law object-image-deterministic)))))
                ((content-store-no? root-relation)
                  (00000001
                    (content-store-authority-witness
                      (status fail)
                      (law root-image-deterministic)))))))))))
)))
