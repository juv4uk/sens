; #1047 — Lisp-owned selector witness.
; Expected routing lives here, not in shell/Rust.
; Ukrainian projection only.

(load "lib/core.lisp")
(load "lib/surface/semantic-registry-api.lisp")
(load "lib/mechanism-selector.lisp")

(визначити mechanism-selector-1047-witness
  (функція ()
    (нехай ((atom-sid (semantic-registry-id (як-є atom?)))
           (plus-sid (semantic-registry-id (як-є +)))
           (selected (mechanism-select atom-sid (як-є evaluator)))
           (plus-prolog (mechanism-select plus-sid (як-є prolog)))
           (missing (mechanism-select atom-sid (як-є prolog)))
           (no-route (mechanism-select 255 (як-є evaluator)))
           (quoted-shadow (mechanism-select "00001100" (як-є prolog))))
      (за-умовою
        ((однакові?
           selected
           (список
             (як-є mechanism-selected)
             atom-sid
             (як-є evaluator)
             (як-є atom-primitive)))
         (за-умовою
           ((однакові?
              plus-prolog
              (список
                (як-є mechanism-selected)
                plus-sid
                (як-є prolog)
                (як-є bounded-exact-add)))
            (за-умовою
              ((однакові?
                 missing
                 (список
                   (як-є mechanism-unavailable)
                   atom-sid
                   (як-є prolog)))
               (за-умовою
                 ((однакові?
                    no-route
                    (список
                      (як-є mechanism-unavailable)
                      255
                      (як-є evaluator)))
                  (за-умовою
                    ((однакові?
                       quoted-shadow
                       (список
                         (як-є mechanism-selection-failure)
                         (як-є sid-not-in-function-table)
                         "00001100"))
                     (як-є (mechanism-selector-1047 (status pass))))
                    (так (перше (як-є ())))))
                 (так (перше (як-є ())))))
              (так (перше (як-є ())))))
           (так (перше (як-є ())))))
        (так (перше (як-є ())))))))

(mechanism-selector-1047-witness)
