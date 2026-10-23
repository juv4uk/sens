; #1117 — виконувана політика межі ABI ядра, якою володіє Lisp СЕНС.
; Хостові інструменти можуть механічно оглядати файли, але допущений напрям
; і заборонений зворотний авторитет визначено тут.
; Селектори «друге», «третє», «четверте» використовують ратифіковані
; визначення Д4, Д5 і Д6 без повторного локального визначення.


(визначити каб-контракт
  (перше
    (читати-всі
      (читати-файл "contracts/kernel-abi-transport-boundary.lisp"))))

(визначити каб-рядки (решта каб-контракт))

(визначити каб-знайти
  (функція (назва рядки)
    (за-умовою
      ((атом? рядки) (як-є ()))
      ((тотожне? (перше (перше рядки)) назва) (перше рядки))
      ((атом? (як-є ())) (каб-знайти назва (решта рядки))))))

(визначити каб-знайти-ядро
  (функція (назва-ядра рядки)
    (за-умовою
      ((атом? рядки) (як-є ()))
      ((атом? (як-є ()))
        (нехай ((рядок (перше рядки)))
          (за-умовою
            ((тотожне? (перше рядок) (як-є kernel))
             (за-умовою
               ((тотожне? (друге рядок) назва-ядра) рядок)
               ((атом? (як-є ())) (каб-знайти-ядро назва-ядра (решта рядки)))))
            ((атом? (як-є ())) (каб-знайти-ядро назва-ядра (решта рядки)))))))))

(визначити каб-перевірити-рядок
  (функція (назва очікуване)
    (нехай ((фактичне (каб-знайти назва каб-рядки)))
      (за-умовою
        ((однакові? фактичне очікуване) (як-є ()))
        ((атом? (як-є ())) (список (як-є policy-mismatch) назва очікуване фактичне))))))

(визначити каб-перевірити-рядок-ядра
  (функція (назва-ядра очікуване)
    (нехай ((фактичне (каб-знайти-ядро назва-ядра каб-рядки)))
      (за-умовою
        ((однакові? фактичне очікуване) (як-є ()))
        ((атом? (як-є ())) (список (як-є kernel-row-mismatch) назва-ядра очікуване фактичне))))))

(визначити каб-перша-невдача
  (функція (перевірки)
    (за-умовою
      ((атом? перевірки) (як-є ()))
      ((атом? (перше перевірки)) (каб-перша-невдача (решта перевірки)))
      ((атом? (як-є ())) (перше перевірки)))))

(визначити каб-вердикт
  (функція ()
    (нехай ((невдача
            (каб-перша-невдача
              (список
                (каб-перевірити-рядок
                  (як-є owner)
                  (як-є (owner sens)))
                (каб-перевірити-рядок
                  (як-є language-identity-type)
                  (як-є (language-identity-type CoreDomainIdentity)))
                (каб-перевірити-рядок
                  (як-є shared-abi-type)
                  (як-є (shared-abi-type WsmKernelRequest)))
                (каб-перевірити-рядок
                  (як-є shared-abi-field)
                  (як-є (shared-abi-field semantic_id)))
                (каб-перевірити-рядок
                  (як-є shared-abi-storage)
                  (як-є (shared-abi-storage opaque-u8)))
                (каб-перевірити-рядок
                  (як-є kernel-wrapper-type)
                  (як-є (kernel-wrapper-type LegacyAbiSemanticId)))
                (каб-перевірити-рядок
                  (як-є kernel-wrapper-role)
                  (як-є (kernel-wrapper-role transport-coordinate-only)))
                (каб-перевірити-рядок
                  (як-є wrapper-language-type-equivalence)
                  (як-є (wrapper-language-type-equivalence forbidden)))
                (каб-перевірити-рядок
                  (як-є kernel-to-language-authority)
                  (як-є (kernel-to-language-authority forbidden)))
                (каб-перевірити-рядок
                  (як-є kernel-may-query-semantic-registry)
                  (як-є (kernel-may-query-semantic-registry forbidden)))
                (каб-перевірити-рядок
                  (як-є kernel-may-import-language-identity-type)
                  (як-є (kernel-may-import-language-identity-type forbidden)))
                (каб-перевірити-рядок
                  (як-є kernel-may-mint-semantic-identity)
                  (як-є (kernel-may-mint-semantic-identity forbidden)))
                (каб-перевірити-рядок
                  (як-є reverse-direction)
                  (як-є
                    (reverse-direction
                      kernel-transport-to-language-meaning
                      forbidden)))
                (каб-перевірити-рядок
                  (як-є native-result-role)
                  (як-є (native-result-role observation-only)))
                (каб-перевірити-рядок
                  (як-є shared-abi-source)
                  (як-є
                    (shared-abi-source
                      "crates/wsm-kernel-c-abi/src/lib.rs"
                      "crates/wsm-kernel-c-abi/Cargo.toml")))
                (каб-перевірити-рядок-ядра
                  (як-є common-lisp)
                  (як-є
                    (kernel common-lisp
                      "crates/wsm-common-lisp-kernel/src/lib.rs"
                      "crates/wsm-common-lisp-kernel/Cargo.toml")))
                (каб-перевірити-рядок-ядра
                  (як-є prolog)
                  (як-є
                    (kernel prolog
                      "crates/wsm-prolog-kernel/src/lib.rs"
                      "crates/wsm-prolog-kernel/Cargo.toml")))
                (каб-перевірити-рядок-ядра
                  (як-є clips)
                  (як-є
                    (kernel clips
                      "crates/wsm-clips-kernel/src/lib.rs"
                      "crates/wsm-clips-kernel/Cargo.toml")))
                (каб-перевірити-рядок-ядра
                  (як-є datalog)
                  (як-є
                    (kernel datalog
                      "crates/wsm-datalog-kernel/src/lib.rs"
                      "crates/wsm-datalog-kernel/Cargo.toml")))))))
      (за-умовою
        ((атом? невдача)
         (список
           (як-є kernel-abi-transport-boundary-ok)
           (список (як-є kernels) (довжина (як-є (а б в г))))
           (список (як-є language-type) (як-є CoreDomainIdentity))
           (список (як-є abi-wrapper) (як-є LegacyAbiSemanticId))))
        ((атом? (як-є ())) (список (як-є kernel-abi-transport-boundary-violation) невдача))))))

(каб-вердикт)
