; #1047 — Lisp-owned selector witness.
; Expected routing lives here, not in shell/Rust.

(load "lib/core.lisp")
(load "lib/surface/semantic-registry-api.lisp")
(load "lib/mechanism-selector.lisp")

(def mechanism-selector-1047-witness
  (lambda ()
    (let* ((atom-sid (semantic-registry-id (quote atom)))
           (plus-sid (semantic-registry-id (quote +)))
           (selected (mechanism-select atom-sid (quote evaluator)))
           (plus-prolog (mechanism-select plus-sid (quote prolog)))
           (missing (mechanism-select atom-sid (quote prolog)))
           (no-route (mechanism-select 11111111 (quote evaluator)))
           (quoted-shadow (mechanism-select "00001100" (quote prolog))))
      (cond
        ((equal?
           selected
           (list
             (quote mechanism-selected)
             atom-sid
             (quote evaluator)
             (quote atom-primitive)))
         (structural-relation same)
         (cond
           ((equal?
              plus-prolog
              (list
                (quote mechanism-selected)
                plus-sid
                (quote prolog)
                (quote bounded-exact-add)))
            (structural-relation same)
            (cond
              ((equal?
                 missing
                 (list
                   (quote mechanism-unavailable)
                   atom-sid
                   (quote prolog)))
               (structural-relation same)
               (cond
                 ((equal?
                    no-route
                    (list
                      (quote mechanism-unavailable)
                      11111111
                      (quote evaluator)))
                  (structural-relation same)
                  (cond
                    ((equal?
                       quoted-shadow
                       (list
                         (quote mechanism-selection-failure)
                         (quote sid-not-in-function-table)
                         "00001100"))
                     (structural-relation same)
                     (quote (mechanism-selector-1047 (status pass))))
                    (t (car (quote ())))))
                 (t (car (quote ())))))
              (t (car (quote ())))))
           (t (car (quote ())))))
        (t (car (quote ())))))))

(mechanism-selector-1047-witness)
