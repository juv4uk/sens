; scripts/build-inventory.lisp — generate tests/fixtures/inventory.lisp from
; tests/fixtures/conformance.lisp (2026-09-01). Written in my-lisp itself so
; the canonical reader (read-all, write-to-string, sha256-hex) is the same
; one every conforming implementation has. The inventory is a *projection*,
; not a second source of truth — edit conformance.lisp, then rerun:
;
;   cargo run -p my-lisp-cli --bin my-lisp -- scripts/build-inventory.lisp > tests/fixtures/inventory.lisp
;
; Each inventory entry preserves the authoritative fields from conformance.lisp
; and adds stable content-addressed IDs plus mechanically observed forms.
; Never hand-edit the generated file.

(визначити приклади (читати-всі (читати-файл "tests/fixtures/conformance.lisp")))

;; ---- Helpers ----

(визначити знайти-пару
  (функція (ключ список-пар)
    (за-умовою ((атом? список-пар) ()) ((атом? (як-є ())) (за-умовою
           ((тотожне? (перше-першого список-пар) ключ) (перше список-пар))
           ((атом? (як-є ())) (знайти-за-ключем ключ (решта список-пар))))))))

(визначити знайти-рядок-пари
  (функція (ключ список-пар)
    (за-умовою ((атом? список-пар) ()) ((атом? (як-є ())) (за-умовою
           ((тотожне? (перше-першого список-пар) ключ) (решта (перше список-пар)))
           ((атом? (як-є ())) (знайти-рядок-пари ключ (решта список-пар))))))))

(визначити ключі-списку-пар
  (функція (список-пар)
    (за-умовою ((атом? список-пар) ()) ((атом? (як-є ())) (сполучити (перше-першого список-пар) (ключі-списку-пар (решта список-пар)))))))

;; Unique list (preserve order of first appearance)
(визначити унікальні
  (функція (список-хвіст)
    (за-умовою ((атом? список-хвіст) ()) ((атом? (як-є ())) (за-умовою
           ((значення-у-списку? (перше список-хвіст) (решта список-хвіст)) (унікальні (решта список-хвіст)))
           ((атом? (як-є ())) (сполучити (перше список-хвіст) (унікальні (решта список-хвіст)))))))))

;; Structural walk to collect observed-forms
;; Rules:
;; - quote        -> record 'quote, DO NOT recurse into argument (data, not code)
;; - lambda       -> record 'lambda, recurse into body only (not params)
;; - def          -> record 'def, recurse into value expression
;; - defmacro     -> record 'defmacro, recurse into macro body
;; - cond         -> record 'cond, recurse into each clause
;; - any other list (incl. if, and, or, builtins, user calls) -> record 'application, recurse into all elements
;; - atoms (symbols, numbers, strings) -> ignored (not structural forms)

(визначити обійти-спостережені
  (функція (значення)
    (за-умовою ((атом? значення) ()) ((атом? (як-є ())) (нехай ((голова (перше значення)))
         (за-умовою ((атом? голова) (за-умовою
              ((тотожне? голова (як-є quote))
               (список (як-є quote)))
              ((тотожне? голова (як-є lambda))
               (сполучити (як-є lambda)
                     (за-умовою ((атом? (решта-решти значення)) ()) ((атом? (як-є ())) (обійти-спостережені (перше (решта-решти значення)))))))
              ((тотожне? голова (як-є def))
               (сполучити (як-є def)
                     (за-умовою ((атом? (решта-решти значення)) ()) ((атом? (як-є ())) (обійти-спостережені (перше (решта-решти значення)))))))
              ((тотожне? голова (як-є defmacro))
               (сполучити (як-є defmacro)
                     (за-умовою ((атом? (решта-решти значення)) ())
                           ((атом? (решта (решта-решти значення))) ())
                           ((атом? (як-є ())) (обійти-спостережені (перше (решта (решта-решти значення))))))))
              ((тотожне? голова (як-є cond))
               (сполучити (як-є cond) (обійти-клаузи-умови (решта значення))))
              ((атом? (як-є ()))
               (сполучити (як-є application) (обійти-список значення))))) ((атом? (як-є ())) (сполучити (як-є application) (обійти-список значення)))))))))

(визначити обійти-клаузи-умови
  (функція (клаузи)
    (за-умовою ((атом? клаузи) ()) ((атом? (як-є ())) (приєднати (обійти-спостережені (перше-першого клаузи))
                 (приєднати (за-умовою ((атом? (решта (перше клаузи))) ()) ((атом? (як-є ())) (обійти-спостережені (друге (перше клаузи)))))
                         (обійти-клаузи-умови (решта клаузи))))))))

(визначити обійти-список
  (функція (список-хвіст)
    (за-умовою ((атом? список-хвіст) ()) ((атом? (як-є ())) (приєднати (обійти-спостережені (перше список-хвіст))
                 (обійти-список (решта список-хвіст)))))))

