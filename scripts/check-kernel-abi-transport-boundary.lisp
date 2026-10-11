; #1117 — executable Lisp-owned policy for kernel ABI identity scope.
; Host tooling may mechanically inspect files, but the admitted direction and
; forbidden reverse authority are owned here.

(0011 second (0010 (x) (100 (011 x))))
(0011 third (0010 (x) (100 (011 (011 x)))))
(0011 fourth (0010 (x) (100 (011 (011 (011 x))))))

(0011 kab-contract
  (100
    (110101001
      (110110111 "contracts/kernel-abi-transport-boundary.lisp"))))

(0011 kab-rows (011 kab-contract))

(0011 kab-find
  (0010 (name rows)
    (110
      ((010 rows)
       ()
       (001 ()))
      ((010 rows)
       (0)
       (110
         ((101 (100 (100 rows)) name)
          (1)
          (100 rows))
         ((101 (100 (100 rows)) name)
          (0)
          (kab-find name (011 rows))))))))

(0011 kab-find-kernel
  (0010 (kernel-name rows)
    (110
      ((010 rows)
       ()
       (001 ()))
      ((010 rows)
       (0)
       (001000 ((row (100 rows)))
         (110
           ((101 (100 row) (001 kernel))
            (1)
            (110
              ((101 (second row) kernel-name)
               (1)
               row)
              ((101 (second row) kernel-name)
               (0)
               (kab-find-kernel kernel-name (011 rows)))))
           ((101 (100 row) (001 kernel))
            (0)
            (kab-find-kernel kernel-name (011 rows)))))))))

(0011 kab-row-check
  (0010 (name expected)
    (001000 ((actual (kab-find name kab-rows)))
      (110
        ((11110111 actual expected)
         (1)
         (001 ()))
        ((11110111 actual expected)
         (0)
         (1110 (001 policy-mismatch) name expected actual))))))

(0011 kab-kernel-row-check
  (0010 (kernel-name expected)
    (001000 ((actual (kab-find-kernel kernel-name kab-rows)))
      (110
        ((11110111 actual expected)
         (1)
         (001 ()))
        ((11110111 actual expected)
         (0)
         (1110 (001 kernel-row-mismatch) kernel-name expected actual))))))

(0011 kab-first-failure
  (0010 (checks)
    (110
      ((010 checks)
       ()
       (001 ()))
      ((010 (100 checks))
       ()
       (kab-first-failure (011 checks)))
      ((010 (100 checks))
       (0)
       (100 checks))
      ((010 (100 checks))
       (1)
       (100 checks)))))

(0011 kab-verdict
  (0010 ()
    (001000 ((failure
            (kab-first-failure
              (1110
                (kab-row-check
                  (001 owner)
                  (001 (owner sens)))
                (kab-row-check
                  (001 language-identity-type)
                  (001 (language-identity-type CoreDomainIdentity)))
                (kab-row-check
                  (001 shared-abi-type)
                  (001 (shared-abi-type WsmKernelRequest)))
                (kab-row-check
                  (001 shared-abi-field)
                  (001 (shared-abi-field semantic_id)))
                (kab-row-check
                  (001 shared-abi-storage)
                  (001 (shared-abi-storage opaque-u8)))
                (kab-row-check
                  (001 kernel-wrapper-type)
                  (001 (kernel-wrapper-type LegacyAbiSemanticId)))
                (kab-row-check
                  (001 kernel-wrapper-role)
                  (001 (kernel-wrapper-role transport-coordinate-only)))
                (kab-row-check
                  (001 wrapper-language-type-equivalence)
                  (001 (wrapper-language-type-equivalence forbidden)))
                (kab-row-check
                  (001 kernel-to-language-authority)
                  (001 (kernel-to-language-authority forbidden)))
                (kab-row-check
                  (001 kernel-may-query-semantic-registry)
                  (001 (kernel-may-query-semantic-registry forbidden)))
                (kab-row-check
                  (001 kernel-may-import-language-identity-type)
                  (001 (kernel-may-import-language-identity-type forbidden)))
                (kab-row-check
                  (001 kernel-may-mint-semantic-identity)
                  (001 (kernel-may-mint-semantic-identity forbidden)))
                (kab-row-check
                  (001 reverse-direction)
                  (001
                    (reverse-direction
                      kernel-transport-to-language-meaning
                      forbidden)))
                (kab-row-check
                  (001 native-result-role)
                  (001 (native-result-role observation-only)))
                (kab-row-check
                  (001 shared-abi-source)
                  (001
                    (shared-abi-source
                      "crates/wsm-kernel-c-abi/src/lib.rs"
                      "crates/wsm-kernel-c-abi/Cargo.toml")))
                (kab-kernel-row-check
                  (001 common-lisp)
                  (001
                    (kernel common-lisp
                      "crates/wsm-common-lisp-kernel/src/lib.rs"
                      "crates/wsm-common-lisp-kernel/Cargo.toml")))
                (kab-kernel-row-check
                  (001 prolog)
                  (001
                    (kernel prolog
                      "crates/wsm-prolog-kernel/src/lib.rs"
                      "crates/wsm-prolog-kernel/Cargo.toml")))
                (kab-kernel-row-check
                  (001 clips)
                  (001
                    (kernel clips
                      "crates/wsm-clips-kernel/src/lib.rs"
                      "crates/wsm-clips-kernel/Cargo.toml")))
                (kab-kernel-row-check
                  (001 datalog)
                  (001
                    (kernel datalog
                      "crates/wsm-datalog-kernel/src/lib.rs"
                      "crates/wsm-datalog-kernel/Cargo.toml")))))))
      (110
        ((010 failure)
         ()
         (001
           (kernel-abi-transport-boundary-ok
             (kernels 4)
             (language-type CoreDomainIdentity)
             (abi-wrapper LegacyAbiSemanticId))))
        ((010 failure)
         (0)
         (1110
           (001 kernel-abi-transport-boundary-violation)
           failure))
        ((010 failure)
         (1)
         (1110
           (001 kernel-abi-transport-boundary-violation)
           failure))))))

(kab-verdict)