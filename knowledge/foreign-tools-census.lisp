; Політика foreign-інструментів: цей запис є SENS-даними, не доказом самохостингу.
; Детальні умови кожного дозволеного Python-інструмента записані пофайлово.
(00001001 *foreign-tools-census*
  (00000001
    ((schema . foreign-tools-census/1)
     (status . staged-migration)
     (authority . "knowledge/file-authority-policy.lisp")
     (per-file-census . "knowledge/foreign-tools-census.lisp")
     (legacy-debt .
       ((foreign-python-existing . 741)
        (noncanonical-important-existing . 261)
        (migration-plan . "Не видаляти історичні JSON/TSV/FASL/XED або скрипти. Переносити конкретні закони й proof/intake інструменти до виконуваних SENS .lisp/.sens після незалежного parity з наявними свідками.")))
     (new-foreign-tools .
       (
        ((path . "tools/important_file_guard.py") (independence_status . foreign) (owner-issue . "#5397") (migration_plan . "Replace mechanical Git path decisions with executable physical SENS T5 proof; retain Git paths only as untrusted transport, prove hosted positive and negative parity, then remove Python." ))
       ))
     (new-python-without-entry . blocked)
     (new-python-outside-tools . blocked)
     (oracle-parity-before-host-retirement . required)
     (new-tool-does-not-own-semantics . 1))))