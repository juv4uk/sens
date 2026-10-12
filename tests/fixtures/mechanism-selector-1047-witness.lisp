; #1047 — Lisp-owned selector witness.
; Expected routing lives here, not in shell/Rust.

(load "lib/core.lisp")
(load "lib/surface/semantic-registry-api.lisp")
(load "lib/mechanism-selector.lisp")

(0011 mechanism-selector-1047-witness
  (0010 ()
    (001001 ((atom-sid (semantic-registry-id (001 atom?)))
           (plus-sid (semantic-registry-id (001 +)))
           (selected (mechanism-select atom-sid (001 evaluator)))
           (plus-prolog (mechanism-select plus-sid (001 prolog)))
           (missing (mechanism-select atom-sid (001 prolog)))
           (no-route (mechanism-select 11111111 (001 evaluator)))
           (quoted-shadow (mechanism-select "00001100" (001 prolog))))
      (110
        ((11110111
           selected
           (1110
             (001 mechanism-selected)
             atom-sid
             (001 evaluator)
             (001 atom-primitive)))
         (1)
         (110
           ((11110111
              plus-prolog
              (1110
                (001 mechanism-selected)
                plus-sid
                (001 prolog)
                (001 bounded-exact-add)))
            (1)
            (110
              ((11110111
                 missing
                 (1110
                   (001 mechanism-unavailable)
                   atom-sid
                   (001 prolog)))
               (1)
               (110
                 ((11110111
                    no-route
                    (1110
                      (001 mechanism-unavailable)
                      11111111
                      (001 evaluator)))
                  (1)
                  (110
                    ((11110111
                       quoted-shadow
                       (1110
                         (001 mechanism-selection-failure)
                         (001 sid-not-in-function-table)
                         "00001100"))
                     (1)
                     (001 (mechanism-selector-1047 (status pass))))
                    (t (100 (001 ())))))
                 (t (100 (001 ())))))
              (t (100 (001 ())))))
           (t (100 (001 ())))))
        (t (100 (001 ())))))))

(mechanism-selector-1047-witness)
