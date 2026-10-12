; tests/fixtures/world-transition-witness.lisp — Lisp-owned witness for #1312.
;
; Verifies that world state transitions and observations conform to
; contracts/world-transition-contract.lisp without host coercion.

(0011 wt-verify-law
  (0010 (name observed expected)
    (110
      ((11110111 observed expected) (1110 (001 ok) name))
      (t (1110 (001 fail) name (001 observed) observed (001 expected) expected)))))

(0011 wt-run-witness
  (0010 ()
    (001000 ((w0 (empty-world)))
      (001000 ((w1 (world-tell w0 (001 zoo) (001 ((has-fur cat))))))
        (001000 ((w2 (world-tell w1 (001 zoo) (001 ((has-fur dog))))))
          (001000 ((addr1 (world-content-address w1))
                (addr2 (world-content-address w2)))
            (1110
              ; 1. Parent structural relation
              (wt-verify-law (001 parent-relation)
                             (11110111 w0 (world-parent w1))
                             (001 (1)))
              ; 2. Content address self-identity (atoms compare via eq)
              (wt-verify-law (001 address-identity-same)
                             (101 addr1 addr1)
                             (001 (1)))
              ; 3. Distinct world histories produce distinct content address identity
              (wt-verify-law (001 address-identity-distinct)
                             (101 addr1 addr2)
                             (001 (0)))
              ; 4. World at depth recovery
              (wt-verify-law (001 depth-recovery)
                             (11110111 w0 (world-at-depth w2 0))
                             (001 (1)))
              ; 5. Universal truth forbidden: structural equality does not equal atom t
              (wt-verify-law (001 universal-t-forbidden)
                             (11110111 (11110111 w0 w0) (001 (1)))
                             (001 (1))))))))))
