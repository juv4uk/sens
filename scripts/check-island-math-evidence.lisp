; #990 — fail-closed validation for mechanism evidence.
; Evidence may only attach to an existing Canon/function-table SID and to an
; executor route already admitted by #1046 mechanism metadata. This checker does
; not define operation names, meaning, law, domain, or semantic equivalence.

(00001001 registry
  (00000101 (01001011 (10100110 "lib/surface/semantic-registry.lisp"))))

(00001001 mechanisms
  (00000101 (01001011 (10100110 "lib/function-table-mechanisms.lisp"))))

(00001001 evidence
  (00000101 (01001011 (10100110 "lib/island-math-evidence.lisp"))))

(00001001 registry-rows registry)

(00001001 evidence-sid-bits
  (00001000 (sid)
    (00000111
      ((00100100 sid) sid)
      ((00000010 (00000001 ()))
       (01001100 sid)))))

(00001001 empty-list?
  (00001000 (values)
    (00000111
      ((00000010 values)
       (00000011 values (00000001 ())))
      ((00000010 (00000001 ()))
       (00000010 (00000001 (00000000)))))))

(00001001 four-item-row?
  (00001000 (row)
    (00000111
      ((00000010 row)
       (00000010 (00000001 (00000000))))
      ((00000010 (00000110 row))
       (00000010 (00000001 (00000000))))
      ((00000010 (00000110 (00000110 row)))
       (00000010 (00000001 (00000000))))
      ((00000010 (00000110 (00000110 (00000110 row))))
       (00000010 (00000001 (00000000))))
      ((00000010
         (00000110 (00000110 (00000110 (00000110 row)))))
       (00000011
         (00000110 (00000110 (00000110 (00000110 row))))
         (00000001 ())))
      ((00000010 (00000001 ()))
       (00000010 (00000001 (00000000)))))))


(00001001 find-section
  (00001000 (name sections)
    (00000111
      ((empty-list? sections)
       (00000001 ()))
      ((00000011 (00000101 (00000101 sections)) name)
       (00000101 sections))
      ((00000011 0 0)
       (find-section name (00000110 sections))))))

(00001001 mechanism-rows
  (00000110 (find-section (00000001 rows) mechanisms)))

(00001001 evidence-rows
  (00000110 (find-section (00000001 rows) evidence)))

(00001001 registry-has-sid?
  (00001000 (sid rows)
    (00000111
      ((empty-list? rows)
       (00000001 no))
      ((00100010 sid (00000101 (00000101 rows)))
       (00000001 yes))
      ((00000011 0 0)
       (registry-has-sid? sid (00000110 rows))))))

(00001001 mechanism-has-route?
  (00001000 (sid executor rows)
    (00000111
      ((empty-list? rows)
       (00000001 no))
      ((00100010
         (evidence-sid-bits sid)
         (evidence-sid-bits (00000101 (00000101 rows))))
       (00000111
         ((00000011 executor (00101111 (00000101 rows)))
          (00000001 yes))
         ((00000011 0 0)
          (mechanism-has-route? sid executor (00000110 rows)))))
      ((00000011 0 0)
       (mechanism-has-route? sid executor (00000110 rows))))))

(00001001 evidence-has-route?
  (00001000 (sid executor rows)
    (00000111
      ((empty-list? rows)
       (00000001 no))
      ((00100010 sid (00000101 (00000101 rows)))
       (00000111
         ((00000011 executor (00101111 (00000101 rows)))
          (00000001 yes))
         ((00000011 0 0)
          (evidence-has-route? sid executor (00000110 rows)))))
      ((00000011 0 0)
       (evidence-has-route? sid executor (00000110 rows))))))

(00001001 admitted-executor?
  (00001000 (executor)
    (00000111
      ((00000011 executor (00000001 common-lisp)) (00000001 yes))
      ((00000011 executor (00000001 prolog)) (00000001 yes))
      ((00000011 executor (00000001 clips)) (00000001 yes))
      ((00000011 executor (00000001 datalog)) (00000001 yes))
      ((00000011 0 0) (00000001 no)))))

(00001001 admitted-status?
  (00001000 (status)
    (00000111
      ((00000011 status (00000001 execution-witness)) (00000001 yes))
      ((00000011 0 0) (00000001 no)))))

(00001001 forbidden-semantic-symbol?
  (00001000 (value)
    (00000111
      ((00000011 value (00000001 operation)) (00000001 yes))
      ((00000011 value (00000001 meaning)) (00000001 yes))
      ((00000011 value (00000001 law)) (00000001 yes))
      ((00000011 value (00000001 domain)) (00000001 yes))
      ((00000011 value (00000001 operand-domain)) (00000001 yes))
      ((00000011 value (00000001 result-domain)) (00000001 yes))
      ((00000011 0 0) (00000001 no)))))

