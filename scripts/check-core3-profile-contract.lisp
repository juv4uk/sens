; #1134 — executable witness for the thin Core3 profile.

(load "lib/core.lisp")
(load "lib/surface/semantic-registry-api.lisp")
(load "lib/mechanism-selector.lisp")
(load "lib/core3.lisp")

(00001001 c3-plus-sid
  (semantic-registry-id (00000001 +)))

(00001001 c3-route-ok?
  (00001000 (executor)
    (10011100 ((selection (core3-route c3-plus-sid executor)))
      (00000111
        ((00000010 selection) (0)
         (00000111
           ((00000011 (00000101 selection) (00000001 mechanism-selected))
            (1)
            (00000001 yes))
           ((00000001 c3-no) c3-no (00000001 no))))
        ((00000001 c3-no) c3-no (00000001 no))))))

(00001001 c3-all-routes?
  (00001000 ()
    (00000111
      ((00000011 (c3-route-ok? (00000001 common-lisp)) (00000001 yes)) (1)
       (00000111
         ((00000011 (c3-route-ok? (00000001 prolog)) (00000001 yes)) (1)
          (00000111
            ((00000011 (c3-route-ok? (00000001 clips)) (00000001 yes)) (1)
             (00000111
               ((00000011 (c3-route-ok? (00000001 datalog)) (00000001 yes)) (1)
                (00000001 yes))
               ((00000001 c3-no) c3-no (00000001 no))))
            ((00000001 c3-no) c3-no (00000001 no))))
         ((00000001 c3-no) c3-no (00000001 no))))
      ((00000001 c3-no) c3-no (00000001 no)))))

(00000111
  ((00000011 (c3-all-routes?) (00000001 yes)) (1)
   (00000001 (core3-profile-contract-ok (routes 4) (canon-round-trip pending-992) (clips-result available))))
  ((00000001 c3-fail) c3-fail
   (00000001 (core3-profile-contract-violation))))