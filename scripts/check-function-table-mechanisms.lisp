; #1046 — fail-closed validation for transitional mechanism metadata.
; Semantic identity authority is ONLY lib/surface/semantic-registry.lisp.
; This checker proves mechanism metadata cannot invent a function beside that table.
; #1332/#1403: empty-list-ground is not a function mechanism.

(00001001 registry
  (00000101 (01001011 (10100110 "lib/surface/semantic-registry.lisp"))))

(00001001 metadata
  (00000101 (01001011 (10100110 "lib/function-table-mechanisms.lisp"))))

(00001001 registry-rows registry)

(00001001 find-section
  (00001000 (name sections)
    (00000111
      ((00000010 sections) () (00000001 ()))
      ((00000010 sections) (0)
       (00000111
         ((00000011 (00000101 (00000101 sections)) name) (1)
          (00000101 sections))
         ((00000011 (00000101 (00000101 sections)) name) (0)
          (find-section name (00000110 sections))))))))

(00001001 metadata-rows
  (00000110 (find-section (00000001 rows) metadata)))

(00001001 registry-has-sid?
  (00001000 (sid rows)
    (00000111
      ((00000010 rows) () (00000001 no))
      ((00000010 rows) (0)
       (00000111
         ((00000011 sid (00000101 (00000101 rows))) (1) (00000001 yes))
         ((00000011 sid (00000101 (00000101 rows))) (0)
          (registry-has-sid? sid (00000110 rows))))))))

(00001001 metadata-has-route?
  (00001000 (sid executor rows)
    (00000111
      ((00000010 rows) () (00000001 no))
      ((00000010 rows) (0)
       (10011100 ((row (00000101 rows)))
         (00000111
           ((00000011 sid (00000101 row)) (1)
            (00000111
              ((00000011 executor (00101111 row)) (1) (00000001 yes))
              ((00000011 executor (00101111 row)) (0)
               (metadata-has-route? sid executor (00000110 rows)))))
           ((00000011 sid (00000101 row)) (0)
            (metadata-has-route? sid executor (00000110 rows)))))))))

(00001001 admitted-executor?
  (00001000 (executor)
    (00000111
      ((00000011 executor (00000001 evaluator)) (1) (00000001 yes))
      ((00000011 executor (00000001 common-lisp)) (1) (00000001 yes))
      ((00000011 executor (00000001 prolog)) (1) (00000001 yes))
      ((00000011 executor (00000001 clips)) (1) (00000001 yes))
      ((00000011 executor (00000001 datalog)) (1) (00000001 yes))
      (t (00000001 no)))))

(00001001 admitted-mechanism?
  (00001000 (mechanism)
    (00000111
      ((00000011 mechanism (00000001 quote-form)) (1) (00000001 yes))
      ((00000011 mechanism (00000001 atom-primitive)) (1) (00000001 yes))
      ((00000011 mechanism (00000001 eq-primitive)) (1) (00000001 yes))
      ((00000011 mechanism (00000001 cons-primitive)) (1) (00000001 yes))
      ((00000011 mechanism (00000001 car-primitive)) (1) (00000001 yes))
      ((00000011 mechanism (00000001 cdr-primitive)) (1) (00000001 yes))
      ((00000011 mechanism (00000001 cond-form)) (1) (00000001 yes))
      ((00000011 mechanism (00000001 lambda-form)) (1) (00000001 yes))
      ((00000011 mechanism (00000001 define-form)) (1) (00000001 yes))
      ((00000011 mechanism (00000001 bounded-exact-add)) (1) (00000001 yes))
      (t (00000001 no)))))

(00001001 validate-rows
  (00001000 (rows)
    (00000111
      ((00000010 rows) ()
       (00000001 (function-table-mechanisms-ok)))
      ((00000010 rows) (0)
       (10011101 ((row (00000101 rows))
              (sid (00000101 row))
              (executor (00101111 row))
              (mechanism (00110000 row)))
         (00000111
           ((00000011 (admitted-executor? executor) (00000001 no))
            (1)
            (00100111 (00000001 function-table-mechanisms-violation)
                  (00000001 unsupported-executor) sid executor))
           ((00000011 (registry-has-sid? sid registry-rows) (00000001 no))
            (1)
            (00100111 (00000001 function-table-mechanisms-violation)
                  (00000001 sid-not-in-canon-function-table) sid))
           ((00000011 (metadata-has-route? sid executor (00000110 rows)) (00000001 yes))
            (1)
            (00100111 (00000001 function-table-mechanisms-violation)
                  (00000001 duplicate-executor-route) sid executor))
           ((00000011 (admitted-mechanism? mechanism) (00000001 no))
            (1)
            (00100111 (00000001 function-table-mechanisms-violation)
                  (00000001 unsupported-mechanism) sid mechanism))
           (t (validate-rows (00000110 rows)))))))))

(00001001 verdict (validate-rows metadata-rows))
(01001000 verdict)
