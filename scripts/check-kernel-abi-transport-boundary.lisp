; #1117 — executable Lisp-owned policy for kernel ABI identity scope.
; Host tooling may mechanically inspect files, but the admitted direction and
; forbidden reverse authority are owned here.

(визначити second (функція (x) (перше (решта x))))
(визначити third (функція (x) (перше (решта (решта x)))))
(визначити fourth (функція (x) (перше (решта (решта (решта x))))))

(визначити kab-contract
  (перше
    (читати-всі
      (читати-файл "contracts/kernel-abi-transport-boundary.lisp"))))

(визначити kab-rows (решта kab-contract))

(визначити kab-find
  (функція (name rows)
    (за-умовою
      ((атом? rows)
       ()
       (як-є ()))
      ((атом? rows)
       (0)
       (за-умовою
         ((тотожне? (перше (перше rows)) name)
          (1)
          (перше rows))
         ((тотожне? (перше (перше rows)) name)
          (0)
          (kab-find name (решта rows))))))))

(визначити kab-find-kernel
  (функція (kernel-name rows)
    (за-умовою
      ((атом? rows)
       ()
       (як-є ()))
      ((атом? rows)
       (0)
       (нехай ((row (перше rows)))
         (за-умовою
           ((тотожне? (перше row) (як-є kernel))
            (1)
            (за-умовою
              ((тотожне? (second row) kernel-name)
               (1)
               row)
              ((тотожне? (second row) kernel-name)
               (0)
               (kab-find-kernel kernel-name (решта rows)))))
           ((тотожне? (перше row) (як-є kernel))
            (0)
            (kab-find-kernel kernel-name (решта rows)))))))))

(визначити kab-row-check
  (функція (name expected)
    (нехай ((actual (kab-find name kab-rows)))
      (за-умовою
        ((однакові? actual expected)
         (1)
         (як-є ()))
        ((однакові? actual expected)
         (0)
         (список (як-є policy-mismatch) name expected actual))))))

(визначити kab-kernel-row-check
  (функція (kernel-name expected)
    (нехай ((actual (kab-find-kernel kernel-name kab-rows)))
      (за-умовою
        ((однакові? actual expected)
         (1)
         (як-є ()))
        ((однакові? actual expected)
         (0)
         (список (як-є kernel-row-mismatch) kernel-name expected actual))))))

(визначити kab-first-failure
  (функція (checks)
    (за-умовою
      ((атом? checks)
       ()
       (як-є ()))
      ((атом? (перше checks))
       ()
       (kab-first-failure (решта checks)))
      ((атом? (перше checks))
       (0)
       (перше checks))
      ((атом? (перше checks))
       (1)
       (перше checks)))))

(визначити kab-verdict
  (функція ()
    (нехай ((failure
            (kab-first-failure
              (список
                (kab-row-check
                  (як-є owner)
                  (як-є (owner sens)))
                (kab-row-check
                  (як-є language-identity-type)
                  (як-є (language-identity-type CoreDomainIdentity)))
                (kab-row-check
                  (як-є shared-abi-type)
                  (як-є (shared-abi-type WsmKernelRequest)))
                (kab-row-check
                  (як-є shared-abi-field)
                  (як-є (shared-abi-field semantic_id)))
                (kab-row-check
                  (як-є shared-abi-storage)
                  (як-є (shared-abi-storage opaque-u8)))
                (kab-row-check
                  (як-є kernel-wrapper-type)
                  (як-є (kernel-wrapper-type LegacyAbiSemanticId)))
                (kab-row-check
                  (як-є kernel-wrapper-role)
                  (як-є (kernel-wrapper-role transport-coordinate-only)))
                (kab-row-check
                  (як-є wrapper-language-type-equivalence)
                  (як-є (wrapper-language-type-equivalence forbidden)))
                (kab-row-check
                  (як-є kernel-to-language-authority)
                  (як-є (kernel-to-language-authority forbidden)))
                (kab-row-check
                  (як-є kernel-may-query-semantic-registry)
                  (як-є (kernel-may-query-semantic-registry forbidden)))
                (kab-row-check
                  (як-є kernel-may-import-language-identity-type)
                  (як-є (kernel-may-import-language-identity-type forbidden)))
                (kab-row-check
                  (як-є kernel-may-mint-semantic-identity)
                  (як-є (kernel-may-mint-semantic-identity forbidden)))
                (kab-row-check
                  (як-є reverse-direction)
                  (як-є
                    (reverse-direction
                      kernel-transport-to-language-meaning
                      forbidden)))
                (kab-row-check
                  (як-є native-result-role)
                  (як-є (native-result-role observation-only)))
                (kab-row-check
                  (як-є shared-abi-source)
                  (як-є
                    (shared-abi-source
                      "crates/wsm-kernel-c-abi/src/lib.rs"
                      "crates/wsm-kernel-c-abi/Cargo.toml")))
                (kab-kernel-row-check
                  (як-є common-lisp)
                  (як-є
                    (kernel common-lisp
                      "crates/wsm-common-lisp-kernel/src/lib.rs"
                      "crates/wsm-common-lisp-kernel/Cargo.toml")))
                (kab-kernel-row-check
                  (як-є prolog)
                  (як-є
                    (kernel prolog
                      "crates/wsm-prolog-kernel/src/lib.rs"
                      "crates/wsm-prolog-kernel/Cargo.toml")))
                (kab-kernel-row-check
                  (як-є clips)
                  (як-є
                    (kernel clips
                      "crates/wsm-clips-kernel/src/lib.rs"
                      "crates/wsm-clips-kernel/Cargo.toml")))
                (kab-kernel-row-check
                  (як-є datalog)
                  (як-є
                    (kernel datalog
                      "crates/wsm-datalog-kernel/src/lib.rs"
                      "crates/wsm-datalog-kernel/Cargo.toml")))))))
      (за-умовою
        ((атом? failure)
         ()
         (як-є
           (kernel-abi-transport-boundary-ok
             (kernels 4)
             (language-type CoreDomainIdentity)
             (abi-wrapper LegacyAbiSemanticId))))
        ((атом? failure)
         (0)
         (список
           (як-є kernel-abi-transport-boundary-violation)
           failure))
        ((атом? failure)
         (1)
         (список
           (як-є kernel-abi-transport-boundary-violation)
           failure))))))

(kab-verdict)