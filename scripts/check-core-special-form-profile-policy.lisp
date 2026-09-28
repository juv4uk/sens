; #1133 — executable witness for Lisp-owned special-form profile policy.

(00001001 csp-policy
  (00000101
    (01001011
      (10100110 "contracts/core-special-form-profile-policy.lisp"))))

(00001001 csp-rows (00000110 csp-policy))

(00001001 csp-find
  (00001000 (name rows)
    (00000111
      ((00000010 rows)
       ()
       (00000001 ()))
      ((00000010 rows)
       (0)
       (00000111
         ((00000011 (00000101 (00000101 rows)) name)
          (1)
          (00000101 rows))
         ((00000011 (00000101 (00000101 rows)) name)
          (0)
          (csp-find name (00000110 rows))))))))

(00001001 csp-row-check
  (00001000 (name expected)
    (10011100 ((actual (csp-find name csp-rows)))
      (00000111
        ((00100010 actual expected)
         (1)
         (00000001 ()))
        ((00100010 actual expected)
         (0)
         (00100111 (00000001 mismatch) name expected actual))))))

(00001001 csp-first-failure
  (00001000 (checks)
    (00000111
      ((00000010 checks)
       ()
       (00000001 ()))
      ((00000010 (00000101 checks))
       ()
       (csp-first-failure (00000110 checks)))
      ((00000010 (00000101 checks))
       (0)
       (00000101 checks))
      ((00000010 (00000101 checks))
       (1)
       (00000101 checks)))))

(00001001 csp-verdict
  (00001000 ()
    (10011100 ((failure
            (csp-first-failure
              (00100111
                (csp-row-check
                  (00000001 owner)
                  (00000001 (owner sens)))
                (csp-row-check
                  (00000001 cond-sid)
                  (00000001 (cond-sid 00000111)))
                (csp-row-check
                  (00000001 identity)
                  (00000001 (identity shared-across-profiles)))
                (csp-row-check
                  (00000001 selection-order)
                  (00000001 (selection-order profile-before-special-form-mechanism)))
                (csp-row-check
                  (00000001 core2)
                  (00000001
                    (core2
                      clause-family two-part
                      selection-rule historical-truthiness
                      exhaustion-result ()
                      contract (6 0)
                      law-source contracts/core2-profile-contract.lisp
                      activation runtime-profile-hook-required)))
                (csp-row-check
                  (00000001 core3)
                  (00000001
                    (core3
                      clause-family two-part
                      selection-rule historical-truthiness
                      exhaustion-result ()
                      contract (7 0)
                      law-source contracts/core3-profile-contract.lisp
                      activation experimental-profile)))
                (csp-row-check
                  (00000001 core4)
                  (00000001
                    (core4
                      clause-family three-part
                      selection-rule explicit-result-match
                      exhaustion-result UnsatisfiedConditional
                      contract (8 0)
                      law-source language-contract.lisp
                      activation current)))
                (csp-row-check
                  (00000001 implicit-profile-selection)
                  (00000001 (implicit-profile-selection forbidden)))
                (csp-row-check
                  (00000001 host-profile-law-table)
                  (00000001 (host-profile-law-table forbidden)))
                (csp-row-check
                  (00000001 runtime-profile-selector)
                  (00000001
                    (runtime-profile-selector
                      owner sens
                      state active-mechanical-hook)))))))
      (00000111
        ((00000010 failure)
         ()
         (00000001 (core-special-form-profile-policy-ok)))
        ((00000010 failure)
         (0)
         (00100111
           (00000001 core-special-form-profile-policy-violation)
           failure))
        ((00000010 failure)
         (1)
         (00100111
           (00000001 core-special-form-profile-policy-violation)
           failure))))))

(csp-verdict)