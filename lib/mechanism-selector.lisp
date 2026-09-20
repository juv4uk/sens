; #1047 — mechanism selection after Canon()/function-table identity resolution.
; Exact parent: #1046 function-table mechanism authority.
; This file never decides what a SID means. It only selects among executor
; routes already admitted by transitional #1046 mechanism metadata.

(def mechanism-selector-registry
  (car (read-all (read-file "lib/surface/semantic-registry.lisp"))))

(def mechanism-selector-metadata
  (car (read-all (read-file "lib/function-table-mechanisms.lisp"))))

(def mechanism-selector-registry-rows
  (cdr mechanism-selector-registry))

(def mechanism-selector-find-section
  (lambda (name sections)
    (cond
      ((atom sections) (structural-kind empty-list) (quote ()))
      ((atom sections) (structural-kind pair)
       (cond
         ((eq (car (car sections)) name) (identity-relation same)
          (car sections))
         ((eq (car (car sections)) name) (identity-relation distinct)
          (mechanism-selector-find-section name (cdr sections))))))))

(def mechanism-selector-routes
  (cdr (mechanism-selector-find-section
         (quote rows)
         mechanism-selector-metadata)))

(def mechanism-selector-registry-has-sid?
  (lambda (sid rows)
    (cond
      ((atom rows) (structural-kind empty-list) (quote no))
      ((atom rows) (structural-kind pair)
       (cond
         ((equal? sid (car (car rows))) (structural-relation same) (quote yes))
         ((equal? sid (car (car rows))) (structural-relation distinct)
          (mechanism-selector-registry-has-sid? sid (cdr rows))))))))

(def mechanism-selector-find-route
  (lambda (sid executor rows)
    (cond
      ((atom rows) (structural-kind empty-list) (quote ()))
      ((atom rows) (structural-kind pair)
       (let ((row (car rows)))
         (cond
           ((equal? sid (car row)) (structural-relation same)
            (cond
              ((eq executor (second row)) (identity-relation same) row)
              ((eq executor (second row)) (identity-relation distinct)
               (mechanism-selector-find-route sid executor (cdr rows)))))
           ((equal? sid (car row)) (structural-relation distinct)
            (mechanism-selector-find-route sid executor (cdr rows)))))))))

(def mechanism-select
  (lambda (sid executor)
    (cond
      ((eq
         (mechanism-selector-registry-has-sid?
           sid mechanism-selector-registry-rows)
         (quote no))
       (identity-relation same)
       (list
         (quote mechanism-selection-failure)
         (quote sid-not-in-function-table)
         sid))
      (t
       (let ((route
               (mechanism-selector-find-route
                 sid executor mechanism-selector-routes)))
         (cond
           ((atom route) (structural-kind empty-list)
            (list (quote mechanism-unavailable) sid executor))
           ((atom route) (structural-kind pair)
            (list
              (quote mechanism-selected)
              sid
              executor
              (third route)))))))))
