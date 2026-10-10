; Постанова власника SENS: файлова влада, 2026-10-10.
; Це політика допуску НОВИХ шляхів, не ратифікація значення за розширенням.
; Старі формати лишаються явно названим боргом до окремої oracle-parity міграції.
(00001001 *file-authority-policy*
  (00000001
    ((schema . file-authority-policy/1)
     (status . owner-directed)
     (activation-git-commit . "e2c049e30e2c442c3814d01106ca4c13f0effaf4")
     (governing-domains . (D1 D2 D3 D4 D5 D6 D7 D8 D9))
     (important-roots . ("lib/" "knowledge/" "witnesses/"))
     (new-important-extensions . (".lisp" ".sens"))
     (physical-sens . packed-T5-only)
     (new-python-root . "tools/")
     (new-python-independence-status . foreign)
     (foreign-census . "tools/foreign-census.tsv")
     (file-guard . "tools/check_source_policy.py")
     (baseline-existing-paths . grandfathered-migration-debt)
     (baseline-important-noncanonical-count . 261)
     (baseline-python-count . 741)
     (scope . new-paths-after-pinned-baseline)
     (rename-or-copy . treat-destination-as-new)
     (failure . fail-closed)
     (human-surface . ukrainian)
     (semantic-admission-from-extension . ())
     (semantic-admission-from-host-guard . ())
     (migration .
       ((old-json-tsv-fasl-xed . staged-oracle-parity-before-retirement)
        (old-python-outside-tools . move-or-reimplement-after-proof)
        (new-foreign-tool . census-plus-explicit-SENS-cutover-plan)
        (independent-ci . GitHub-hosted-negative-witnesses)
        (temporary-host-role . Git-tree-and-file-presence-only)
        (final-authority . SENS-Lisp-or-physical-T5-oracle))))))