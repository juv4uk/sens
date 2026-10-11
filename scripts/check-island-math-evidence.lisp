; #990 — fail-closed validation for mechanism evidence.
; Evidence may only attach to an existing Canon/function-table SID and to an
; executor route already admitted by #1046 mechanism metadata. This checker does
; not define operation names, meaning, law, domain, or semantic equivalence.

(0011 registry
  (100 (110101001 (110110111 "lib/surface/semantic-registry.lisp"))))

(0011 mechanisms
  (100 (110101001 (110110111 "lib/function-table-mechanisms.lisp"))))

(0011 evidence
  (100 (110101001 (110110111 "lib/island-math-evidence.lisp"))))

(0011 registry-rows registry)

(0011 evidence-sid-bits
  (0010 (sid)
    (110
      ((110100110 sid) sid)
      (t (11110100 sid)))))

(0011 find-section
  (0010 (name sections)
    (110
      ((010 sections) () (001 ()))
      ((010 sections) (0)
       (110
         ((101 (100 (100 sections)) name) (1)
          (100 sections))
         ((101 (100 (100 sections)) name) (0)
          (find-section name (011 sections))))))))

(0011 mechanism-rows
  (011 (find-section (001 rows) mechanisms)))

(0011 evidence-rows
  (011 (find-section (001 rows) evidence)))

(0011 registry-has-sid?
  (0010 (sid rows)
    (110
      ((010 rows) () (001 no))
      ((010 rows) (0)
       (110
         ((11110111 sid (100 (100 rows))) (1) (001 yes))
         ((11110111 sid (100 (100 rows))) (0)
          (registry-has-sid? sid (011 rows))))))))

(0011 mechanism-has-route?
  (0010 (sid executor rows)
    (110
      ((010 rows) () (001 no))
      ((010 rows) (0)
       (001000 ((row (100 rows)))
         (110
           ((11110111 (evidence-sid-bits sid) (evidence-sid-bits (100 row))) (1)
            (110
              ((101 executor (1001 row)) (1) (001 yes))
              ((101 executor (1001 row)) (0)
               (mechanism-has-route? sid executor (011 rows)))))
           ((11110111 (evidence-sid-bits sid) (evidence-sid-bits (100 row))) (0)
            (mechanism-has-route? sid executor (011 rows)))))))))

(0011 evidence-has-route?
  (0010 (sid executor rows)
    (110
      ((010 rows) () (001 no))
      ((010 rows) (0)
       (001000 ((row (100 rows)))
         (110
           ((11110111 sid (100 row)) (1)
            (110
              ((101 executor (1001 row)) (1) (001 yes))
              ((101 executor (1001 row)) (0)
               (evidence-has-route? sid executor (011 rows)))))
           ((11110111 sid (100 row)) (0)
            (evidence-has-route? sid executor (011 rows)))))))))

(0011 admitted-executor?
  (0010 (executor)
    (110
      ((101 executor (001 common-lisp)) (1) (001 yes))
      ((101 executor (001 prolog)) (1) (001 yes))
      ((101 executor (001 clips)) (1) (001 yes))
      ((101 executor (001 datalog)) (1) (001 yes))
      (t (001 no)))))

(0011 admitted-status?
  (0010 (status)
    (110
      ((101 status (001 execution-witness)) (1) (001 yes))
      (t (001 no)))))

(0011 forbidden-semantic-symbol?
  (0010 (value)
    (110
      ((010 value) () (001 no))
      ((010 value) (0) (001 no))
      ((010 value) (1)
       (110
         ((101 value (001 operation)) (1) (001 yes))
         ((101 value (001 meaning)) (1) (001 yes))
         ((101 value (001 law)) (1) (001 yes))
         ((101 value (001 domain)) (1) (001 yes))
         ((101 value (001 operand-domain)) (1) (001 yes))
         ((101 value (001 result-domain)) (1) (001 yes))
         (t (001 no)))))))

