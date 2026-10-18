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

(визначити second (функція (x) (перше (решта x))))
(визначити third (функція (x) (перше (решта (решта x)))))
(визначити fourth (функція (x) (перше (решта (решта (решта x))))))
(визначити fifth (функція (x) (перше (решта (решта (решта (решта x)))))))

(визначити rust-changes (читати-всі (read-file "tests/rust-retirement-changes.lisp")))

(визначити rust-retirement-verdict-for
  (функція (changes)
    (за-умовою
      ((атом? changes) (structural-kind empty-list)
       (як-є (rust-retirement-ok)))
      ((атом? changes) (structural-kind pair)
       (001000 ((change (100 changes)))
         (001000 ((path (second change)))
           (001000 ((additions (third change)))
             (001000 ((status (fifth change)))
               (за-умовою
                 ((тотожне? status (як-є new)) (identity-relation same)
                  (список
                    (як-є rust-retirement-violation)
                    path
                    additions
                    status
                    "New Rust paths are forbidden during retirement. See #299."))
                 ((тотожне? status (як-є new)) (identity-relation distinct)
                  (за-умовою
                    ((= additions 0) 1
                     (rust-retirement-verdict-for (решта changes)))
                    ((= additions 0) 0
                     (список
                       (як-є rust-retirement-violation)
                       path
                       additions
                       status
                       "Rust may only shrink; added Rust lines are forbidden. See #299.")))))))))))))

(rust-retirement-verdict-for rust-changes)

; opt-in повна укр-поверхня: exact identity = lib/domains/d*.lisp; DEFINE-аліас, без нової диспетчеризації.
(визначити читати-всі read-all)
