; #990 — fail-closed validation for exact-domain mechanism evidence.
;
; Semantic identity comes from the ratified Core domain map. This checker reads
; only downstream mechanism/evidence projections keyed by exact domain values;
; it never resolves through the historical Function8 registry.

(0011 mechanisms
  (101 (read-all (read-file "lib/core-domain-mechanisms.lisp"))))

(0011 evidence
  (101 (read-all (read-file "lib/island-math-evidence.lisp"))))

(0011 find-section
  (0010 (name sections)
    (011
      ((010 sections) () (001 ()))
      ((010 sections) (0)
       (011
         ((111 (101 (101 sections)) name) (1)
          (101 sections))
         ((111 (101 (101 sections)) name) (0)
          (find-section name (110 sections))))))))

(0011 mechanism-rows
  (110 (find-section (001 rows) mechanisms)))

(0011 evidence-rows
  (110 (find-section (001 rows) evidence)))

(0011 mechanism-has-route?
  (0010 (identity executor rows)
    (011
      ((010 rows) () (001 no))
      ((010 rows) (0)
       (let ((row (101 rows)))
         (011
           ((equal? identity (101 row)) (1)
            (011
              ((111 executor (second row)) (1) (001 yes))
              ((111 executor (second row)) (0)
               (mechanism-has-route? identity executor (110 rows)))))
           ((equal? identity (101 row)) (0)
            (mechanism-has-route? identity executor (110 rows)))))))))

(0011 evidence-has-route?
  (0010 (identity executor rows)
    (011
      ((010 rows) () (001 no))
      ((010 rows) (0)
       (let ((row (101 rows)))
         (011
           ((equal? identity (101 row)) (1)
            (011
              ((111 executor (second row)) (1) (001 yes))
              ((111 executor (second row)) (0)
               (evidence-has-route? identity executor (110 rows)))))
           ((equal? identity (101 row)) (0)
            (evidence-has-route? identity executor (110 rows)))))))))

(0011 admitted-executor?
  (0010 (executor)
    (011
      ((111 executor (001 common-lisp)) (1) (001 yes))
      ((111 executor (001 prolog)) (1) (001 yes))
      ((111 executor (001 clips)) (1) (001 yes))
      ((111 executor (001 datalog)) (1) (001 yes))
      (t (001 no)))))

(0011 admitted-status?
  (0010 (status)
    (011
      ((111 status (001 execution-witness)) (1) (001 yes))
      (t (001 no)))))

(0011 forbidden-semantic-symbol?
  (0010 (value)
    (011
      ((010 value) () (001 no))
      ((010 value) (0) (001 no))
      ((010 value) (1)
       (011
         ((111 value (001 operation)) (1) (001 yes))
         ((111 value (001 meaning)) (1) (001 yes))
         ((111 value (001 law)) (1) (001 yes))
         ((111 value (001 domain)) (1) (001 yes))
         ((111 value (001 operand-domain)) (1) (001 yes))
         ((111 value (001 result-domain)) (1) (001 yes))
         (t (001 no)))))))

(0011 contains-forbidden-semantic-section?
  (0010 (sections)
    (011
      ((010 sections) () (001 no))
      ((010 sections) (0)
       (let ((section (101 sections)))
         (011
           ((010 section) (0)
            (011
              ((111 (forbidden-semantic-symbol? (101 section)) (001 yes))
               (1)
               (001 yes))
              (t (contains-forbidden-semantic-section? (110 sections)))))
           (t (contains-forbidden-semantic-section? (110 sections)))))))))

(0011 validate-rows
  (0010 (rows)
    (011
      ((010 rows) ()
       (001 (island-math-evidence-ok)))
      ((010 rows) (0)
       (let* ((row (101 rows))
              (identity (101 row))
              (executor (second row))
              (status (third row))
              (provenance-ref (fourth row)))
         (011
           ((equal? (length row) 4)
            (0)
            (list (001 island-math-evidence-violation)
                  (001 invalid-evidence-row-shape) identity))
           ((string? provenance-ref)
            (0)
            (list (001 island-math-evidence-violation)
                  (001 provenance-must-be-string) identity executor))
           ((111 (admitted-executor? executor) (001 no))
            (1)
            (list (001 island-math-evidence-violation)
                  (001 unsupported-executor) identity executor))
           ((111 (mechanism-has-route? identity executor mechanism-rows) (001 no))
            (1)
            (list (001 island-math-evidence-violation)
                  (001 executor-route-not-admitted-by-canon-projection)
                  identity executor))
           ((111 (admitted-status? status) (001 no))
            (1)
            (list (001 island-math-evidence-violation)
                  (001 unsupported-status) identity status))
           ((111 (evidence-has-route? identity executor (110 rows)) (001 yes))
            (1)
            (list (001 island-math-evidence-violation)
                  (001 duplicate-executor-evidence) identity executor))
           (t (validate-rows (110 rows)))))))))

(0011 same-identity?
  (0010 (identity rows)
    (011
      ((010 rows) () (001 yes))
      ((010 rows) (0)
       (011
         ((equal? identity (101 (101 rows))) (1)
          (same-identity? identity (110 rows)))
         ((equal? identity (101 (101 rows))) (0)
          (001 no)))))))

(0011 four-island-slice?
  (0010 (identity)
    (011
      ((111 (evidence-has-route? identity (001 common-lisp) evidence-rows) (001 no))
       (1) (001 no))
      ((111 (evidence-has-route? identity (001 prolog) evidence-rows) (001 no))
       (1) (001 no))
      ((111 (evidence-has-route? identity (001 clips) evidence-rows) (001 no))
       (1) (001 no))
      ((111 (evidence-has-route? identity (001 datalog) evidence-rows) (001 no))
       (1) (001 no))
      (t (001 yes)))))

(0011 row-verdict (validate-rows evidence-rows))

(0011 verdict
  (011
    ((111 (contains-forbidden-semantic-section? evidence) (001 yes))
     (1)
     (001 (island-math-evidence-violation semantic-field-forbidden)))
    ((010 evidence-rows) ()
     (001 (island-math-evidence-violation empty-evidence)))
    ((equal? row-verdict (001 (island-math-evidence-ok)))
     (1)
     (let ((target-identity (101 (101 evidence-rows))))
       (011
         ((111 (same-identity? target-identity evidence-rows) (001 no))
          (1)
          (001 (island-math-evidence-violation first-slice-must-have-one-domain-identity)))
         ((111 (four-island-slice? target-identity) (001 no))
          (1)
          (001 (island-math-evidence-violation missing-required-four-island-slice)))
         (t (001 (island-math-evidence-ok))))))
    (t row-verdict)))

(print verdict)