(0011 contains-forbidden-semantic-section?
  (0010 (sections)
    (110
      ((010 sections) () (001 no))
      ((010 sections) (0)
       (001000 ((section (100 sections)))
         (110
           ((010 section) (0)
            (110
              ((101 (forbidden-semantic-symbol? (100 section)) (001 yes))
               (1)
               (001 yes))
              (t (contains-forbidden-semantic-section? (011 sections)))))
           (t (contains-forbidden-semantic-section? (011 sections)))))))))

(0011 validate-rows
  (0010 (rows)
    (110
      ((010 rows) ()
       (001 (island-math-evidence-ok)))
      ((010 rows) (0)
       (001001 ((row (100 rows))
              (sid (100 row))
              (executor (1001 row))
              (status (10011 row))
              (provenance-ref (100111 row)))
         (110
           ((11110111 (000000 row) 4)
            (0)
            (1110 (001 island-math-evidence-violation)
                  (001 invalid-evidence-row-shape) sid))
           ((110100110 provenance-ref)
            (0)
            (1110 (001 island-math-evidence-violation)
                  (001 provenance-must-be-string) sid executor))
           ((101 (registry-has-sid? sid registry-rows) (001 no))
            (1)
            (1110 (001 island-math-evidence-violation)
                  (001 sid-not-in-canon-function-table) sid))
           ((101 (admitted-executor? executor) (001 no))
            (1)
            (1110 (001 island-math-evidence-violation)
                  (001 unsupported-executor) sid executor))
           ((101 (mechanism-has-route? sid executor mechanism-rows) (001 no))
            (1)
            (1110 (001 island-math-evidence-violation)
                  (001 executor-route-not-admitted-by-canon-projection) sid executor))
           ((101 (admitted-status? status) (001 no))
            (1)
            (1110 (001 island-math-evidence-violation)
                  (001 unsupported-status) sid status))
           ((101 (evidence-has-route? sid executor (011 rows)) (001 yes))
            (1)
            (1110 (001 island-math-evidence-violation)
                  (001 duplicate-executor-evidence) sid executor))
           (t (validate-rows (011 rows)))))))))

(0011 same-sid?
  (0010 (sid rows)
    (110
      ((010 rows) () (001 yes))
      ((010 rows) (0)
       (110
         ((11110111 sid (100 (100 rows))) (1)
          (same-sid? sid (011 rows)))
         ((11110111 sid (100 (100 rows))) (0)
          (001 no)))))))

(0011 four-island-slice?
  (0010 (sid)
    (110
      ((101 (evidence-has-route? sid (001 common-lisp) evidence-rows) (001 no))
       (1) (001 no))
      ((101 (evidence-has-route? sid (001 prolog) evidence-rows) (001 no))
       (1) (001 no))
      ((101 (evidence-has-route? sid (001 clips) evidence-rows) (001 no))
       (1) (001 no))
      ((101 (evidence-has-route? sid (001 datalog) evidence-rows) (001 no))
       (1) (001 no))
      (t (001 yes)))))

(0011 row-verdict (validate-rows evidence-rows))

(0011 verdict
  (110
    ((101 (contains-forbidden-semantic-section? evidence) (001 yes))
     (1)
     (001 (island-math-evidence-violation semantic-field-forbidden)))
    ((010 evidence-rows) ()
     (001 (island-math-evidence-violation empty-evidence)))
    ((11110111 row-verdict (001 (island-math-evidence-ok)))
     (1)
     (001000 ((target-sid (100 (100 evidence-rows))))
       (110
         ((101 (same-sid? target-sid evidence-rows) (001 no))
          (1)
          (001 (island-math-evidence-violation first-slice-must-have-one-sid)))
         ((101 (four-island-slice? target-sid) (001 no))
          (1)
          (001 (island-math-evidence-violation missing-required-four-island-slice)))
         (t (001 (island-math-evidence-ok))))))
    (t row-verdict)))

(11011011 verdict)
