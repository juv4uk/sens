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
        ((path . "tools/important_file_guard.py") (independence_status . foreign) (owner-issue . "#5397") (migration_plan . "Git/NUL path transport only; all file-admission decisions belong to knowledge/file-authority-guard.lisp executed as physical SENS T5. Remaining debt: replace this Python carrier only after a native transport preserves exact paths and fail-closed status handling."))
        ((path . "tools/d10_hysteresis_chez.ss") (independence_status . foreign) (owner-issue . "#4013") (migration_plan . "Незалежний Chez Scheme oracle для точної D10 двопорогової семантики; не є мовною владою SENS; виконувані фізичні SENS свідки повинні окремо пройти паритет"))
       ))
     (new-python-without-entry . blocked)
     (new-python-outside-tools . blocked)
     (oracle-parity-before-host-retirement . required)
     (new-tool-does-not-own-semantics . 1))))