;; Parse expr using read-all (canonical), then walk for observed-forms.
;; For NumericOverflow fixtures, the parser rejects the literal, so we skip
;; reading and return empty observed-forms (honest: no structural forms observed).
(визначити отримати-спостережені-форми
  (функція (рядок-виразу вид-помилки)
    (за-умовою
      ((тотожне? вид-помилки "NumericOverflow")
       ())
      ((атом? (як-є ()))
       (нехай ((форми (читати-всі рядок-виразу)))
         (за-умовою ((атом? форми) ()) ((атом? (як-є ())) (унікальні (обійти-спостережені (перше форми))))))))))

;; Build identity record and compute ID
;; Identity includes axioms, not just expr+outcome: two fixtures can share the
;; exact same expr and expected outcome while being distinct constitutive
;; claims justified by different axioms (e.g. "(eq 3 3)" is asserted once
;; under G1's general equality and again under S1's numeric exactness) —
;; collapsing those into one ID would silently erase which axiom a fixture
;; is actually evidence for.
(визначити обчислити-ід
  (функція (вираз аксіоми вид-наслідку значення-наслідку)
    (нехай-послідовно ((запис-тотожності (список (сполучити (як-є вираз) вираз)
                          (сполучити (як-є axioms) аксіоми)
                          (сполучити вид-наслідку значення-наслідку)))
          (закодоване (значення-у-текст запис-тотожності))
          (хеш (геш-256-шістнадцятковий закодоване)))
      (рядок-додати "F-" (рядок-зріз хеш 0 16)))))

;; Process one fixture -> emit inventory record
(визначити вивести-приклад
  (функція (приклад)
    (нехай-послідовно ((вираз (знайти-рядок-пари (як-є вираз) приклад))
          (очікуване (знайти-рядок-пари (як-є expected) приклад))
          (вид-помилки (знайти-рядок-пари (як-є error) приклад))
          (ярус (знайти-рядок-пари (як-є tier) приклад))
          (аксіоми (знайти-рядок-пари (як-є axioms) приклад))
          (вимоги (знайти-рядок-пари (як-є requires) приклад))
          (роль (знайти-рядок-пари (як-є role) приклад))
          (нотатка (знайти-рядок-пари (як-є note) приклад))
          (вид-наслідку (за-умовою (очікуване (як-є expected)) ((атом? (як-є ())) (як-є error))))
          (значення-наслідку (за-умовою (очікуване очікуване) ((атом? (як-є ())) вид-помилки)))
          (ід (обчислити-ід вираз аксіоми вид-наслідку значення-наслідку))
          (спостережені-форми (отримати-спостережені-форми вираз вид-помилки)))
      (друкувати (список (як-є приклад)
                   (сполучити (як-є id) ід)
                   (сполучити (як-є tier) ярус)
                   (сполучити (як-є axioms) аксіоми)
                   (сполучити (як-є declared-requires) (за-умовою (вимоги вимоги) ((атом? (як-є ())) ())))
                   (сполучити (як-є observed-forms) спостережені-форми)
                   (сполучити (як-є outcome-kind) вид-наслідку)
                   (сполучити (як-є outcome-value) значення-наслідку)
                   (сполучити (як-є role) (за-умовою (роль роль) ((атом? (як-є ())) ())))
                   (сполучити (як-є note) (за-умовою (нотатка нотатка) ((атом? (як-є ())) ()))))))))

;; Emit all fixtures
(визначити вивести-всі
  (функція (залишок)
    (за-умовою ((атом? залишок) (як-є ())) ((атом? (як-є ())) (нехай ((надруковане (вивести-приклад (перше залишок))))
         (вивести-всі (решта залишок)))))))

;; Header
(друкувати (сполучити (як-є about) "tests/fixtures/inventory.lisp — deterministic index over tests/fixtures/conformance.lisp. Each entry carries a stable content-addressed ID (F-<16hex>), the authoritative tier/axioms/declared-requires, mechanically observed forms from canonical reader walk, and the expected outcome. Generated — do not hand-edit. Run: cargo run -p my-lisp-cli --bin my-lisp -- scripts/build-inventory.lisp > tests/fixtures/inventory.lisp"))
(друкувати (сполучити (як-є generated) "This file is GENERATED — do not hand-edit. It is a projection over tests/fixtures/conformance.lisp plus this script's canonical logic."))
(друкувати (сполучити (як-є source) "tests/fixtures/conformance.lisp"))

(вивести-всі приклади)

(як-є ())

; opt-in повна укр-поверхня: exact identity = lib/domains/d*.lisp; DEFINE-аліас, без нової диспетчеризації.
(визначити знайти-за-ключем знайти-пару)
