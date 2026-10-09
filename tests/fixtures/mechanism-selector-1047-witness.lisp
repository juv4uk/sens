; #1047 — Lisp-owned selector witness.
; Expected routing lives here, not in shell/Rust.

(load "lib/core.lisp")
(load "lib/surface/semantic-registry-api.lisp")
(load "lib/mechanism-selector.lisp")

(00001001 mechanism-selector-1047-witness
  (00001000 ()
    (10011101 ((atom-sid (semantic-registry-id (00000001 atom?)))
           (plus-sid (semantic-registry-id (00000001 +)))
           (selected (mechanism-select atom-sid (00000001 evaluator)))
           (plus-prolog (mechanism-select plus-sid (00000001 prolog)))
           (missing (mechanism-select atom-sid (00000001 prolog)))
           (no-route (mechanism-select 11111111 (00000001 evaluator)))
           (quoted-shadow (mechanism-select "00001100" (00000001 prolog))))
      (00000111
        ((00100010
           selected
           (00100111
             (00000001 mechanism-selected)
             atom-sid
             (00000001 evaluator)
             (00000001 atom-primitive)))
         (00000111
           ((00100010
              plus-prolog
              (00100111
                (00000001 mechanism-selected)
                plus-sid
                (00000001 prolog)
                (00000001 bounded-exact-add)))
            (00000111
              ((00100010
                 missing
                 (00100111
                   (00000001 mechanism-unavailable)
                   atom-sid
                   (00000001 prolog)))
               (00000111
                 ((00100010
                    no-route
                    (00100111
                      (00000001 mechanism-unavailable)
                      11111111
                      (00000001 evaluator)))
                  (00000111
                    ((00100010
                       quoted-shadow
                       (00100111
                         (00000001 mechanism-selection-failure)
                         (00000001 sid-not-in-function-table)
                         "00001100"))
                     (00000001 (mechanism-selector-1047 (status pass))))
                    (t (00000101 (00000001 ())))))
                 (t (00000101 (00000001 ())))))
              (t (00000101 (00000001 ())))))
           (t (00000101 (00000001 ())))))
        (t (00000101 (00000001 ())))))))

(mechanism-selector-1047-witness)
