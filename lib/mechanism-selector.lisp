; #1047 — mechanism selection after Canon()/function-table identity resolution.
; Exact parent: #1046 function-table mechanism authority.
; This file never decides what a SID means. It only selects among executor
; routes already admitted by transitional #1046 mechanism metadata.

(def mechanism-selector-registry
  (car (read-all (read-file "lib/surface/semantic-registry.lisp"))))

(def mechanism-selector-metadata
  (car (read-all (read-file "lib/function-table-mechanisms.lisp"))))

(def mechanism-selector-registry-rows
  mechanism-selector-registry)

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

(def mechanism-selector-profile-routes
  (cdr (mechanism-selector-find-section
         (quote profile-rows)
         mechanism-selector-metadata)))

(def mechanism-selector-registry-has-sid?
  (lambda (sid rows)
    (cond
      ((atom rows) (structural-kind empty-list) (quote no))
      ((atom rows) (structural-kind pair)
       (cond
         ((eq sid (car (car rows))) (identity-relation same) (quote yes))
         ((eq sid (car (car rows))) (identity-relation distinct)
          (mechanism-selector-registry-has-sid? sid (cdr rows))))))))

(def mechanism-selector-find-route
  (lambda (sid executor rows)
    (cond
      ((atom rows) (structural-kind empty-list) (quote ()))
      ((atom rows) (structural-kind pair)
       (let ((row (car rows)))
         (cond
           ((eq sid (car row)) (identity-relation same)
            (cond
              ((eq executor (second row)) (identity-relation same) row)
              ((eq executor (second row)) (identity-relation distinct)
               (mechanism-selector-find-route sid executor (cdr rows)))))
           ((eq sid (car row)) (identity-relation distinct)
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


; #1422 — selected-Core-aware admission. This consumes only profile-scoped
; SENS-owned mechanism metadata; host availability is intentionally absent here.
(def mechanism-selector-find-profile-route
  (lambda (profile function rows)
    (cond
      ((atom rows) (structural-kind empty-list) (quote ()))
      ((atom rows) (structural-kind pair)
       (let ((row (car rows)))
         (cond
           ((eq profile (car row)) (identity-relation same)
            (cond
              ((eq function (second row)) (identity-relation same) row)
              ((eq function (second row)) (identity-relation distinct)
               (mechanism-selector-find-profile-route
                 profile function (cdr rows)))))
           ((eq profile (car row)) (identity-relation distinct)
            (mechanism-selector-find-profile-route
              profile function (cdr rows)))))))))

(def mechanism-select-for-core
  (lambda (profile function)
    (cond
      ((eq
         (mechanism-selector-registry-has-sid?
           function mechanism-selector-registry-rows)
         (quote no))
       (identity-relation same)
       (list
         (quote profile-mechanism-selection-failure)
         (quote function-not-in-function-table)
         profile function))
      (t
       (let ((route
               (mechanism-selector-find-profile-route
                 profile function mechanism-selector-profile-routes)))
         (cond
           ((atom route) (structural-kind empty-list)
            (list
              (quote profile-mechanism-unavailable)
              profile function))
           ((atom route) (structural-kind pair)
            (list
              (quote profile-mechanism-selected)
              profile
              function
              (third route)))))))))
