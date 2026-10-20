; #1048 / #1169 — current honest lowering witness.
; Ukrainian projection only. Payload wire format remains mechanism transport.
; Semantic addition uses the same arguments-only payload across islands.

(load "lib/core.lisp")
(load "lib/surface/semantic-registry-api.lisp")
(load "lib/mechanism-selector.lisp")
(load "lib/island-lowering.lisp")

(визначити island-lowering-1048-witness
  (функція ()
    (нехай ((plus-sid 12)
           (cl (island-lower-binary plus-sid (як-є common-lisp) 2 3))
           (pl (island-lower-binary plus-sid (як-є prolog) 2 3))
           (clips-result (island-lower-binary plus-sid (як-є clips) 2 3))
           (dl (island-lower-binary plus-sid (як-є datalog) 2 3)))
      (за-умовою
        ((однакові?
           cl
           (список (як-є island-lowering-result)
                 plus-sid
                 (як-є common-lisp)
                 (як-є bounded-exact-add)
                 "#q2:10/1 #q2:11/1"))
         (за-умовою
           ((однакові?
              pl
              (список (як-є island-lowering-result)
                    plus-sid
                    (як-є prolog)
                    (як-є bounded-exact-add)
                    "#q2:10/1 #q2:11/1"))
            (за-умовою
              ((однакові?
                 dl
                 (список (як-є island-lowering-result)
                       plus-sid
                       (як-є datalog)
                       (як-є bounded-exact-add)
                       "#q2:10/1 #q2:11/1"))
               (за-умовою
                 ((однакові?
                    clips-result
                    (список (як-є island-lowering-result)
                          plus-sid
                          (як-є clips)
                          (як-є bounded-exact-add)
                          "#q2:10/1 #q2:11/1"))
                  (як-є (island-lowering-1048 (status pass) (executable-payloads 4) (clips admitted-direct))))
                 (так (перше (як-є ())))))
              (так (перше (як-є ())))))
           (так (перше (як-є ())))))
        (так (перше (як-є ())))))))

(island-lowering-1048-witness)
