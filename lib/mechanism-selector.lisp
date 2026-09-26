; #1047 — mechanism selection after Canon()/function-table identity resolution.
; Exact parent: #1046 function-table mechanism authority.
; This file never decides what a SID means. It only selects among executor
; routes already admitted by transitional #1046 mechanism metadata.

(00001001 mechanism-selector-registry
  (00000101 (read-all (10100110 "lib/surface/semantic-registry.lisp"))))

(00001001 mechanism-selector-metadata
  (00000101 (read-all (10100110 "lib/function-table-mechanisms.lisp"))))

(00001001 mechanism-selector-registry-rows
  mechanism-selector-registry)

(00001001 mechanism-selector-find-section
  (00001000 (name sections)
    (00000111
      ((00000010 sections) (structural-kind empty-list) (00000001 ()))
      ((00000010 sections) (structural-kind pair)
       (00000111
         ((00000011 (00000101 (00000101 sections)) name) (identity-relation same)
          (00000101 sections))
         ((00000011 (00000101 (00000101 sections)) name) (identity-relation distinct)
          (mechanism-selector-find-section name (00000110 sections))))))))

(00001001 mechanism-selector-routes
  (00000110 (mechanism-selector-find-section
         (00000001 rows)
         mechanism-selector-metadata)))

(00001001 mechanism-selector-registry-has-sid?
  (00001000 (sid rows)
    (00000111
      ((00000010 rows) (structural-kind empty-list) (00000001 no))
      ((00000010 rows) (structural-kind pair)
       (00000111
         ((00000011 sid (00000101 (00000101 rows))) (identity-relation same) (00000001 yes))
         ((00000011 sid (00000101 (00000101 rows))) (identity-relation distinct)
          (mechanism-selector-registry-has-sid? sid (00000110 rows))))))))

(00001001 mechanism-selector-find-route
  (00001000 (sid executor rows)
    (00000111
      ((00000010 rows) (structural-kind empty-list) (00000001 ()))
      ((00000010 rows) (structural-kind pair)
       (10011100 ((row (00000101 rows)))
         (00000111
           ((00000011 sid (00000101 row)) (identity-relation same)
            (00000111
              ((00000011 executor (00101111 row)) (identity-relation same) row)
              ((00000011 executor (00101111 row)) (identity-relation distinct)
               (mechanism-selector-find-route sid executor (00000110 rows)))))
           ((00000011 sid (00000101 row)) (identity-relation distinct)
            (mechanism-selector-find-route sid executor (00000110 rows)))))))))

(00001001 mechanism-select
  (00001000 (sid executor)
    (00000111
      ((00000011
         (mechanism-selector-registry-has-sid?
           sid mechanism-selector-registry-rows)
         (00000001 no))
       (identity-relation same)
       (00100111
         (00000001 mechanism-selection-failure)
         (00000001 sid-not-in-function-table)
         sid))
      (t
       (10011100 ((route
               (mechanism-selector-find-route
                 sid executor mechanism-selector-routes)))
         (00000111
           ((00000010 route) (structural-kind empty-list)
            (00100111 (00000001 mechanism-unavailable) sid executor))
           ((00000010 route) (structural-kind pair)
            (00100111
              (00000001 mechanism-selected)
              sid
              executor
              (00110000 route)))))))))
