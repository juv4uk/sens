; #1117 — мовна перевірка межі тотожності ядрового ABI.
; Зовнішні інструменти можуть механічно перевіряти файли,
; але допущений напрям повноважень та заборону зворотного
; семантичного впливу визначає тільки СЕНС.
; Значення протокольних полів і шляхи файлів залишаються незмінними.

(визначити абі-друге (функція (значення) (перше (решта значення))))
(визначити абі-третє (функція (значення) (перше (решта (решта значення)))))
(визначити абі-четверте (функція (значення) (перше (решта (решта (решта значення))))))

(визначити контракт-межі-абі
  (перше
    (читати-всі
      (читати-файл "contracts/kernel-abi-transport-boundary.lisp"))))

(визначити рядки-межі-абі (решта контракт-межі-абі))

(визначити знайти-поле-абі
  (функція (назва рядки)
    (за-умовою
      ((атом? рядки)
       ()
       (як-є ()))
      ((атом? рядки)
       (0)
       (за-умовою
         ((тотожне? (перше (перше рядки)) назва)
          (1)
          (перше рядки))
         ((тотожне? (перше (перше рядки)) назва)
          (0)
          (знайти-поле-абі назва (решта рядки))))))))

(визначити знайти-ядро-абі
  (функція (назва-ядра рядки)
    (за-умовою
      ((атом? рядки)
       ()
       (як-є ()))
      ((атом? рядки)
       (0)
       (нехай ((рядок (перше рядки)))
         (за-умовою
           ((тотожне? (перше рядок) (як-є kernel))
            (1)
            (за-умовою
              ((тотожне? (абі-друге рядок) назва-ядра)
               (1)
               рядок)
              ((тотожне? (абі-друге рядок) назва-ядра)
               (0)
               (знайти-ядро-абі назва-ядра (решта рядки)))))
           ((тотожне? (перше рядок) (як-є kernel))
            (0)
            (знайти-ядро-абі назва-ядра (решта рядки)))))))))

(визначити перевірити-поле-абі
  (функція (назва очікуване)
    (нехай ((отримане (знайти-поле-абі назва рядки-межі-абі)))
      (за-умовою
        ((однакові? отримане очікуване)
         (1)
         (як-є ()))
        ((однакові? отримане очікуване)
         (0)
         (список (як-є policy-mismatch) назва очікуване отримане))))))

(визначити перевірити-рядок-ядра-абі
  (функція (назва-ядра очікуване)
    (нехай ((отримане (знайти-ядро-абі назва-ядра рядки-межі-абі)))
      (за-умовою
        ((однакові? отримане очікуване)
         (1)
         (як-є ()))
        ((однакові? отримане очікуване)
         (0)
         (список (як-є kernel-row-mismatch) назва-ядра очікуване отримане))))))

(визначити перша-помилка-абі
  (функція (перевірки)
    (за-умовою
      ((атом? перевірки)
       ()
       (як-є ()))
      ((атом? (перше перевірки))
       ()
       (перша-помилка-абі (решта перевірки)))
      ((атом? (перше перевірки))
       (0)
       (перше перевірки))
      ((атом? (перше перевірки))
       (1)
       (перше перевірки)))))

(визначити висновок-межі-абі
  (функція ()
    (нехай ((помилка
            (перша-помилка-абі
              (список
                (перевірити-поле-абі
                  (як-є owner)
                  (як-є (owner sens)))
                (перевірити-поле-абі
                  (як-є language-identity-type)
                  (як-є (language-identity-type CoreDomainIdentity)))
                (перевірити-поле-абі
                  (як-є shared-abi-type)
                  (як-є (shared-abi-type WsmKernelRequest)))
                (перевірити-поле-абі
                  (як-є shared-abi-field)
                  (як-є (shared-abi-field semantic_id)))
                (перевірити-поле-абі
                  (як-є shared-abi-storage)
                  (як-є (shared-abi-storage opaque-u8)))
                (перевірити-поле-абі
                  (як-є kernel-wrapper-type)
                  (як-є (kernel-wrapper-type LegacyAbiSemanticId)))
                (перевірити-поле-абі
                  (як-є kernel-wrapper-role)
                  (як-є (kernel-wrapper-role transport-coordinate-only)))
                (перевірити-поле-абі
                  (як-є wrapper-language-type-equivalence)
                  (як-є (wrapper-language-type-equivalence forbidden)))
                (перевірити-поле-абі
                  (як-є kernel-to-language-authority)
                  (як-є (kernel-to-language-authority forbidden)))
                (перевірити-поле-абі
                  (як-є kernel-may-query-semantic-registry)
                  (як-є (kernel-may-query-semantic-registry forbidden)))
                (перевірити-поле-абі
                  (як-є kernel-may-import-language-identity-type)
                  (як-є (kernel-may-import-language-identity-type forbidden)))
                (перевірити-поле-абі
                  (як-є kernel-may-mint-semantic-identity)
                  (як-є (kernel-may-mint-semantic-identity forbidden)))
                (перевірити-поле-абі
                  (як-є reverse-direction)
                  (як-є
                    (reverse-direction
                      kernel-transport-to-language-meaning
                      forbidden)))
                (перевірити-поле-абі
                  (як-є native-result-role)
                  (як-є (native-result-role observation-only)))
                (перевірити-поле-абі
                  (як-є shared-abi-source)
                  (як-є
                    (shared-abi-source
                      "crates/wsm-kernel-c-abi/src/lib.rs"
                      "crates/wsm-kernel-c-abi/Cargo.toml")))
                (перевірити-рядок-ядра-абі
                  (як-є common-lisp)
                  (як-є
                    (kernel common-lisp
                      "crates/wsm-common-lisp-kernel/src/lib.rs"
                      "crates/wsm-common-lisp-kernel/Cargo.toml")))
                (перевірити-рядок-ядра-абі
                  (як-є prolog)
                  (як-є
                    (kernel prolog
                      "crates/wsm-prolog-kernel/src/lib.rs"
                      "crates/wsm-prolog-kernel/Cargo.toml")))
                (перевірити-рядок-ядра-абі
                  (як-є clips)
                  (як-є
                    (kernel clips
                      "crates/wsm-clips-kernel/src/lib.rs"
                      "crates/wsm-clips-kernel/Cargo.toml")))
                (перевірити-рядок-ядра-абі
                  (як-є datalog)
                  (як-є
                    (kernel datalog
                      "crates/wsm-datalog-kernel/src/lib.rs"
                      "crates/wsm-datalog-kernel/Cargo.toml")))))))
      (за-умовою
        ((атом? помилка)
         ()
         (як-є
           (kernel-abi-transport-boundary-ok
             (kernels 4)
             (language-type CoreDomainIdentity)
             (abi-wrapper LegacyAbiSemanticId))))
        ((атом? помилка)
         (0)
         (список
           (як-є kernel-abi-transport-boundary-violation)
           помилка))
        ((атом? помилка)
         (1)
         (список
           (як-є kernel-abi-transport-boundary-violation)
           помилка))))))

(висновок-межі-абі)