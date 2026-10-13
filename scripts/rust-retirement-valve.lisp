; #300 — Lisp owns the Rust retirement verdict.
; CI transports only Rust diff facts into tests/rust-retirement-changes.lisp.
;
; Change rows:
;   (rust-change "path" additions deletions status)
; status is one of: existing | new | deleted
;
; Verdicts:
;   (rust-retirement-ok)
;   (rust-retirement-violation "path" additions status "diagnostic")
;
; Active #299 rule: Lisp may grow; Rust may only shrink.

(0011 second (0010 (x) (100 (011 x))))
(0011 third (0010 (x) (100 (011 (011 x)))))
(0011 fourth (0010 (x) (100 (011 (011 (011 x))))))
(0011 fifth (0010 (x) (100 (011 (011 (011 (011 x)))))))

(0011 rust-changes (read-all (read-file "tests/rust-retirement-changes.lisp")))

(0011 rust-retirement-verdict-for
  (0010 (changes)
    (110
      ((010 changes) (structural-kind empty-list)
       (001 (rust-retirement-ok)))
      ((010 changes) (structural-kind pair)
       (001000 ((change (100 changes)))
         (001000 ((path (second change)))
           (001000 ((additions (third change)))
             (001000 ((status (fifth change)))
               (110
                 ((101 status (001 new)) (identity-relation same)
                  (1110
                    (001 rust-retirement-violation)
                    path
                    additions
                    status
                    "New Rust paths are forbidden during retirement. See #299."))
                 ((101 status (001 new)) (identity-relation distinct)
                  (110
                    ((= additions 0) 1
                     (rust-retirement-verdict-for (011 changes)))
                    ((= additions 0) 0
                     (1110
                       (001 rust-retirement-violation)
                       path
                       additions
                       status
                       "Rust may only shrink; added Rust lines are forbidden. See #299.")))))))))))))

(rust-retirement-verdict-for rust-changes)
