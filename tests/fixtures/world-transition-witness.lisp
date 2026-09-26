; tests/fixtures/world-transition-witness.lisp — Lisp-owned witness for #1312.
;
; Verifies that world state transitions and observations conform to
; contracts/world-transition-contract.lisp without host coercion.

(00001001 wt-verify-law
  (00001000 (name observed expected)
    (00000111
      ((00100010 observed expected) (00100111 (00000001 ok) name))
      (t (00100111 (00000001 fail) name (00000001 observed) observed (00000001 expected) expected)))))

(00001001 wt-run-witness
  (00001000 ()
    (10011100 ((w0 (empty-world)))
      (10011100 ((w1 (world-tell w0 (00000001 zoo) (00000001 ((has-fur cat))))))
        (10011100 ((w2 (world-tell w1 (00000001 zoo) (00000001 ((has-fur dog))))))
          (10011100 ((addr1 (world-content-address w1))
                (addr2 (world-content-address w2)))
            (00100111
              ; 1. Parent structural relation
              (wt-verify-law (00000001 parent-relation)
                             (00100010 w0 (world-parent w1))
                             (00000001 (1)))
              ; 2. Content address self-identity (atoms compare via eq)
              (wt-verify-law (00000001 address-identity-same)
                             (00000011 addr1 addr1)
                             (00000001 (1)))
              ; 3. Distinct world histories produce distinct content address identity
              (wt-verify-law (00000001 address-identity-distinct)
                             (00000011 addr1 addr2)
                             (00000001 (0)))
              ; 4. World at depth recovery
              (wt-verify-law (00000001 depth-recovery)
                             (00100010 w0 (world-at-depth w2 0))
                             (00000001 (1)))
              ; 5. Universal truth forbidden: structural equality does not equal atom t
              (wt-verify-law (00000001 universal-t-forbidden)
                             (00100010 (00100010 w0 w0) (00000001 (1)))
                             (00000001 (1))))))))))
