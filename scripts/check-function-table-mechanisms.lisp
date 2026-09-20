; #1046 — fail-closed validation for transitional mechanism metadata.
; Semantic identity authority is ONLY lib/surface/semantic-registry.lisp.
; This checker proves mechanism metadata cannot invent a SID beside that table.

(def registry
  (car (read-all (read-file "lib/surface/semantic-registry.lisp"))))

(def metadata
  (car (read-all (read-file "lib/function-table-mechanisms.lisp"))))

(def registry-rows (cdr registry))

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

(def metadata-rows
  (cdr (find-section (quote rows) metadata)))

(def registry-has-sid?
  (lambda (sid rows)
    (cond
      ((atom rows) (structural-kind empty-list) (quote no))
      ((atom rows) (structural-kind pair)
       (cond
         ((equal? sid (car (car rows))) (structural-relation same) (quote yes))
         ((equal? sid (car (car rows))) (structural-relation distinct)
          (registry-has-sid? sid (cdr rows))))))))

(def metadata-has-route?
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
               (metadata-has-route? sid executor (cdr rows)))))
           ((equal? sid (car row)) (structural-relation distinct)
            (metadata-has-route? sid executor (cdr rows)))))))))

(def admitted-executor?
  (lambda (executor)
    (cond
      ((eq executor (quote evaluator)) (identity-relation same) (quote yes))
      ((eq executor (quote common-lisp)) (identity-relation same) (quote yes))
      ((eq executor (quote prolog)) (identity-relation same) (quote yes))
      ((eq executor (quote clips)) (identity-relation same) (quote yes))
      ((eq executor (quote datalog)) (identity-relation same) (quote yes))
      (t (quote no)))))

(def admitted-mechanism?
  (lambda (mechanism)
    (cond
      ((eq mechanism (quote empty-list-ground)) (identity-relation same) (quote yes))
      ((eq mechanism (quote quote-form)) (identity-relation same) (quote yes))
      ((eq mechanism (quote atom-primitive)) (identity-relation same) (quote yes))
      ((eq mechanism (quote eq-primitive)) (identity-relation same) (quote yes))
      ((eq mechanism (quote cons-primitive)) (identity-relation same) (quote yes))
      ((eq mechanism (quote car-primitive)) (identity-relation same) (quote yes))
      ((eq mechanism (quote cdr-primitive)) (identity-relation same) (quote yes))
      ((eq mechanism (quote cond-form)) (identity-relation same) (quote yes))
      ((eq mechanism (quote lambda-form)) (identity-relation same) (quote yes))
      ((eq mechanism (quote define-form)) (identity-relation same) (quote yes))
      ((eq mechanism (quote bounded-exact-add)) (identity-relation same) (quote yes))
      (t (quote no)))))

(def validate-rows
  (lambda (rows)
    (cond
      ((atom rows) (structural-kind empty-list)
       (quote (function-table-mechanisms-ok)))
      ((atom rows) (structural-kind pair)
       (let* ((row (car rows))
              (sid (car row))
              (executor (second row))
              (mechanism (third row)))
         (cond
           ((eq (admitted-executor? executor) (quote no))
            (identity-relation same)
            (list (quote function-table-mechanisms-violation)
                  (quote unsupported-executor) sid executor))
           ((eq (registry-has-sid? sid registry-rows) (quote no))
            (identity-relation same)
            (list (quote function-table-mechanisms-violation)
                  (quote sid-not-in-canon-function-table) sid))
           ((eq (metadata-has-route? sid executor (cdr rows)) (quote yes))
            (identity-relation same)
            (list (quote function-table-mechanisms-violation)
                  (quote duplicate-executor-route) sid executor))
           ((eq (admitted-mechanism? mechanism) (quote no))
            (identity-relation same)
            (list (quote function-table-mechanisms-violation)
                  (quote unsupported-mechanism) sid mechanism))
           (t (validate-rows (cdr rows)))))))))

(def verdict (validate-rows metadata-rows))
(print verdict)

(cond
  ((equal? verdict (quote (function-table-mechanisms-ok)))
   (structural-relation same)
   verdict)
  (t
   (car (quote ()))))
