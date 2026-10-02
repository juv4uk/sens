; #2376 — executable witness for the explicit mechanism laboratory.

(load "lib/core.lisp")
(load "lib/surface/semantic-registry-api.lisp")
(load "lib/mechanism-selector.lisp")
(load "lib/mechanism-lab.lisp")

(00001001 lab-plus-sid
  (semantic-registry-id (00000001 +)))

(00001001 lab-route-ok?
  (00001000 (executor)
    (10011100 ((selection (mechanism-lab-route lab-plus-sid executor)))
      (00000111
        ((00000010 selection) (0)
         (00000111
           ((00000011 (00000101 selection) (00000001 mechanism-selected))
            (1)
            (00000001 yes))
           ((00000001 lab-no) lab-no (00000001 no))))
        ((00000001 lab-no) lab-no (00000001 no))))))

(00001001 lab-all-routes?
  (00001000 ()
    (00000111
      ((00000011 (lab-route-ok? (00000001 common-lisp)) (00000001 yes)) (1)
       (00000111
         ((00000011 (lab-route-ok? (00000001 prolog)) (00000001 yes)) (1)
          (00000111
            ((00000011 (lab-route-ok? (00000001 clips)) (00000001 yes)) (1)
             (00000111
               ((00000011 (lab-route-ok? (00000001 datalog)) (00000001 yes)) (1)
                (00000001 yes))
               ((00000001 lab-no) lab-no (00000001 no))))
            ((00000001 lab-no) lab-no (00000001 no))))
         ((00000001 lab-no) lab-no (00000001 no))))
      ((00000001 lab-no) lab-no (00000001 no)))))

(00000111
  ((00000011 (lab-all-routes?) (00000001 yes)) (1)
   (00000001 (mechanism-lab-contract-ok (routes 4) (canon-round-trip pending-992) (clips-result available))))
  ((00000001 lab-fail) lab-fail
   (00000001 (mechanism-lab-contract-violation))))