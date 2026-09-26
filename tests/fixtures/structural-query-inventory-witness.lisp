; #218 STRUCTURAL-QUERY-1 — Lisp-owned inventory completeness witness.
;
; Rust may transport the two source documents into these bindings:
;   structural-query-inventory-document
;   public-surface-inventory-document
; but the coverage/classification verdict stays in Lisp.
;
; The witness deliberately derives the predicate surface set from
; lib/surface/uk-inventory.lisp instead of copying the 18 names here.

(00001001 sqi-field
  (00001000 (key row)
    (10011100 ((entry (00101101 key row)))
      (00000111
        ((00000010 entry) () (00000001 ()))
        ((00000010 entry) (1) (00000001 ()))
        (t (00000110 entry))))))

(00001001 sqi-find-tag
  (00001000 (tag entries)
    (00000111
      ((00000010 entries) () (00000001 ()))
      ((00000010 entries) (1) (00000001 ()))
      ((10011010 (10110001 (00000010 (00000101 entries)))
            (00000011 (00000101 (00000101 entries)) tag))
       (00000101 entries))
      (t (sqi-find-tag tag (00000110 entries))))))

(00001001 sqi-public-predicates
  (00001000 ()
    (10011100 ((entry (sqi-find-tag (00000001 public-predicates)
                               (00000110 public-surface-inventory-document))))
      (00000111
        ((00000010 entry) () (00000001 ()))
        ((00000010 entry) (1) (00000001 ()))
        (t (00000101 (00000110 entry)))))))

(00001001 sqi-rows
  (00001000 ()
    (00000110 structural-query-inventory-document)))

(00001001 sqi-count-surface
  (00001000 (surface rows)
    (00000111
      ((00000010 rows) () 0)
      ((00000010 rows) (1) 0)
      ((00000011 (sqi-field (00000001 surface) (00000101 rows)) surface)
       (00001100 1 (sqi-count-surface surface (00000110 rows))))
      (t
       (sqi-count-surface surface (00000110 rows))))))

(00001001 sqi-required-row?
  (00001000 (row)
    (10011010
      (10110001 (00000010 (00101101 (00000001 identity) row)))
      (10110001 (00000010 (00101101 (00000001 surface) row)))
      (10110001 (00000010 (00101101 (00000001 producer) row)))
      (10110001 (00000010 (00101101 (00000001 current-result) row)))
      (10110001 (00000010 (00101101 (00000001 question-domain) row)))
      (10110001 (00000010 (00101101 (00000001 mathematical-binary?) row)))
      (10110001 (00000010 (00101101 (00000001 owner) row)))
      (10110001 (00000010 (00101101 (00000001 consumer-class) row)))
      (10110001 (00000010 (00101101 (00000001 compatibility-impact) row)))
      (10110001 (00000010 (00101101 (00000001 migration) row))))))

(00001001 sqi-all-public-covered-once?
  (00001000 (predicates rows)
    (00000111
      ((00000010 predicates) () t)
      ((00000010 predicates) (1) t)
      ((00000011 (sqi-count-surface (00000101 predicates) rows) 1)
       (sqi-all-public-covered-once? (00000110 predicates) rows))
      (t (00000001 ())))))

(00001001 sqi-no-extra-surfaces?
  (00001000 (rows predicates)
    (00000111
      ((00000010 rows) () t)
      ((00000010 rows) (1) t)
      ((10011010 (sqi-required-row? (00000101 rows))
            (00101100 (sqi-field (00000001 surface) (00000101 rows)) predicates))
       (sqi-no-extra-surfaces? (00000110 rows) predicates))
      (t (00000001 ())))))

(00001001 sqi-math-delegation-valid?
  (00001000 (rows)
    (00000111
      ((00000010 rows) () t)
      ((00000010 rows) (1) t)
      (t
       (10011100 ((row (00000101 rows)))
         (00000111
           ((00000011 (sqi-field (00000001 mathematical-binary?) row) (00000001 yes-domain-bounded))
            (00000111
              ((00000011 (sqi-field (00000001 owner) row) (00000001 exact-q-decision-216))
               (sqi-math-delegation-valid? (00000110 rows)))
              (t (00000001 ()))))
           (t (sqi-math-delegation-valid? (00000110 rows)))))))))

(00001001 structural-query-inventory-witness
  (00001000 ()
    (10011100 ((predicates (sqi-public-predicates))
          (rows (sqi-rows)))
      (00000111
        ((10011010 (00000011 (00101000 predicates) 18)
              (00000011 (00101000 rows) 18)
              (sqi-all-public-covered-once? predicates rows)
              (sqi-no-extra-surfaces? rows predicates)
              (sqi-math-delegation-valid? rows))
         (00100111 (00000001 structural-query-inventory-witness)
               (00100111 (00000001 status) (00000001 pass))
               (00100111 (00000001 public-predicate-count) (00101000 predicates))
               (00100111 (00000001 classified-row-count) (00101000 rows))))
        (t
         (00100111 (00000001 structural-query-inventory-witness)
               (00100111 (00000001 status) (00000001 fail))
               (00100111 (00000001 public-predicate-count) (00101000 predicates))
               (00100111 (00000001 classified-row-count) (00101000 rows))))))))
