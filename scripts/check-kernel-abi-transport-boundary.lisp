; #1117 — executable Lisp-owned policy for kernel ABI identity scope.
; Host tooling may mechanically inspect files, but the admitted direction and
; forbidden reverse authority are owned here.

(00001001 second (00001000 (x) (00000101 (00000110 x))))
(00001001 third (00001000 (x) (00000101 (00000110 (00000110 x)))))
(00001001 fourth (00001000 (x) (00000101 (00000110 (00000110 (00000110 x))))))

(00001001 kab-contract
  (00000101
    (01001011
      (10100110 "contracts/kernel-abi-transport-boundary.lisp"))))

(00001001 kab-rows (00000110 kab-contract))

(00001001 kab-find
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
          (kab-find name (00000110 rows))))))))

(00001001 kab-find-kernel
  (00001000 (kernel-name rows)
    (00000111
      ((00000010 rows)
       ()
       (00000001 ()))
      ((00000010 rows)
       (0)
       (10011100 ((row (00000101 rows)))
         (00000111
           ((00000011 (00000101 row) (00000001 kernel))
            (1)
            (00000111
              ((00000011 (second row) kernel-name)
               (1)
               row)
              ((00000011 (second row) kernel-name)
               (0)
               (kab-find-kernel kernel-name (00000110 rows)))))
           ((00000011 (00000101 row) (00000001 kernel))
            (0)
            (kab-find-kernel kernel-name (00000110 rows)))))))))

(00001001 kab-row-check
  (00001000 (name expected)
    (10011100 ((actual (kab-find name kab-rows)))
      (00000111
        ((00100010 actual expected)
         (1)
         (00000001 ()))
        ((00100010 actual expected)
         (0)
         (00100111 (00000001 policy-mismatch) name expected actual))))))

(00001001 kab-kernel-row-check
  (00001000 (kernel-name expected)
    (10011100 ((actual (kab-find-kernel kernel-name kab-rows)))
      (00000111
        ((00100010 actual expected)
         (1)
         (00000001 ()))
        ((00100010 actual expected)
         (0)
         (00100111 (00000001 kernel-row-mismatch) kernel-name expected actual))))))

(00001001 kab-first-failure
  (00001000 (checks)
    (00000111
      ((00000010 checks)
       ()
       (00000001 ()))
      ((00000010 (00000101 checks))
       ()
       (kab-first-failure (00000110 checks)))
      ((00000010 (00000101 checks))
       (0)
       (00000101 checks))
      ((00000010 (00000101 checks))
       (1)
       (00000101 checks)))))

(00001001 kab-verdict
  (00001000 ()
    (10011100 ((failure
            (kab-first-failure
              (00100111
                (kab-row-check
                  (00000001 owner)
                  (00000001 (owner sens)))
                (kab-row-check
                  (00000001 language-identity-type)
                  (00000001 (language-identity-type CoreDomainIdentity)))
                (kab-row-check
                  (00000001 shared-abi-type)
                  (00000001 (shared-abi-type WsmKernelRequest)))
                (kab-row-check
                  (00000001 shared-abi-field)
                  (00000001 (shared-abi-field semantic_id)))
                (kab-row-check
                  (00000001 shared-abi-storage)
                  (00000001 (shared-abi-storage opaque-u8)))
                (kab-row-check
                  (00000001 kernel-wrapper-type)
                  (00000001 (kernel-wrapper-type LegacyAbiSemanticId)))
                (kab-row-check
                  (00000001 kernel-wrapper-role)
                  (00000001 (kernel-wrapper-role transport-coordinate-only)))
                (kab-row-check
                  (00000001 wrapper-language-type-equivalence)
                  (00000001 (wrapper-language-type-equivalence forbidden)))
                (kab-row-check
                  (00000001 kernel-to-language-authority)
                  (00000001 (kernel-to-language-authority forbidden)))
                (kab-row-check
                  (00000001 kernel-may-query-semantic-registry)
                  (00000001 (kernel-may-query-semantic-registry forbidden)))
                (kab-row-check
                  (00000001 kernel-may-import-language-identity-type)
                  (00000001 (kernel-may-import-language-identity-type forbidden)))
                (kab-row-check
                  (00000001 kernel-may-mint-semantic-identity)
                  (00000001 (kernel-may-mint-semantic-identity forbidden)))
                (kab-row-check
                  (00000001 reverse-direction)
                  (00000001
                    (reverse-direction
                      kernel-transport-to-language-meaning
                      forbidden)))
                (kab-row-check
                  (00000001 native-result-role)
                  (00000001 (native-result-role observation-only)))
                (kab-row-check
                  (00000001 shared-abi-source)
                  (00000001
                    (shared-abi-source
                      "crates/wsm-kernel-c-abi/src/lib.rs"
                      "crates/wsm-kernel-c-abi/Cargo.toml")))
                (kab-kernel-row-check
                  (00000001 common-lisp)
                  (00000001
                    (kernel common-lisp
                      "crates/wsm-common-lisp-kernel/src/lib.rs"
                      "crates/wsm-common-lisp-kernel/Cargo.toml")))
                (kab-kernel-row-check
                  (00000001 prolog)
                  (00000001
                    (kernel prolog
                      "crates/wsm-prolog-kernel/src/lib.rs"
                      "crates/wsm-prolog-kernel/Cargo.toml")))
                (kab-kernel-row-check
                  (00000001 clips)
                  (00000001
                    (kernel clips
                      "crates/wsm-clips-kernel/src/lib.rs"
                      "crates/wsm-clips-kernel/Cargo.toml")))
                (kab-kernel-row-check
                  (00000001 datalog)
                  (00000001
                    (kernel datalog
                      "crates/wsm-datalog-kernel/src/lib.rs"
                      "crates/wsm-datalog-kernel/Cargo.toml")))))))
      (00000111
        ((00000010 failure)
         ()
         (00000001
           (kernel-abi-transport-boundary-ok
             (kernels 4)
             (language-type CoreDomainIdentity)
             (abi-wrapper LegacyAbiSemanticId))))
        ((00000010 failure)
         (0)
         (00100111
           (00000001 kernel-abi-transport-boundary-violation)
           failure))
        ((00000010 failure)
         (1)
         (00100111
           (00000001 kernel-abi-transport-boundary-violation)
           failure))))))

(kab-verdict)