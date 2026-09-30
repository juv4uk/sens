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
      (t (01001100 sid)))))

(00001001 find-section
  (00001000 (name sections)
    (00000111
      ((00000010 sections) () (00000001 ()))
      ((00000010 sections) (#b0)
       (00000111
         ((00000011 (00000101 (00000101 sections)) name) (#b1)
          (00000101 sections))
         ((00000011 (00000101 (00000101 sections)) name) (#b0)
          (find-section name (00000110 sections))))))))

(00001001 mechanism-rows
  (00000110 (find-section (00000001 rows) mechanisms)))

(00001001 evidence-rows
  (00000110 (find-section (00000001 rows) evidence)))

(00001001 registry-has-sid?
  (00001000 (sid rows)
    (00000111
      ((00000010 rows) () (00000001 no))
      ((00000010 rows) (#b0)
       (00000111
         ((00100010 sid (00000101 (00000101 rows))) (#b1) (00000001 yes))
         ((00100010 sid (00000101 (00000101 rows))) (#b0)
          (registry-has-sid? sid (00000110 rows))))))))

(00001001 mechanism-has-route?
  (00001000 (sid executor rows)
    (00000111
      ((00000010 rows) () (00000001 no))
      ((00000010 rows) (#b0)
       (10011100 ((row (00000101 rows)))
         (00000111
           ((00100010 (evidence-sid-bits sid) (evidence-sid-bits (00000101 row))) (#b1)
            (00000111
              ((00000011 executor (00101111 row)) (#b1) (00000001 yes))
              ((00000011 executor (00101111 row)) (#b0)
               (mechanism-has-route? sid executor (00000110 rows)))))
           ((00100010 (evidence-sid-bits sid) (evidence-sid-bits (00000101 row))) (#b0)
            (mechanism-has-route? sid executor (00000110 rows)))))))))

(00001001 evidence-has-route?
  (00001000 (sid executor rows)
    (00000111
      ((00000010 rows) () (00000001 no))
      ((00000010 rows) (#b0)
       (10011100 ((row (00000101 rows)))
         (00000111
           ((00100010 sid (00000101 row)) (#b1)
            (00000111
              ((00000011 executor (00101111 row)) (#b1) (00000001 yes))
              ((00000011 executor (00101111 row)) (#b0)
               (evidence-has-route? sid executor (00000110 rows)))))
           ((00100010 sid (00000101 row)) (#b0)
            (evidence-has-route? sid executor (00000110 rows)))))))))

(00001001 admitted-executor?
  (00001000 (executor)
    (00000111
      ((00000011 executor (00000001 common-lisp)) (#b1) (00000001 yes))
      ((00000011 executor (00000001 prolog)) (#b1) (00000001 yes))
      ((00000011 executor (00000001 clips)) (#b1) (00000001 yes))
      ((00000011 executor (00000001 datalog)) (#b1) (00000001 yes))
      (t (00000001 no)))))

(00001001 admitted-status?
  (00001000 (status)
    (00000111
      ((00000011 status (00000001 execution-witness)) (#b1) (00000001 yes))
      (t (00000001 no)))))

(00001001 forbidden-semantic-symbol?
  (00001000 (value)
    (00000111
      ((00000010 value) () (00000001 no))
      ((00000010 value) (#b0) (00000001 no))
      ((00000010 value) (#b1)
       (00000111
         ((00000011 value (00000001 operation)) (#b1) (00000001 yes))
         ((00000011 value (00000001 meaning)) (#b1) (00000001 yes))
         ((00000011 value (00000001 law)) (#b1) (00000001 yes))
         ((00000011 value (00000001 domain)) (#b1) (00000001 yes))
         ((00000011 value (00000001 operand-domain)) (#b1) (00000001 yes))
         ((00000011 value (00000001 result-domain)) (#b1) (00000001 yes))
         (t (00000001 no)))))))

(00001001 contains-forbidden-semantic-section?
  (00001000 (sections)
    (00000111
      ((00000010 sections) () (00000001 no))
      ((00000010 sections) (#b0)
       (10011100 ((section (00000101 sections)))
         (00000111
           ((00000010 section) (#b0)
            (00000111
              ((00000011 (forbidden-semantic-symbol? (00000101 section)) (00000001 yes))
               (#b1)
               (00000001 yes))
              (t (contains-forbidden-semantic-section? (00000110 sections)))))
           (t (contains-forbidden-semantic-section? (00000110 sections)))))))))

(00001001 validate-rows
  (00001000 (rows)
    (00000111
      ((00000010 rows) ()
       (00000001 (island-math-evidence-ok)))
      ((00000010 rows) (#b0)
       (10011101 ((row (00000101 rows))
              (sid (00000101 row))
              (executor (00101111 row))
              (status (00110000 row))
              (provenance-ref (00110001 row)))
         (00000111
           ((00100010 (00101000 row) #b100)
            (#b0)
            (00100111 (00000001 island-math-evidence-violation)
                  (00000001 invalid-evidence-row-shape) sid))
           ((00100100 provenance-ref)
            (#b0)
            (00100111 (00000001 island-math-evidence-violation)
                  (00000001 provenance-must-be-string) sid executor))
           ((00000011 (registry-has-sid? sid registry-rows) (00000001 no))
            (#b1)
            (00100111 (00000001 island-math-evidence-violation)
                  (00000001 sid-not-in-canon-function-table) sid))
           ((00000011 (admitted-executor? executor) (00000001 no))
            (#b1)
            (00100111 (00000001 island-math-evidence-violation)
                  (00000001 unsupported-executor) sid executor))
           ((00000011 (mechanism-has-route? sid executor mechanism-rows) (00000001 no))
            (#b1)
            (00100111 (00000001 island-math-evidence-violation)
                  (00000001 executor-route-not-admitted-by-canon-projection) sid executor))
           ((00000011 (admitted-status? status) (00000001 no))
            (#b1)
            (00100111 (00000001 island-math-evidence-violation)
                  (00000001 unsupported-status) sid status))
           ((00000011 (evidence-has-route? sid executor (00000110 rows)) (00000001 yes))
            (#b1)
            (00100111 (00000001 island-math-evidence-violation)
                  (00000001 duplicate-executor-evidence) sid executor))
           (t (validate-rows (00000110 rows)))))))))

(00001001 same-sid?
  (00001000 (sid rows)
    (00000111
      ((00000010 rows) () (00000001 yes))
      ((00000010 rows) (#b0)
       (00000111
         ((00100010 sid (00000101 (00000101 rows))) (#b1)
          (same-sid? sid (00000110 rows)))
         ((00100010 sid (00000101 (00000101 rows))) (#b0)
          (00000001 no)))))))

(00001001 four-island-slice?
  (00001000 (sid)
    (00000111
      ((00000011 (evidence-has-route? sid (00000001 common-lisp) evidence-rows) (00000001 no))
       (#b1) (00000001 no))
      ((00000011 (evidence-has-route? sid (00000001 prolog) evidence-rows) (00000001 no))
       (#b1) (00000001 no))
      ((00000011 (evidence-has-route? sid (00000001 clips) evidence-rows) (00000001 no))
       (#b1) (00000001 no))
      ((00000011 (evidence-has-route? sid (00000001 datalog) evidence-rows) (00000001 no))
       (#b1) (00000001 no))
      (t (00000001 yes)))))

(00001001 row-verdict (validate-rows evidence-rows))

(00001001 verdict
  (00000111
    ((00000011 (contains-forbidden-semantic-section? evidence) (00000001 yes))
     (#b1)
     (00000001 (island-math-evidence-violation semantic-field-forbidden)))
    ((00000010 evidence-rows) ()
     (00000001 (island-math-evidence-violation empty-evidence)))
    ((00100010 row-verdict (00000001 (island-math-evidence-ok)))
     (#b1)
     (10011100 ((target-sid (00000101 (00000101 evidence-rows))))
       (00000111
         ((00000011 (same-sid? target-sid evidence-rows) (00000001 no))
          (#b1)
          (00000001 (island-math-evidence-violation first-slice-must-have-one-sid)))
         ((00000011 (four-island-slice? target-sid) (00000001 no))
          (#b1)
          (00000001 (island-math-evidence-violation missing-required-four-island-slice)))
         (t (00000001 (island-math-evidence-ok))))))
    (t row-verdict)))

(01001000 verdict)
