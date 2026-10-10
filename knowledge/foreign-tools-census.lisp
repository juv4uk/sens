; Перепис сторонніх інструментів. SENS лишається джерелом закону.
; Шлях + independence_status=foreign + окремий план міграції обов'язкові
; для КОЖНОГО нового файла-механізму host у tools/.
(00001001 *foreign-tools-census*
  (00000001
    ((schema . foreign-tools-census/1)
     (status . staged-migration)
     (authority . "knowledge/file-authority-policy.lisp")
     (legacy-debt .
       ((foreign-python-existing . 741)
        (noncanonical-important-existing . 261)
        (migration-plan . "міграція: інвентаризувати старі scripts/, tests/, benchmarks/, research/ та knowledge/; перенести перевірювані закони у виконувані SENS .lisp/.sens за незалежним oracle parity; не вилучати ратифікаційні JSON або Core4 FASL без замінного доказу")))
     (new-foreign-tools .
       (((path . "tools/file-authority-guard.sh") (independence_status . foreign) (migration_plan . "міграція: переписати механічний Git-сканер у SENS, залишивши мінімальний host-виклик лише для отримання Git-дерева; після доведення рівності відмов вилучити shell"))
        ((path . "tools/file_guard.py") (independence_status . foreign) (migration_plan . "міграція: перенести рішення щодо нових файлів у виконувану фізичну програму SENS; залишити Git лише транспортом назв; підтвердити негативні свідки й тоді вилучити Python"))
        ((path . "tools/important_file_guard.py") (independence_status . foreign) (migration_plan . "міграція: переписати обробку статусів Git та файловий допуск як фізичний SENS-доказ; звірити незалежні негативні випадки; видалити Python після доказу паритету"))))
     (new-python-without-entry . blocked)
     (new-python-outside-tools . blocked)
     (oracle-parity-before-host-retirement . required)
     (new-tool-does-not-own-semantics . 1))))
