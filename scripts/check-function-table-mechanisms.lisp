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
      ((atom? sections) () (quote ()))
      ((atom? sections) (0)
       (cond
         ((eq? (car (car sections)) name) (1)
          (car sections))
         ((eq? (car (car sections)) name) (0)
          (find-section name (cdr sections))))))))

(def metadata-rows
  (cdr (find-section (quote rows) metadata)))

(def registry-has-sid?
  (lambda (sid rows)
    (cond
      ((atom? rows) () (quote no))
      ((atom? rows) (0)
       (cond
         ((eq? sid (car (car rows))) (1) (quote yes))
         ((eq? sid (car (car rows))) (0)
          (registry-has-sid? sid (cdr rows))))))))

(def metadata-has-route?
  (lambda (sid executor rows)
    (cond
      ((atom? rows) () (quote no))
      ((atom? rows) (0)
       (let ((row (car rows)))
         (cond
           ((eq? sid (car row)) (1)
            (cond
              ((eq? executor (second row)) (1) (quote yes))
              ((eq? executor (second row)) (0)
               (metadata-has-route? sid executor (cdr rows)))))
           ((eq? sid (car row)) (0)
            (metadata-has-route? sid executor (cdr rows)))))))))

(def admitted-executor?
  (lambda (executor)
    (cond
      ((eq? executor (quote evaluator)) (1) (quote yes))
      ((eq? executor (quote common-lisp)) (1) (quote yes))
      ((eq? executor (quote prolog)) (1) (quote yes))
      ((eq? executor (quote clips)) (1) (quote yes))
      ((eq? executor (quote datalog)) (1) (quote yes))
      (t (quote no)))))

(def admitted-mechanism?
  (lambda (mechanism)
    (cond
      ((eq? mechanism (quote quote-form)) (1) (quote yes))
      ((eq? mechanism (quote atom-primitive)) (1) (quote yes))
      ((eq? mechanism (quote eq-primitive)) (1) (quote yes))
      ((eq? mechanism (quote cons-primitive)) (1) (quote yes))
      ((eq? mechanism (quote car-primitive)) (1) (quote yes))
      ((eq? mechanism (quote cdr-primitive)) (1) (quote yes))
      ((eq? mechanism (quote cond-form)) (1) (quote yes))
      ((eq? mechanism (quote lambda-form)) (1) (quote yes))
      ((eq? mechanism (quote define-form)) (1) (quote yes))
      ((eq? mechanism (quote bounded-exact-add)) (1) (quote yes))
      (t (quote no)))))

(def validate-rows
  (lambda (rows)
    (cond
      ((atom? rows) ()
       (quote (function-table-mechanisms-ok)))
      ((atom? rows) (0)
       (let* ((row (car rows))
              (sid (car row))
              (executor (second row))
              (mechanism (third row)))
         (cond
           ((eq? (admitted-executor? executor) (quote no))
            (1)
            (list (quote function-table-mechanisms-violation)
                  (quote unsupported-executor) sid executor))
           ((eq? (registry-has-sid? sid registry-rows) (quote no))
            (1)
            (list (quote function-table-mechanisms-violation)
                  (quote sid-not-in-canon-function-table) sid))
           ((eq? (metadata-has-route? sid executor (cdr rows)) (quote yes))
            (1)
            (list (quote function-table-mechanisms-violation)
                  (quote duplicate-executor-route) sid executor))
           ((eq? (admitted-mechanism? mechanism) (quote no))
            (1)
            (list (quote function-table-mechanisms-violation)
                  (quote unsupported-mechanism) sid mechanism))
           (t (validate-rows (cdr rows)))))))))

(def verdict (validate-rows metadata-rows))
(print verdict)
