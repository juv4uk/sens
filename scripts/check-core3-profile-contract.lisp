; #1134 — executable witness for the thin Core3 profile.

(load "lib/core4.lisp")
(load "lib/surface/semantic-registry-api.lisp")
(load "lib/mechanism-selector.lisp")
(load "lib/core3.lisp")

(визначити c3-plus-sid
  (semantic-registry-id (як-є +)))

(визначити c3-route-ok?
  (функція (executor)
    (001000 ((selection (core3-route c3-plus-sid executor)))
      (за-умовою
        ((хибне? (атом? selection))
         (за-умовою
           ((тотожне? (перше selection) (як-є mechanism-selected))
            (як-є yes))
           ((атом? (як-є ())) (як-є no))))
        ((атом? (як-є ())) (як-є no))))))

(визначити c3-all-routes?
  (функція ()
    (за-умовою
      ((тотожне? (c3-route-ok? (як-є common-lisp)) (як-є yes))
       (за-умовою
         ((тотожне? (c3-route-ok? (як-є prolog)) (як-є yes))
          (за-умовою
            ((тотожне? (c3-route-ok? (як-є clips)) (як-є yes))
             (за-умовою
               ((тотожне? (c3-route-ok? (як-є datalog)) (як-є yes))
                (як-є yes))
               ((атом? (як-є ())) (як-є no))))
            ((атом? (як-є ())) (як-є no))))
         ((атом? (як-є ())) (як-є no))))
      ((атом? (як-є ())) (як-є no)))))

(за-умовою
  ((тотожне? (c3-all-routes?) (як-є yes))
   (як-є (core3-profile-contract-ok (routes 4) (canon-round-trip pending-992) (clips-result available))))
  ((атом? (як-є ()))
   (як-є (core3-profile-contract-violation))))