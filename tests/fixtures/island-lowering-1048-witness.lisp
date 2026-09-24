; #1048 / #1169 — current honest lowering witness.
; All admitted bounded-add transports carry arguments only under exact SID8 identity.
; CLIPS raw operator-text Eval remains diagnostic-only; semantic addition uses
; the same arguments-only payload as Common Lisp, Prolog and Datalog.

(load "lib/core4.lisp")
(load "lib/surface/semantic-registry-api.lisp")
(load "lib/mechanism-selector.lisp")
(load "lib/island-lowering.lisp")

(def island-lowering-1048-witness
  (lambda ()
    (let* ((plus-sid (semantic-registry-id (quote +)))
           (cl (island-lower-binary plus-sid (quote common-lisp) 2 3))
           (pl (island-lower-binary plus-sid (quote prolog) 2 3))
           (clips-result (island-lower-binary plus-sid (quote clips) 2 3))
           (dl (island-lower-binary plus-sid (quote datalog) 2 3)))
      (cond
        ((equal?
           cl
           (list (quote island-lowering-result)
                 plus-sid
                 (quote common-lisp)
                 (quote bounded-exact-add)
                 "2 3"))
         (structural-relation same)
         (cond
           ((equal?
              pl
              (list (quote island-lowering-result)
                    plus-sid
                    (quote prolog)
                    (quote bounded-exact-add)
                    "2 3"))
            (structural-relation same)
            (cond
              ((equal?
                 dl
                 (list (quote island-lowering-result)
                       plus-sid
                       (quote datalog)
                       (quote bounded-exact-add)
                       "2 3"))
               (structural-relation same)
               (cond
                 ((equal?
                    clips-result
                    (list (quote island-lowering-result)
                          plus-sid
                          (quote clips)
                          (quote bounded-exact-add)
                          "2 3"))
                  (structural-relation same)
                  (quote (island-lowering-1048 (status pass) (executable-payloads 4) (clips admitted-direct-sid8))))
                 ((quote witness-clips-fail) witness-clips-fail
                  (car (quote ())))))
              ((quote witness-datalog-fail) witness-datalog-fail
               (car (quote ())))))
           ((quote witness-prolog-fail) witness-prolog-fail
            (car (quote ())))))
        ((quote witness-cl-fail) witness-cl-fail
         (car (quote ())))))))

(island-lowering-1048-witness)
