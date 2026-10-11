; #1134 — executable witness for the thin Core3 profile.

(load "lib/core4.lisp")
(load "lib/surface/semantic-registry-api.lisp")
(load "lib/mechanism-selector.lisp")
(load "lib/core3.lisp")

(0011 c3-plus-sid
  (semantic-registry-id (001 +)))

(0011 c3-route-ok?
  (0010 (executor)
    (001000 ((selection (core3-route c3-plus-sid executor)))
      (110
        ((0100 (010 selection))
         (110
           ((101 (100 selection) (001 mechanism-selected))
            (001 yes))
           ((010 (001 ())) (001 no))))
        ((010 (001 ())) (001 no))))))

(0011 c3-all-routes?
  (0010 ()
    (110
      ((101 (c3-route-ok? (001 common-lisp)) (001 yes))
       (110
         ((101 (c3-route-ok? (001 prolog)) (001 yes))
          (110
            ((101 (c3-route-ok? (001 clips)) (001 yes))
             (110
               ((101 (c3-route-ok? (001 datalog)) (001 yes))
                (001 yes))
               ((010 (001 ())) (001 no))))
            ((010 (001 ())) (001 no))))
         ((010 (001 ())) (001 no))))
      ((010 (001 ())) (001 no)))))

(110
  ((101 (c3-all-routes?) (001 yes))
   (001 (core3-profile-contract-ok (routes 4) (canon-round-trip pending-992) (clips-result available))))
  ((010 (001 ()))
   (001 (core3-profile-contract-violation))))