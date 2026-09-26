; tests/fixtures/world-transition-witness.lisp — Lisp-owned witness for #1312.
;
; Verifies that world state transitions and observations conform to
; contracts/world-transition-contract.lisp without host coercion.

(def wt-verify-law
  (lambda (name observed expected)
    (cond
      ((equal? observed expected) (list (quote ok) name))
      (t (list (quote fail) name (quote observed) observed (quote expected) expected)))))

(def wt-run-witness
  (lambda ()
    (let ((w0 (empty-world)))
      (let ((w1 (world-tell w0 (quote zoo) (quote ((has-fur cat))))))
        (let ((w2 (world-tell w1 (quote zoo) (quote ((has-fur dog))))))
          (let ((addr1 (world-content-address w1))
                (addr2 (world-content-address w2)))
            (list
              ; 1. Parent structural relation
              (wt-verify-law (quote parent-relation)
                             (equal? w0 (world-parent w1))
                             (quote (1)))
              ; 2. Content address self-identity (atoms compare via eq)
              (wt-verify-law (quote address-identity-same)
                             (eq? addr1 addr1)
                             (quote (1)))
              ; 3. Distinct world histories produce distinct content address identity
              (wt-verify-law (quote address-identity-distinct)
                             (eq? addr1 addr2)
                             (quote (0)))
              ; 4. World at depth recovery
              (wt-verify-law (quote depth-recovery)
                             (equal? w0 (world-at-depth w2 0))
                             (quote (1)))
              ; 5. Universal truth forbidden: structural equality does not equal atom t
              (wt-verify-law (quote universal-t-forbidden)
                             (equal? (equal? w0 w0) (quote (1)))
                             (quote (1))))))))))
