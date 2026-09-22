; #990 — fail-closed validation for mechanism evidence.
; Evidence may only attach to an existing Canon/function-table SID and to an
; executor route already admitted by #1046 mechanism metadata. This checker does
; not define operation names, meaning, law, domain, or semantic equivalence.

(def registry
  (car (read-all (read-file "lib/surface/semantic-registry.lisp"))))

(def mechanisms
  (car (read-all (read-file "lib/function-table-mechanisms.lisp"))))

(def evidence
  (car (read-all (read-file "lib/island-math-evidence.lisp"))))

(def registry-rows
  (cond
    ((equal? (car registry) (quote (binary 8))) (structural-relation same) (cdr registry))
    ((equal? (car registry) (quote (binary 8))) (structural-relation distinct) registry)))

(def evidence-sid-text
  (lambda (sid)
    (cond
      ((string? sid) sid)
      (t (write-to-string sid)))))

(def find-section
  (lambda (name sections)
    (cond
      ((atom sections) (structural-kind empty-list) (quote ()))
      ((atom sections) (structural-kind pair)
       (cond
         ((eq (car (car sections)) name) (identity-relation same)
          (car sections))
         ((eq (car (car sections)) name) (identity-relation distinct)
          (find-section name (cdr sections))))))))

(def mechanism-rows
  (cdr (find-section (quote rows) mechanisms)))

(def evidence-rows
  (cdr (find-section (quote rows) evidence)))

(def registry-has-sid?
  (lambda (sid rows)
    (cond
      ((atom rows) (structural-kind empty-list) (quote no))
      ((atom rows) (structural-kind pair)
       (cond
         ((equal? sid (car (car rows))) (structural-relation same) (quote yes))
         ((equal? sid (car (car rows))) (structural-relation distinct)
          (registry-has-sid? sid (cdr rows))))))))

(def mechanism-has-route?
  (lambda (sid executor rows)
    (cond
      ((atom rows) (structural-kind empty-list) (quote no))
      ((atom rows) (structural-kind pair)
       (let ((row (car rows)))
         (cond
           ((equal? (evidence-sid-text sid) (evidence-sid-text (car row))) (structural-relation same)
            (cond
              ((eq executor (second row)) (identity-relation same) (quote yes))
              ((eq executor (second row)) (identity-relation distinct)
               (mechanism-has-route? sid executor (cdr rows)))))
           ((equal? (evidence-sid-text sid) (evidence-sid-text (car row))) (structural-relation distinct)
            (mechanism-has-route? sid executor (cdr rows)))))))))

(def evidence-has-route?
  (lambda (sid executor rows)
    (cond
      ((atom rows) (structural-kind empty-list) (quote no))
      ((atom rows) (structural-kind pair)
       (let ((row (car rows)))
         (cond
           ((equal? sid (car row)) (structural-relation same)
            (cond
              ((eq executor (second row)) (identity-relation same) (quote yes))
              ((eq executor (second row)) (identity-relation distinct)
               (evidence-has-route? sid executor (cdr rows)))))
           ((equal? sid (car row)) (structural-relation distinct)
            (evidence-has-route? sid executor (cdr rows)))))))))

(def admitted-executor?
  (lambda (executor)
    (cond
      ((eq executor (quote common-lisp)) (identity-relation same) (quote yes))
      ((eq executor (quote prolog)) (identity-relation same) (quote yes))
      ((eq executor (quote clips)) (identity-relation same) (quote yes))
      ((eq executor (quote datalog)) (identity-relation same) (quote yes))
      (t (quote no)))))

(def admitted-status?
  (lambda (status)
    (cond
      ((eq status (quote execution-witness)) (identity-relation same) (quote yes))
      (t (quote no)))))

(def forbidden-semantic-symbol?
  (lambda (value)
    (cond
      ((atom value) (structural-kind empty-list) (quote no))
      ((atom value) (structural-kind pair) (quote no))
      ((atom value) (structural-kind atom)
       (cond
         ((eq value (quote operation)) (identity-relation same) (quote yes))
         ((eq value (quote meaning)) (identity-relation same) (quote yes))
         ((eq value (quote law)) (identity-relation same) (quote yes))
         ((eq value (quote domain)) (identity-relation same) (quote yes))
         ((eq value (quote operand-domain)) (identity-relation same) (quote yes))
         ((eq value (quote result-domain)) (identity-relation same) (quote yes))
         (t (quote no)))))))

