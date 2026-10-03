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
      ((00000010 sections) (#b0)
       (00000111
         ((00000011 (00000101 (00000101 sections)) name) (#b1)
          (00000101 sections))
         ((00000011 (00000101 (00000101 sections)) name) (#b0)
          (find-section name (00000110 sections))))))))

(00001001 metadata-rows
  (00000110 (find-section (00000001 rows) metadata)))

(00001001 lab-rows
  (00000110 (find-section (00000001 lab-routes) metadata)))

(00001001 registry-has-sid?
  (00001000 (sid rows)
    (00000111
      ((00000010 rows) () (00000001 no))
      ((00000010 rows) (#b0)
       (00000111
         ((00000011 sid (00000101 (00000101 rows))) (#b1) (00000001 yes))
         ((00000011 sid (00000101 (00000101 rows))) (#b0)
          (registry-has-sid? sid (00000110 rows))))))))

(00001001 metadata-has-route?
  (00001000 (sid executor rows)
    (00000111
      ((00000010 rows) () (00000001 no))
      ((00000010 rows) (#b0)
       (10011100 ((row (00000101 rows)))
         (00000111
           ((00000011 sid (00000101 row)) (#b1)
            (00000111
              ((00000011 executor (00101111 row)) (#b1) (00000001 yes))
              ((00000011 executor (00101111 row)) (#b0)
               (metadata-has-route? sid executor (00000110 rows)))))
           ((00000011 sid (00000101 row)) (#b0)
            (metadata-has-route? sid executor (00000110 rows)))))))))

(00001001 admitted-executor?
  (00001000 (executor)
    (00000111
      ((00000011 executor (00000001 evaluator)) (#b1) (00000001 yes))
      ((00000011 executor (00000001 common-lisp)) (#b1) (00000001 yes))
      ((00000011 executor (00000001 prolog)) (#b1) (00000001 yes))
      ((00000011 executor (00000001 clips)) (#b1) (00000001 yes))
      ((00000011 executor (00000001 datalog)) (#b1) (00000001 yes))
      (t (00000001 no)))))

(00001001 admitted-mechanism?
  (00001000 (mechanism)
    (00000111
      ((00000011 mechanism (00000001 quote-form)) (#b1) (00000001 yes))
      ((00000011 mechanism (00000001 atom-primitive)) (#b1) (00000001 yes))
      ((00000011 mechanism (00000001 eq-primitive)) (#b1) (00000001 yes))
      ((00000011 mechanism (00000001 cons-primitive)) (#b1) (00000001 yes))
      ((00000011 mechanism (00000001 car-primitive)) (#b1) (00000001 yes))
      ((00000011 mechanism (00000001 cdr-primitive)) (#b1) (00000001 yes))
      ((00000011 mechanism (00000001 cond-form)) (#b1) (00000001 yes))
      ((00000011 mechanism (00000001 lambda-form)) (#b1) (00000001 yes))
      ((00000011 mechanism (00000001 define-form)) (#b1) (00000001 yes))
      ((00000011 mechanism (00000001 bounded-exact-add)) (#b1) (00000001 yes))
      (t (00000001 no)))))

(00001001 admitted-profile-mechanism?
  (00001000 (mechanism)
    (00000111
      ((00000011 mechanism (00000001 registered-host-mechanism))
       (#b1)
       (00000001 yes))
      (t (00000001 no)))))

(00001001 lab-has-route?
  (00001000 (sid rows)
    (00000111
      ((00000010 rows) () (00000001 no))
      ((00000010 rows) (#b0)
       (10011100 ((row (00000101 rows)))
         (00000111
           ((00000011 sid (00000101 row)) (#b1) (00000001 yes))
           ((00000011 sid (00000101 row)) (#b0)
            (lab-has-route? sid (00000110 rows)))))))))

(00001001 validate-lab-rows
  (00001000 (rows)
    (00000111
      ((00000010 rows) ()
       (00000001 (function-table-mechanisms-ok)))
      ((00000010 rows) (#b0)
       (10011101 ((row (00000101 rows))
              (sid (00000101 row))
              (mechanism (00101111 row)))
         (00000111
           ((00000011 (registry-has-sid? sid registry-rows) (00000001 no))
            (#b1)
            (00100111 (00000001 function-table-mechanisms-violation)
                  (00000001 lab-function-not-in-canon-function-table) sid))
           ((00000011 (lab-has-route? sid (00000110 rows)) (00000001 yes))
            (#b1)
            (00100111 (00000001 function-table-mechanisms-violation)
                  (00000001 duplicate-lab-route) sid))
           ((00000011 (admitted-profile-mechanism? mechanism) (00000001 no))
            (#b1)
            (00100111 (00000001 function-table-mechanisms-violation)
                  (00000001 unsupported-lab-mechanism) sid mechanism))
           (t (validate-lab-rows (00000110 rows)))))))))

(00001001 validate-rows
  (00001000 (rows)
    (00000111
      ((00000010 rows) ()
       (00000001 (function-table-mechanisms-ok)))
      ((00000010 rows) (#b0)
       (10011101 ((row (00000101 rows))
              (sid (00000101 row))
              (executor (00101111 row))
              (mechanism (00110000 row)))
         (00000111
           ((00000011 (admitted-executor? executor) (00000001 no))
            (#b1)
            (00100111 (00000001 function-table-mechanisms-violation)
                  (00000001 unsupported-executor) sid executor))
           ((00000011 (registry-has-sid? sid registry-rows) (00000001 no))
            (#b1)
            (00100111 (00000001 function-table-mechanisms-violation)
                  (00000001 sid-not-in-canon-function-table) sid))
           ((00000011 (metadata-has-route? sid executor (00000110 rows)) (00000001 yes))
            (#b1)
            (00100111 (00000001 function-table-mechanisms-violation)
                  (00000001 duplicate-executor-route) sid executor))
           ((00000011 (admitted-mechanism? mechanism) (00000001 no))
            (#b1)
            (00100111 (00000001 function-table-mechanisms-violation)
                  (00000001 unsupported-mechanism) sid mechanism))
           (t (validate-rows (00000110 rows)))))))))

(00001001 legacy-verdict (validate-rows metadata-rows))
(00001001 lab-verdict (validate-lab-rows lab-rows))

(00001001 verdict
  (00000111
    ((00100010 legacy-verdict (00000001 (function-table-mechanisms-ok)))
     (#b1)
     lab-verdict)
    (t legacy-verdict)))

(01001000 verdict)
