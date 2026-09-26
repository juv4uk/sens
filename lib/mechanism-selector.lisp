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
      ((atom? sections) () (quote ()))
      ((atom? sections) (0)
       (cond
         ((eq? (car (car sections)) name) (1)
          (car sections))
         ((eq? (car (car sections)) name) (0)
          (mechanism-selector-find-section name (cdr sections))))))))

(def mechanism-selector-routes
  (cdr (mechanism-selector-find-section
         (quote rows)
         mechanism-selector-metadata)))

(def mechanism-selector-registry-has-sid?
  (lambda (sid rows)
    (cond
      ((atom? rows) () (quote no))
      ((atom? rows) (0)
       (cond
         ((eq? sid (car (car rows))) (1) (quote yes))
         ((eq? sid (car (car rows))) (0)
          (mechanism-selector-registry-has-sid? sid (cdr rows))))))))

(def mechanism-selector-find-route
  (lambda (sid executor rows)
    (cond
      ((atom? rows) () (quote ()))
      ((atom? rows) (0)
       (let ((row (car rows)))
         (cond
           ((eq? sid (car row)) (1)
            (cond
              ((eq? executor (second row)) (1) row)
              ((eq? executor (second row)) (0)
               (mechanism-selector-find-route sid executor (cdr rows)))))
           ((eq? sid (car row)) (0)
            (mechanism-selector-find-route sid executor (cdr rows)))))))))

(def mechanism-select
  (lambda (sid executor)
    (cond
      ((eq?
         (mechanism-selector-registry-has-sid?
           sid mechanism-selector-registry-rows)
         (quote no))
       (1)
       (list
         (quote mechanism-selection-failure)
         (quote sid-not-in-function-table)
         sid))
      (t
       (let ((route
               (mechanism-selector-find-route
                 sid executor mechanism-selector-routes)))
         (cond
           ((atom? route) ()
            (list (quote mechanism-unavailable) sid executor))
           ((atom? route) (0)
            (list
              (quote mechanism-selected)
              sid
              executor
              (third route)))))))))
