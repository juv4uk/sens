; #114/#220/#275 — Lisp owns the semantic relation verdicts used by the
; content-store regression evidence.  Rust may observe serialization bytes and
; store cardinality, but it must not freeze `equal?` as historical t/().
;
; This witness deliberately says nothing about host mechanics.  It only asks
; the language whether the two deterministic images are structurally the same
; and whether two Worlds with equal current clauses have the same projection.

(def content-store-authority-witness
  (lambda ()
    (let* ((value (quote (lambda (x) x)))
           (written (fs-write (fs-empty) "code" value))
           (fs (car written))
           (root-a (fs-serialize-root fs))
           (root-b (fs-serialize-root fs))
           (object-a (fs-serialize-object value))
           (object-b (fs-serialize-object value))
           (root-relation (equal? root-a root-b))
           (object-relation (equal? object-a object-b))
           (direct
             (world-tell (empty-world) (quote zoo) (quote ((has-fur cat)))))
           (retold
             (world-tell
               (world-retract
                 (world-tell (empty-world) (quote zoo) (quote ((has-fur cat))))
                 (quote zoo) (quote ((has-fur cat))))
               (quote zoo) (quote ((has-fur cat)))))
           (projection-relation
             (equal?
               (world-clauses direct (quote zoo))
               (world-clauses retold (quote zoo)))))
      (cond
        (root-relation (1)
          (cond
            (object-relation (1)
              (cond
                (projection-relation (1)
                  (quote
                    (content-store-authority-witness
                      (status pass)
                      (laws
                        root-image-deterministic
                        object-image-deterministic
                        equal-current-projection))))
                (projection-relation (0)
                  (quote
                    (content-store-authority-witness
                      (status fail)
                      (law equal-current-projection))))))
            (object-relation (0)
              (quote
                (content-store-authority-witness
                  (status fail)
                  (law object-image-deterministic))))))
        (root-relation (0)
          (quote
            (content-store-authority-witness
              (status fail)
              (law root-image-deterministic))))))))
