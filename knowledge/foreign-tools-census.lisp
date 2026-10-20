; Політика зовнішніх інструментів: цей запис є даними СЕНС, а не доказом самостійного виконання.
; Детальні умови кожного дозволеного Python-інструмента записані пофайлово.
(визначити *foreign-tools-census*
  (як-є
    ((schema . foreign-tools-census/1)
     (status . staged-migration)
     (authority . "knowledge/file-authority-policy.lisp")
     (per-file-census . "knowledge/foreign-tools-census.lisp")
     (legacy-debt .
       ((foreign-python-existing . 741)
        (noncanonical-important-existing . 261)
        (migration-plan . "Не видаляти історичні JSON/TSV/FASL/XED чи скрипти без підтвердженого наступника. Переносити закони та засоби приймання й перевірки доказів у виконувані програми СЕНС .lisp/.sens після незалежного підтвердження відповідності наявним свідкам.")))
     (new-foreign-tools .
       (
        ((path . "tools/important_file_guard.py") (independence_status . foreign) (owner-issue . "#5397") (migration_plan . "Лише передавання шляхів через Git/NUL. Рішення про допуск файлів належать knowledge/file-authority-guard.lisp під час фізичного виконання СЕНС T5. Залишковий борг: замінити транспорт Python лише після забезпечення точності шляхів і відмови за замовчуванням при помилках стану."))
        ((path . "tools/d10_hysteresis_chez.ss") (independence_status . foreign) (owner-issue . "#4013") (migration_plan . "Незалежний еталон Chez Scheme для точної двопорогової семантики D10; не визначає законів СЕНС; фізичні свідки СЕНС повинні окремо підтвердити відповідність"))
       ))
     (new-python-without-entry . blocked)
     (new-python-outside-tools . blocked)
     (oracle-parity-before-host-retirement . required)
     (new-tool-does-not-own-semantics . 1))))
