; tests/fixtures/world-transition-witness.lisp — Lisp-owned witness for #1312.
;
; Verifies that world state transitions and observations conform to
; contracts/world-transition-contract.lisp without host coercion.
; Ukrainian projection only.

(визначити wt-verify-law
  (функція (name observed expected)
    (за-умовою
      ((однакові? observed expected) (список (як-є ok) name))
      (так (список (як-є fail) name (як-є observed) observed (як-є expected) expected)))))

(визначити wt-run-witness
  (функція ()
    (нехай ((w0 (empty-world)))
      (нехай ((w1 (world-tell w0 (як-є zoo) (як-є ((has-fur cat))))))
        (нехай ((w2 (world-tell w1 (як-є zoo) (як-є ((has-fur dog))))))
          (нехай ((addr1 (world-content-address w1))
                (addr2 (world-content-address w2)))
            (список
              ; 1. Parent structural relation
              (wt-verify-law (як-є parent-relation)
                             (однакові? w0 (world-parent w1))
                             (як-є (1)))
              ; 2. Content address self-identity (atoms compare via eq)
              (wt-verify-law (як-є address-identity-same)
                             (тотожне? addr1 addr1)
                             (як-є (1)))
              ; 3. Distinct world histories produce distinct content address identity
              (wt-verify-law (як-є address-identity-distinct)
                             (тотожне? addr1 addr2)
                             (як-є (0)))
              ; 4. World at depth recovery
              (wt-verify-law (як-є depth-recovery)
                             (однакові? w0 (world-at-depth w2 0))
                             (як-є (1)))
              ; 5. Universal truth forbidden: structural equality does not equal atom t
              (wt-verify-law (як-є universal-t-forbidden)
                             (однакові? (однакові? w0 w0) (як-є (1)))
                             (як-є (1))))))))))
