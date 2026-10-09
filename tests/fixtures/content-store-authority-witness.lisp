; #114/#220/#275 — Lisp owns the semantic relation verdicts used by the
; content-store regression evidence. Rust may observe serialization bytes and
; store cardinality, but it must not freeze `equal?` as historical t/().
;
; This witness deliberately says nothing about host mechanics. It only asks
; the language whether the two deterministic images are structurally the same
; and whether two Worlds with equal current clauses have the same projection.
; The negative-result adapter constructs an exact D1:0 by comparing against
; ATOM of a non-empty quoted list. No three-part expected-result COND remains.

(00001001 content-store-no?
  (00001000 (value)
    (00100010 value (00100010 (00000001 d1-no-left) (00000001 d1-no-right)))))

; Canonical three-part COND uses structural expected-result data, not truthiness.
(00001001 content-store-authority-witness
  (00001000 ()
    (10011101 ((value (00000001 (lambda (x) x)))
           (written (fs-write (fs-empty) "code" value))
           (fs (00000101 written))
           (root-a (fs-serialize-root fs))
           (root-b (fs-serialize-root fs))
           (object-a (fs-serialize-object value))
           (object-b (fs-serialize-object value))
           (root-relation (00100010 root-a root-b))
           (object-relation (00100010 object-a object-b))
           (direct
             (world-tell (empty-world) (00000001 zoo) (00000001 ((has-fur cat)))))
           (retold
             (world-tell
               (world-retract
                 (world-tell (empty-world) (00000001 zoo) (00000001 ((has-fur cat))))
                 (00000001 zoo) (00000001 ((has-fur cat))))
               (00000001 zoo) (00000001 ((has-fur cat)))))
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
                      (laws
                        root-image-deterministic
                        object-image-deterministic
                        equal-current-projection))))
                ((content-store-no? projection-relation)
                  (00000001
                    (content-store-authority-witness
                      (status fail)
                      (law equal-current-projection)))))
            ((content-store-no? object-relation)
              (00000001
                (content-store-authority-witness
                  (status fail)
                  (law object-image-deterministic)))))
        ((content-store-no? root-relation)
          (00000001
            (content-store-authority-witness
              (status fail)
              (law root-image-deterministic))))))))
))