(00001001 contains-forbidden-semantic-section?
  (00001000 (sections)
    (00000111
      ((empty-list? sections)
       (00000001 no))
      ((00000011
         (forbidden-semantic-symbol? (00000101 (00000101 sections)))
         (00000001 yes))
       (00000001 yes))
      ((00000011 0 0)
       (contains-forbidden-semantic-section? (00000110 sections))))))

(00001001 validate-rows
  (00001000 (rows)
    (00000111
      ((empty-list? rows)
       (00000001 (island-math-evidence-ok)))
      ((four-item-row? (00000101 rows))
       (00000111
         ((00100100 (00110001 (00000101 rows)))
          (00000111
            ((00000011
               (registry-has-sid?
                 (00000101 (00000101 rows))
                 registry-rows)
               (00000001 yes))
             (00000111
               ((00000011
                  (admitted-executor? (00101111 (00000101 rows)))
                  (00000001 yes))
                (00000111
                  ((00000011
                     (mechanism-has-route?
                       (00000101 (00000101 rows))
                       (00101111 (00000101 rows))
                       mechanism-rows)
                     (00000001 yes))
                   (00000111
                     ((00000011
                        (admitted-status? (00110000 (00000101 rows)))
                        (00000001 yes))
                      (00000111
                        ((00000011
                           (evidence-has-route?
                             (00000101 (00000101 rows))
                             (00101111 (00000101 rows))
                             (00000110 rows))
                           (00000001 yes))
                         (00100111
                           (00000001 island-math-evidence-violation)
                           (00000001 duplicate-executor-evidence)
                           (00000101 (00000101 rows))
                           (00101111 (00000101 rows))))
                        ((00000011 0 0)
                         (validate-rows (00000110 rows)))))
                     ((00000011 0 0)
                      (00100111
                        (00000001 island-math-evidence-violation)
                        (00000001 unsupported-status)
                        (00000101 (00000101 rows))
                        (00110000 (00000101 rows))))))
                  ((00000011 0 0)
                   (00100111
                     (00000001 island-math-evidence-violation)
                     (00000001 executor-route-not-admitted-by-canon-projection)
                     (00000101 (00000101 rows))
                     (00101111 (00000101 rows))))))
               ((00000011 0 0)
                (00100111
                  (00000001 island-math-evidence-violation)
                  (00000001 unsupported-executor)
                  (00000101 (00000101 rows))
                  (00101111 (00000101 rows))))))
            ((00000011 0 0)
             (00100111
               (00000001 island-math-evidence-violation)
               (00000001 sid-not-in-canon-function-table)
               (00000101 (00000101 rows))))))
         ((00000011 0 0)
          (00100111
            (00000001 island-math-evidence-violation)
            (00000001 provenance-must-be-string)
            (00000101 (00000101 rows))
            (00101111 (00000101 rows))))))
      ((00000011 0 0)
       (00100111
         (00000001 island-math-evidence-violation)
         (00000001 invalid-evidence-row-shape)
         (00000101 (00000101 rows)))))))

(00001001 same-sid?
  (00001000 (sid rows)
    (00000111
      ((empty-list? rows)
       (00000001 yes))
      ((00100010 sid (00000101 (00000101 rows)))
       (same-sid? sid (00000110 rows)))
      ((00000011 0 0)
       (00000001 no)))))

(00001001 four-island-slice?
  (00001000 (sid)
    (00000111
      ((00000011
         (evidence-has-route? sid (00000001 common-lisp) evidence-rows)
         (00000001 no))
       (00000001 no))
      ((00000011
         (evidence-has-route? sid (00000001 prolog) evidence-rows)
         (00000001 no))
       (00000001 no))
      ((00000011
         (evidence-has-route? sid (00000001 clips) evidence-rows)
         (00000001 no))
       (00000001 no))
      ((00000011
         (evidence-has-route? sid (00000001 datalog) evidence-rows)
         (00000001 no))
       (00000001 no))
      ((00000011 0 0)
       (00000001 yes)))))

(00001001 row-verdict (validate-rows evidence-rows))

(00001001 verdict
  (00000111
    ((00000011
       (contains-forbidden-semantic-section? evidence)
       (00000001 yes))
     (00000001
       (island-math-evidence-violation semantic-field-forbidden)))
    ((empty-list? evidence-rows)
     (00000001
       (island-math-evidence-violation empty-evidence)))
    ((00100010
       row-verdict
       (00000001 (island-math-evidence-ok)))
     (00000111
       ((00000011
          (same-sid?
            (00000101 (00000101 evidence-rows))
            evidence-rows)
          (00000001 no))
        (00000001
          (island-math-evidence-violation
            first-slice-must-have-one-sid)))
       ((00000011
          (four-island-slice?
            (00000101 (00000101 evidence-rows)))
          (00000001 no))
        (00000001
          (island-math-evidence-violation
            missing-required-four-island-slice)))
       ((00000011 0 0)
        (00000001 (island-math-evidence-ok)))))
    ((00000011 0 0) row-verdict)))

(01001000 verdict)
