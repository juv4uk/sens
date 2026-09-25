; #1046 — fail-closed validation for transitional mechanism metadata.
; Semantic identity authority is ONLY lib/surface/semantic-registry.lisp.
; This checker proves mechanism metadata cannot invent a function beside that table.
; #1332/#1403: empty-list-ground is not a function mechanism.

(def registry
  (car (read-all (read-file "lib/surface/semantic-registry.lisp"))))

(def metadata
  (car (read-all (read-file "lib/function-table-mechanisms.lisp"))))

(def registry-rows registry)

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

(def profile-metadata-rows
  (cdr (find-section (quote profile-rows) metadata)))

(def registry-has-sid?
  (lambda (sid rows)
    (cond
      ((atom rows) (structural-kind empty-list) (quote no))
      ((atom rows) (structural-kind pair)
       (cond
         ((eq sid (car (car rows))) (identity-relation same) (quote yes))
         ((eq sid (car (car rows))) (identity-relation distinct)
          (registry-has-sid? sid (cdr rows))))))))

(def metadata-has-route?
  (lambda (sid executor rows)
    (cond
      ((atom rows) (structural-kind empty-list) (quote no))
      ((atom rows) (structural-kind pair)
       (let ((row (car rows)))
         (cond
           ((eq sid (car row)) (identity-relation same)
            (cond
              ((eq executor (second row)) (identity-relation same) (quote yes))
              ((eq executor (second row)) (identity-relation distinct)
               (metadata-has-route? sid executor (cdr rows)))))
           ((eq sid (car row)) (identity-relation distinct)
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

(def admitted-profile?
  (lambda (profile)
    (cond
      ((eq profile (quote core1)) (identity-relation same) (quote yes))
      ((eq profile (quote core2)) (identity-relation same) (quote yes))
      ((eq profile (quote core3)) (identity-relation same) (quote yes))
      ((eq profile (quote core4)) (identity-relation same) (quote yes))
      (t (quote no)))))

(def admitted-profile-mechanism?
  (lambda (mechanism)
    (cond
      ((eq mechanism (quote registered-host-mechanism))
       (identity-relation same)
       (quote yes))
      (t (quote no)))))

(def profile-metadata-has-route?
  (lambda (profile function rows)
    (cond
      ((atom rows) (structural-kind empty-list) (quote no))
      ((atom rows) (structural-kind pair)
       (let ((row (car rows)))
         (cond
           ((eq profile (car row)) (identity-relation same)
            (cond
              ((eq function (second row)) (identity-relation same) (quote yes))
              ((eq function (second row)) (identity-relation distinct)
               (profile-metadata-has-route? profile function (cdr rows)))))
           ((eq profile (car row)) (identity-relation distinct)
            (profile-metadata-has-route? profile function (cdr rows)))))))))

(def validate-profile-rows
  (lambda (rows)
    (cond
      ((atom rows) (structural-kind empty-list)
       (quote (function-table-profile-mechanisms-ok)))
      ((atom rows) (structural-kind pair)
       (let* ((row (car rows))
              (profile (car row))
              (function (second row))
              (mechanism (third row)))
         (cond
           ((eq (admitted-profile? profile) (quote no))
            (identity-relation same)
            (list (quote function-table-mechanisms-violation)
                  (quote unsupported-profile) profile))
           ((eq (registry-has-sid? function registry-rows) (quote no))
            (identity-relation same)
            (list (quote function-table-mechanisms-violation)
                  (quote function-not-in-function-table) function))
           ((eq
              (profile-metadata-has-route? profile function (cdr rows))
              (quote yes))
            (identity-relation same)
            (list (quote function-table-mechanisms-violation)
                  (quote duplicate-profile-function-route) profile function))
           ((eq (admitted-profile-mechanism? mechanism) (quote no))
            (identity-relation same)
            (list (quote function-table-mechanisms-violation)
                  (quote unsupported-profile-mechanism)
                  profile function mechanism))
           (t (validate-profile-rows (cdr rows)))))))))

(def legacy-verdict (validate-rows metadata-rows))
(def profile-verdict (validate-profile-rows profile-metadata-rows))

(def verdict
  (cond
    ((eq (car legacy-verdict) (quote function-table-mechanisms-ok))
     (identity-relation same)
     (cond
       ((eq
          (car profile-verdict)
          (quote function-table-profile-mechanisms-ok))
        (identity-relation same)
        (quote (function-table-mechanisms-ok)))
       ((quote profile-validation-failed)
        profile-validation-failed
        profile-verdict)))
    ((quote legacy-validation-failed)
     legacy-validation-failed
     legacy-verdict)))

(print verdict)
