; #1134 — executable witness for the thin Core3 profile.

(load "lib/core4.lisp")
(load "lib/surface/semantic-registry-api.lisp")
(load "lib/mechanism-selector.lisp")
(load "lib/core3.lisp")

(def c3-plus-sid
  (semantic-registry-id (quote +)))

(def c3-route-ok?
  (lambda (executor)
    (let ((selection (core3-route c3-plus-sid executor)))
      (cond
        ((atom? selection) (0)
         (cond
           ((eq? (car selection) (quote mechanism-selected))
            (1)
            (quote yes))
           ((quote c3-no) c3-no (quote no))))
        ((quote c3-no) c3-no (quote no))))))

(def c3-all-routes?
  (lambda ()
    (cond
      ((eq? (c3-route-ok? (quote common-lisp)) (quote yes)) (1)
       (cond
         ((eq? (c3-route-ok? (quote prolog)) (quote yes)) (1)
          (cond
            ((eq? (c3-route-ok? (quote clips)) (quote yes)) (1)
             (cond
               ((eq? (c3-route-ok? (quote datalog)) (quote yes)) (1)
                (quote yes))
               ((quote c3-no) c3-no (quote no))))
            ((quote c3-no) c3-no (quote no))))
         ((quote c3-no) c3-no (quote no))))
      ((quote c3-no) c3-no (quote no)))))

(cond
  ((eq? (c3-all-routes?) (quote yes)) (1)
   (quote (core3-profile-contract-ok (routes 4) (canon-round-trip pending-992) (clips-result available))))
  ((quote c3-fail) c3-fail
   (quote (core3-profile-contract-violation))))