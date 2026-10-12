; #1048 / #1169 — current honest lowering witness.
; All admitted bounded-add transports carry arguments only under exact SID8 identity.
; CLIPS raw operator-text Eval remains diagnostic-only; semantic addition uses
; the same arguments-only payload as Common Lisp, Prolog and Datalog.
;
; The payload numbers are the canonical machine wire (#q2:<bits>/<bits>) that
; write-to-string owns since #1648, not decimal text: this is a mechanism
; transport, not a human presentation (#1693, #1656).

(load "lib/core.lisp")
(load "lib/surface/semantic-registry-api.lisp")
(load "lib/mechanism-selector.lisp")
(load "lib/island-lowering.lisp")

(0011 island-lowering-1048-witness
  (0010 ()
    (001001 ((plus-sid 00001100)
           (cl (island-lower-binary plus-sid (001 common-lisp) 2 3))
           (pl (island-lower-binary plus-sid (001 prolog) 2 3))
           (clips-result (island-lower-binary plus-sid (001 clips) 2 3))
           (dl (island-lower-binary plus-sid (001 datalog) 2 3)))
      (110
        ((11110111
           cl
           (1110 (001 island-lowering-result)
                 plus-sid
                 (001 common-lisp)
                 (001 bounded-exact-add)
                 "#q2:10/1 #q2:11/1"))
         (1)
         (110
           ((11110111
              pl
              (1110 (001 island-lowering-result)
                    plus-sid
                    (001 prolog)
                    (001 bounded-exact-add)
                    "#q2:10/1 #q2:11/1"))
            (1)
            (110
              ((11110111
                 dl
                 (1110 (001 island-lowering-result)
                       plus-sid
                       (001 datalog)
                       (001 bounded-exact-add)
                       "#q2:10/1 #q2:11/1"))
               (1)
               (110
                 ((11110111
                    clips-result
                    (1110 (001 island-lowering-result)
                          plus-sid
                          (001 clips)
                          (001 bounded-exact-add)
                          "#q2:10/1 #q2:11/1"))
                  (1)
                  (001 (island-lowering-1048 (status pass) (executable-payloads 4) (clips admitted-direct-sid8))))
                 ((001 witness-clips-fail) witness-clips-fail
                  (100 (001 ())))))
              ((001 witness-datalog-fail) witness-datalog-fail
               (100 (001 ())))))
           ((001 witness-prolog-fail) witness-prolog-fail
            (100 (001 ())))))
        ((001 witness-cl-fail) witness-cl-fail
         (100 (001 ())))))))

(island-lowering-1048-witness)
