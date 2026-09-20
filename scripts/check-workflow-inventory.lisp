; #384 — GitHub Actions workflow inventory checker.
; Governance metadata only. This checker does not define workflow behavior or language semantics.

(def workflow-inventory-violation
  (lambda (kind detail)
    (list (quote workflow-inventory-violation) kind detail)))

(def workflow-field-from
  (lambda (name fields)
    (cond
      ((atom fields) (structural-kind empty-list) (quote missing))
      ((atom fields) (structural-kind atom) (quote missing))
      ((atom fields) (structural-kind pair)
       (let ((field (car fields)))
         (cond
           ((atom field) (structural-kind empty-list)
            (workflow-field-from name (cdr fields)))
           ((atom field) (structural-kind atom)
            (workflow-field-from name (cdr fields)))
           ((atom field) (structural-kind pair)
            (cond
              ((eq (car field) name) (identity-relation same) (second field))
              ((eq (car field) name) (identity-relation distinct)
               (workflow-field-from name (cdr fields)))))))))))

(def workflow-field
  (lambda (name row)
    (workflow-field-from name (cdr row))))

(def workflow-rows
  (lambda (forms)
    (cond
      ((atom forms) (structural-kind empty-list) (quote ()))
      ((atom forms) (structural-kind atom) (quote ()))
      ((atom forms) (structural-kind pair)
       (let ((form (car forms)))
         (cond
           ((atom form) (structural-kind empty-list)
            (workflow-rows (cdr forms)))
           ((atom form) (structural-kind atom)
            (workflow-rows (cdr forms)))
           ((atom form) (structural-kind pair)
            (cond
              ((eq (car form) (quote workflow-inventory)) (identity-relation same)
               (cdr form))
              ((eq (car form) (quote workflow-inventory)) (identity-relation distinct)
               (workflow-rows (cdr forms)))))))))))

(def workflow-find-by-path
  (lambda (path rows)
    (cond
      ((atom rows) (structural-kind empty-list) (quote ()))
      ((atom rows) (structural-kind atom) (quote ()))
      ((atom rows) (structural-kind pair)
       (let ((row (car rows)))
         (cond
           ((equal? path (workflow-field (quote path) row))
            (structural-relation same)
            row)
           ((equal? path (workflow-field (quote path) row))
            (structural-relation distinct)
            (workflow-find-by-path path (cdr rows)))))))))

(def workflow-count-path
  (lambda (path rows)
    (cond
      ((atom rows) (structural-kind empty-list) 0)
      ((atom rows) (structural-kind atom) 0)
      ((atom rows) (structural-kind pair)
       (let ((row (car rows)))
         (cond
           ((equal? path (workflow-field (quote path) row))
            (structural-relation same)
            (+ 1 (workflow-count-path path (cdr rows))))
           ((equal? path (workflow-field (quote path) row))
            (structural-relation distinct)
            (workflow-count-path path (cdr rows)))))))))

(def workflow-paths-from-dir
  (lambda (names)
    (cond
      ((atom names) (structural-kind empty-list) (quote ()))
      ((atom names) (structural-kind atom) (quote ()))
      ((atom names) (structural-kind pair)
       (cons
         (string-append ".github/workflows/" (car names))
         (workflow-paths-from-dir (cdr names)))))))

(def workflow-observed-verdict
  (lambda (observed rows)
    (cond
      ((atom observed) (structural-kind empty-list) (quote (workflow-inventory-ok)))
      ((atom observed) (structural-kind atom)
       (workflow-inventory-violation (quote malformed-observed-workflows) observed))
      ((atom observed) (structural-kind pair)
       (let* ((path (car observed))
              (count (workflow-count-path path rows)))
         (cond
           ((= count 1) 1
            (workflow-observed-verdict (cdr observed) rows))
           ((= count 0) 1
            (workflow-inventory-violation (quote unregistered-workflow) path))
           ((> count 1) 1
            (workflow-inventory-violation (quote duplicate-workflow-row) path))))))))

(def workflow-observed-path-state
  (lambda (path observed)
    (cond
      ((atom observed) (structural-kind empty-list) (quote absent))
      ((atom observed) (structural-kind atom) (quote malformed))
      ((atom observed) (structural-kind pair)
       (cond
         ((equal? path (car observed)) (structural-relation same) (quote present))
         ((equal? path (car observed)) (structural-relation distinct)
          (workflow-observed-path-state path (cdr observed))))))))

(def workflow-stale-verdict
  (lambda (rows observed)
    (cond
      ((atom rows) (structural-kind empty-list) (quote (workflow-inventory-ok)))
      ((atom rows) (structural-kind atom)
       (workflow-inventory-violation (quote malformed-workflow-rows) rows))
      ((atom rows) (structural-kind pair)
       (let* ((row (car rows))
              (path (workflow-field (quote path) row))
              (state (workflow-observed-path-state path observed)))
         (cond
           ((eq state (quote present)) (identity-relation same)
            (workflow-stale-verdict (cdr rows) observed))
           ((eq state (quote absent)) (identity-relation same)
            (workflow-inventory-violation (quote stale-workflow-row) path))
           ((eq state (quote malformed)) (identity-relation same)
            (workflow-inventory-violation (quote malformed-observed-workflows) observed))))))))

(def workflow-verdict
  (lambda (observed rows)
    (let ((coverage (workflow-observed-verdict observed rows)))
      (cond
        ((equal? coverage (quote (workflow-inventory-ok))) (structural-relation same)
         (workflow-stale-verdict rows observed))
        ((equal? coverage (quote (workflow-inventory-ok))) (structural-relation distinct)
         coverage)))))

(def workflow-assert
  (lambda (actual expected)
    (cond
      ((equal? actual expected) (structural-relation same)
       (quote (workflow-inventory-selftest-ok)))
      ((equal? actual expected) (structural-relation distinct)
       (let ((shown (print (list (quote workflow-inventory-selftest-failed) actual expected))))
         (car (quote ())))))))

; Pure negative witnesses.
(def workflow-sample-row
  (quote
    (workflow
      (path ".github/workflows/a.yml")
      (purpose "sample")
      (triggers (pull-request))
      (lane fast-pr)
      (semantic-or-mechanism mechanism-build)
      (direct-commands ())
      (repo-tools ())
      (upstream-authority ())
      (expected-cost low)
      (cancellation unspecified)
      (lifecycle active)
      (removal-condition explicit-review))))

(workflow-assert
  (workflow-verdict
    (quote (".github/workflows/a.yml" ".github/workflows/b.yml"))
    (list workflow-sample-row))
  (quote (workflow-inventory-violation unregistered-workflow ".github/workflows/b.yml")))

(workflow-assert
  (workflow-verdict
    (quote (".github/workflows/a.yml"))
    (list workflow-sample-row workflow-sample-row))
  (quote (workflow-inventory-violation duplicate-workflow-row ".github/workflows/a.yml")))

(workflow-assert
  (workflow-verdict
    (quote ())
    (list workflow-sample-row))
  (quote (workflow-inventory-violation stale-workflow-row ".github/workflows/a.yml")))

; Real repository observation.
(def workflow-live-forms
  (read-all (read-file "knowledge/workflow-inventory.lisp")))

(def workflow-live-rows
  (workflow-rows workflow-live-forms))

(def workflow-live-observed
  (workflow-paths-from-dir (read-dir ".github/workflows")))

(def workflow-live-verdict
  (workflow-verdict workflow-live-observed workflow-live-rows))

(print workflow-live-verdict)

(workflow-assert workflow-live-verdict (quote (workflow-inventory-ok)))