(def contains-forbidden-semantic-section?
  (lambda (sections)
    (cond
      ((atom sections) (structural-kind empty-list) (quote no))
      ((atom sections) (structural-kind pair)
       (let ((section (car sections)))
         (cond
           ((atom section) (structural-kind pair)
            (cond
              ((eq (forbidden-semantic-symbol? (car section)) (quote yes))
               (identity-relation same)
               (quote yes))
              (t (contains-forbidden-semantic-section? (cdr sections)))))
           (t (contains-forbidden-semantic-section? (cdr sections)))))))))

(def validate-rows
  (lambda (rows)
    (cond
      ((atom rows) (structural-kind empty-list)
       (quote (island-math-evidence-ok)))
      ((atom rows) (structural-kind pair)
       (let* ((row (car rows))
              (sid (car row))
              (executor (second row))
              (status (third row))
              (provenance (fourth row)))
         (cond
           ((equal? (length row) 4)
            (structural-relation distinct)
            (list (quote island-math-evidence-violation)
                  (quote invalid-evidence-row-shape) sid))
           ((string? provenance)
            (identity-relation distinct)
            (list (quote island-math-evidence-violation)
                  (quote provenance-must-be-string) sid executor))
           ((eq (registry-has-sid? sid registry-rows) (quote no))
            (identity-relation same)
            (list (quote island-math-evidence-violation)
                  (quote sid-not-in-canon-function-table) sid))
           ((eq (admitted-executor? executor) (quote no))
            (identity-relation same)
            (list (quote island-math-evidence-violation)
                  (quote unsupported-executor) sid executor))
           ((eq (mechanism-has-route? sid executor mechanism-rows) (quote no))
            (identity-relation same)
            (list (quote island-math-evidence-violation)
                  (quote executor-route-not-admitted-by-canon-projection) sid executor))
           ((eq (admitted-status? status) (quote no))
            (identity-relation same)
            (list (quote island-math-evidence-violation)
                  (quote unsupported-status) sid status))
           ((eq (evidence-has-route? sid executor (cdr rows)) (quote yes))
            (identity-relation same)
            (list (quote island-math-evidence-violation)
                  (quote duplicate-executor-evidence) sid executor))
           (t (validate-rows (cdr rows)))))))))

(def same-sid?
  (lambda (sid rows)
    (cond
      ((atom rows) (structural-kind empty-list) (quote yes))
      ((atom rows) (structural-kind pair)
       (cond
         ((equal? sid (car (car rows))) (structural-relation same)
          (same-sid? sid (cdr rows)))
         ((equal? sid (car (car rows))) (structural-relation distinct)
          (quote no)))))))

(def four-island-slice?
  (lambda (sid)
    (cond
      ((eq (evidence-has-route? sid (quote common-lisp) evidence-rows) (quote no))
       (identity-relation same) (quote no))
      ((eq (evidence-has-route? sid (quote prolog) evidence-rows) (quote no))
       (identity-relation same) (quote no))
      ((eq (evidence-has-route? sid (quote clips) evidence-rows) (quote no))
       (identity-relation same) (quote no))
      ((eq (evidence-has-route? sid (quote datalog) evidence-rows) (quote no))
       (identity-relation same) (quote no))
      (t (quote yes)))))

(def row-verdict (validate-rows evidence-rows))

(def verdict
  (cond
    ((eq (contains-forbidden-semantic-section? evidence) (quote yes))
     (identity-relation same)
     (quote (island-math-evidence-violation semantic-field-forbidden)))
    ((atom evidence-rows) (structural-kind empty-list)
     (quote (island-math-evidence-violation empty-evidence)))
    ((equal? row-verdict (quote (island-math-evidence-ok)))
     (structural-relation same)
     (let ((target-sid (car (car evidence-rows))))
       (cond
         ((eq (same-sid? target-sid evidence-rows) (quote no))
          (identity-relation same)
          (quote (island-math-evidence-violation first-slice-must-have-one-sid)))
         ((eq (four-island-slice? target-sid) (quote no))
          (identity-relation same)
          (quote (island-math-evidence-violation missing-required-four-island-slice)))
         (t (quote (island-math-evidence-ok))))))
    (t row-verdict)))

(print verdict)
