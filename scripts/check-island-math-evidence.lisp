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

(def registry-rows registry)

(def evidence-sid-text
  (lambda (sid)
    (cond
      ((string? sid) sid)
      (t (write-to-string sid)))))

(def find-section
  (lambda (name sections)
    (cond
      ((atom? sections) () (quote ()))
      ((atom? sections) (0)
       (cond
         ((eq? (car (car sections)) name) (1)
          (car sections))
         ((eq? (car (car sections)) name) (0)
          (find-section name (cdr sections))))))))

(def mechanism-rows
  (cdr (find-section (quote rows) mechanisms)))

(def evidence-rows
  (cdr (find-section (quote rows) evidence)))

(def registry-has-sid?
  (lambda (sid rows)
    (cond
      ((atom? rows) () (quote no))
      ((atom? rows) (0)
       (cond
         ((equal? sid (car (car rows))) (1) (quote yes))
         ((equal? sid (car (car rows))) (0)
          (registry-has-sid? sid (cdr rows))))))))

(def mechanism-has-route?
  (lambda (sid executor rows)
    (cond
      ((atom? rows) () (quote no))
      ((atom? rows) (0)
       (let ((row (car rows)))
         (cond
           ((equal? (evidence-sid-text sid) (evidence-sid-text (car row))) (1)
            (cond
              ((eq? executor (second row)) (1) (quote yes))
              ((eq? executor (second row)) (0)
               (mechanism-has-route? sid executor (cdr rows)))))
           ((equal? (evidence-sid-text sid) (evidence-sid-text (car row))) (0)
            (mechanism-has-route? sid executor (cdr rows)))))))))

(def evidence-has-route?
  (lambda (sid executor rows)
    (cond
      ((atom? rows) () (quote no))
      ((atom? rows) (0)
       (let ((row (car rows)))
         (cond
           ((equal? sid (car row)) (1)
            (cond
              ((eq? executor (second row)) (1) (quote yes))
              ((eq? executor (second row)) (0)
               (evidence-has-route? sid executor (cdr rows)))))
           ((equal? sid (car row)) (0)
            (evidence-has-route? sid executor (cdr rows)))))))))

(def admitted-executor?
  (lambda (executor)
    (cond
      ((eq? executor (quote common-lisp)) (1) (quote yes))
      ((eq? executor (quote prolog)) (1) (quote yes))
      ((eq? executor (quote clips)) (1) (quote yes))
      ((eq? executor (quote datalog)) (1) (quote yes))
      (t (quote no)))))

(def admitted-status?
  (lambda (status)
    (cond
      ((eq? status (quote execution-witness)) (1) (quote yes))
      (t (quote no)))))

(def forbidden-semantic-symbol?
  (lambda (value)
    (cond
      ((atom? value) () (quote no))
      ((atom? value) (0) (quote no))
      ((atom? value) (1)
       (cond
         ((eq? value (quote operation)) (1) (quote yes))
         ((eq? value (quote meaning)) (1) (quote yes))
         ((eq? value (quote law)) (1) (quote yes))
         ((eq? value (quote domain)) (1) (quote yes))
         ((eq? value (quote operand-domain)) (1) (quote yes))
         ((eq? value (quote result-domain)) (1) (quote yes))
         (t (quote no)))))))

(def contains-forbidden-semantic-section?
  (lambda (sections)
    (cond
      ((atom? sections) () (quote no))
      ((atom? sections) (0)
       (let ((section (car sections)))
         (cond
           ((atom? section) (0)
            (cond
              ((eq? (forbidden-semantic-symbol? (car section)) (quote yes))
               (1)
               (quote yes))
              (t (contains-forbidden-semantic-section? (cdr sections)))))
           (t (contains-forbidden-semantic-section? (cdr sections)))))))))

(def validate-rows
  (lambda (rows)
    (cond
      ((atom? rows) ()
       (quote (island-math-evidence-ok)))
      ((atom? rows) (0)
       (let* ((row (car rows))
              (sid (car row))
              (executor (second row))
              (status (third row))
              (provenance (fourth row)))
         (cond
           ((equal? (length row) 4)
            (0)
            (list (quote island-math-evidence-violation)
                  (quote invalid-evidence-row-shape) sid))
           ((string? provenance)
            (0)
            (list (quote island-math-evidence-violation)
                  (quote provenance-must-be-string) sid executor))
           ((eq? (registry-has-sid? sid registry-rows) (quote no))
            (1)
            (list (quote island-math-evidence-violation)
                  (quote sid-not-in-canon-function-table) sid))
           ((eq? (admitted-executor? executor) (quote no))
            (1)
            (list (quote island-math-evidence-violation)
                  (quote unsupported-executor) sid executor))
           ((eq? (mechanism-has-route? sid executor mechanism-rows) (quote no))
            (1)
            (list (quote island-math-evidence-violation)
                  (quote executor-route-not-admitted-by-canon-projection) sid executor))
           ((eq? (admitted-status? status) (quote no))
            (1)
            (list (quote island-math-evidence-violation)
                  (quote unsupported-status) sid status))
           ((eq? (evidence-has-route? sid executor (cdr rows)) (quote yes))
            (1)
            (list (quote island-math-evidence-violation)
                  (quote duplicate-executor-evidence) sid executor))
           (t (validate-rows (cdr rows)))))))))

(def same-sid?
  (lambda (sid rows)
    (cond
      ((atom? rows) () (quote yes))
      ((atom? rows) (0)
       (cond
         ((equal? sid (car (car rows))) (1)
          (same-sid? sid (cdr rows)))
         ((equal? sid (car (car rows))) (0)
          (quote no)))))))

(def four-island-slice?
  (lambda (sid)
    (cond
      ((eq? (evidence-has-route? sid (quote common-lisp) evidence-rows) (quote no))
       (1) (quote no))
      ((eq? (evidence-has-route? sid (quote prolog) evidence-rows) (quote no))
       (1) (quote no))
      ((eq? (evidence-has-route? sid (quote clips) evidence-rows) (quote no))
       (1) (quote no))
      ((eq? (evidence-has-route? sid (quote datalog) evidence-rows) (quote no))
       (1) (quote no))
      (t (quote yes)))))

(def row-verdict (validate-rows evidence-rows))

(def verdict
  (cond
    ((eq? (contains-forbidden-semantic-section? evidence) (quote yes))
     (1)
     (quote (island-math-evidence-violation semantic-field-forbidden)))
    ((atom? evidence-rows) ()
     (quote (island-math-evidence-violation empty-evidence)))
    ((equal? row-verdict (quote (island-math-evidence-ok)))
     (1)
     (let ((target-sid (car (car evidence-rows))))
       (cond
         ((eq? (same-sid? target-sid evidence-rows) (quote no))
          (1)
          (quote (island-math-evidence-violation first-slice-must-have-one-sid)))
         ((eq? (four-island-slice? target-sid) (quote no))
          (1)
          (quote (island-math-evidence-violation missing-required-four-island-slice)))
         (t (quote (island-math-evidence-ok))))))
    (t row-verdict)))

(print verdict)
