; #382 — перевірка обліку інструментів репозиторію мовою СЕНС.
; Політика та записи обліку належать самій мові Lisp.
; Цей сценарій перевіряє стан інструментів, але не визначає
; семантичних законів мови. Назви полів протоколу не перекладаємо.

(визначити інструменти-обов'язкові-поля
  (як-є (path kind language role lifecycle callers authority-source
               migration-issue replacement removal-condition)))

(визначити інструменти-допустимі-види
  (як-є (check generator migration benchmark deploy release helper other)))

(визначити інструменти-допустимі-мови
  (як-є (lisp python shell javascript powershell other)))

(визначити інструменти-допустимі-стани-життєвого-циклу
  (як-є (active transitional legacy generated-helper archive-candidate)))

(визначити інструменти-порушення
  (функція (kind detail)
    (список (як-є інструменти-порушення) kind detail)))

(визначити інструменти-поле-зі-списку
  (функція (name fields)
    (за-умовою
      ((атом? fields) () (як-є missing))
      ((атом? fields) (1) (як-є missing))
      ((атом? fields) (0)
       (нехай ((field (перше fields)))
         (за-умовою
           ((атом? field) ()
            (інструменти-поле-зі-списку name (решта fields)))
           ((атом? field) (1)
            (інструменти-поле-зі-списку name (решта fields)))
           ((атом? field) (0)
            (за-умовою
              ((тотожне? (перше field) name) (1) (друге field))
              ((тотожне? (перше field) name) (0)
               (інструменти-поле-зі-списку name (решта fields)))))))))))

(визначити інструменти-поле-запису
  (функція (name row)
    (за-умовою
      ((атом? row) () (як-є missing))
      ((атом? row) (1) (як-є missing))
      ((атом? row) (0)
       (інструменти-поле-зі-списку name (решта row))))))

(визначити інструменти-стан-правильного-вердикту
  (функція (verdict)
    (за-умовою
      ((однакові? verdict (список (як-є repo-tooling-ok)))
       (1)
       (як-є yes))
      ((однакові? verdict (список (як-є repo-tooling-ok)))
       (0)
       (як-є no)))))

(визначити інструменти-наявність-поля
  (функція (value)
    (за-умовою
      ((атом? value) () (як-є present))
      ((атом? value) (1)
       (за-умовою
         ((тотожне? value (як-є missing)) (1) (як-є missing))
         ((тотожне? value (як-є missing)) (0) (як-є present))))
      ((атом? value) (0) (як-є present)))))

(визначити інструменти-вердикт-обов'язкових-полів
  (функція (required row)
    (за-умовою
      ((атом? required) () (список (як-є repo-tooling-ok)))
      ((атом? required) (1)
       (інструменти-порушення (як-є malformed-required-field-list) required))
      ((атом? required) (0)
       (за-умовою
         ((тотожне? (інструменти-наявність-поля
                (інструменти-поле-запису (перше required) row))
              (як-є missing))
          (1)
          (інструменти-порушення (як-є missing-field) (перше required)))
         ((тотожне? (інструменти-наявність-поля
                (інструменти-поле-запису (перше required) row))
              (як-є missing))
          (0)
          (інструменти-вердикт-обов'язкових-полів (решта required) row)))))))

(визначити інструменти-вердикт-обов'язкових-полів-рядка
  (функція (row)
    (за-умовою
      ((атом? row) ()
       (інструменти-порушення (як-є malformed-row) row))
      ((атом? row) (1)
       (інструменти-порушення (як-є malformed-row) row))
      ((атом? row) (0)
       (за-умовою
         ((тотожне? (перше row) (як-є tool)) (1)
          (інструменти-вердикт-обов'язкових-полів інструменти-обов'язкові-поля row))
         ((тотожне? (перше row) (як-є tool)) (0)
          (інструменти-порушення (як-є malformed-row-kind) (перше row))))))))

(визначити інструменти-вердикт-обов'язкових-записів
  (функція (rows)
    (за-умовою
      ((атом? rows) () (список (як-є repo-tooling-ok)))
      ((атом? rows) (1)
       (інструменти-порушення (як-є malformed-inventory-list) rows))
      ((атом? rows) (0)
       (нехай ((row-verdict (інструменти-вердикт-обов'язкових-полів-рядка (перше rows))))
         (за-умовою
           ((тотожне? (інструменти-стан-правильного-вердикту row-verdict) (як-є yes))
            (1)
            (інструменти-вердикт-обов'язкових-записів (решта rows)))
           ((тотожне? (інструменти-стан-правильного-вердикту row-verdict) (як-є no))
            (1)
            row-verdict)))))))

(визначити інструменти-допуск-символу
  (функція (value admitted)
    (за-умовою
      ((атом? admitted) () (як-є rejected))
      ((атом? admitted) (1) (як-є malformed-admitted-set))
      ((атом? admitted) (0)
       (за-умовою
         ((тотожне? value (перше admitted)) (1) (як-є admitted))
         ((тотожне? value (перше admitted)) (0)
          (інструменти-допуск-символу value (решта admitted))))))))

(визначити інструменти-вердикт-значень-рядка
  (функція (row)
    (нехай-послідовно ((kind (інструменти-поле-запису (як-є kind) row))
           (language (інструменти-поле-запису (як-є language) row))
           (lifecycle (інструменти-поле-запису (як-є lifecycle) row))
           (kind-state (інструменти-допуск-символу kind інструменти-допустимі-види)))
      (за-умовою
        ((тотожне? kind-state (як-є admitted)) (1)
         (нехай ((language-state
                 (інструменти-допуск-символу language інструменти-допустимі-мови)))
           (за-умовою
             ((тотожне? language-state (як-є admitted)) (1)
              (нехай ((lifecycle-state
                      (інструменти-допуск-символу lifecycle інструменти-допустимі-стани-життєвого-циклу)))
                (за-умовою
                  ((тотожне? lifecycle-state (як-є admitted)) (1)
                   (список (як-є repo-tooling-ok)))
                  ((тотожне? lifecycle-state (як-є rejected)) (1)
                   (інструменти-порушення (як-є invalid-lifecycle) lifecycle))
                  ((тотожне? lifecycle-state (як-є malformed-admitted-set))
                   (1)
                   (інструменти-порушення
                     (як-є malformed-lifecycle-vocabulary)
                     lifecycle)))))
             ((тотожне? language-state (як-є rejected)) (1)
              (інструменти-порушення (як-є invalid-language) language))
             ((тотожне? language-state (як-є malformed-admitted-set))
              (1)
              (інструменти-порушення
                (як-є malformed-language-vocabulary)
                language)))))
        ((тотожне? kind-state (як-є rejected)) (1)
         (інструменти-порушення (як-є invalid-kind) kind))
        ((тотожне? kind-state (як-є malformed-admitted-set)) (1)
         (інструменти-порушення (як-є malformed-kind-vocabulary) kind))))))

(визначити інструменти-вердикт-допустимих-значень
  (функція (rows)
    (за-умовою
      ((атом? rows) () (список (як-є repo-tooling-ok)))
      ((атом? rows) (1)
       (інструменти-порушення (як-є malformed-inventory-list) rows))
      ((атом? rows) (0)
       (нехай ((row-verdict (інструменти-вердикт-значень-рядка (перше rows))))
         (за-умовою
           ((тотожне? (інструменти-стан-правильного-вердикту row-verdict) (як-є yes))
            (1)
            (інструменти-вердикт-допустимих-значень (решта rows)))
           ((тотожне? (інструменти-стан-правильного-вердикту row-verdict) (як-є no))
            (1)
            row-verdict)))))))

(визначити інструменти-стан-потреби-міграції-пайтона
  (функція (row)
    (нехай ((language (інструменти-поле-запису (як-є language) row))
          (lifecycle (інструменти-поле-запису (як-є lifecycle) row)))
      (за-умовою
        ((тотожне? language (як-є python)) (1)
         (за-умовою
           ((тотожне? lifecycle (як-є active)) (1) (як-є required))
           ((тотожне? lifecycle (як-є active)) (0)
            (за-умовою
              ((тотожне? lifecycle (як-є transitional))
               (1)
               (як-є required))
              ((тотожне? lifecycle (як-є transitional))
               (0)
               (як-є not-required))))))
        ((тотожне? language (як-є python)) (0)
         (як-є not-required))))))

(визначити інструменти-стан-власника-міграції
  (функція (owner)
    (за-умовою
      ((атом? owner) () (як-є missing))
      ((атом? owner) (1)
       (за-умовою
         ((тотожне? owner (як-є missing)) (1) (як-є missing))
         ((тотожне? owner (як-є missing)) (0) (як-є present))))
      ((атом? owner) (0) (як-є present)))))

(визначити інструменти-вердикт-міграції-пайтона-для-рядка
  (функція (row)
    (нехай ((required-state (інструменти-стан-потреби-міграції-пайтона row)))
      (за-умовою
        ((тотожне? required-state (як-є not-required)) (1)
         (список (як-є repo-tooling-ok)))
        ((тотожне? required-state (як-є required)) (1)
         (нехай-послідовно ((owner (інструменти-поле-запису (як-є migration-issue) row))
                (owner-state (інструменти-стан-власника-міграції owner)))
           (за-умовою
             ((тотожне? owner-state (як-є present)) (1)
              (список (як-є repo-tooling-ok)))
             ((тотожне? owner-state (як-є missing)) (1)
              (інструменти-порушення
                (як-є python-migration-unowned)
                (інструменти-поле-запису (як-є path) row))))))))))

(визначити інструменти-вердикт-міграції-пайтона
  (функція (rows)
    (за-умовою
      ((атом? rows) () (список (як-є repo-tooling-ok)))
      ((атом? rows) (1)
       (інструменти-порушення (як-є malformed-inventory-list) rows))
      ((атом? rows) (0)
       (нехай ((row-verdict (інструменти-вердикт-міграції-пайтона-для-рядка (перше rows))))
         (за-умовою
           ((тотожне? (інструменти-стан-правильного-вердикту row-verdict) (як-є yes))
            (1)
            (інструменти-вердикт-міграції-пайтона (решта rows)))
           ((тотожне? (інструменти-стан-правильного-вердикту row-verdict) (як-є no))
            (1)
            row-verdict)))))))

(визначити інструменти-знайти-рядок-за-шляхом
  (функція (path rows)
    (за-умовою
      ((атом? rows) () (як-є ()))
      ((атом? rows) (1) (як-є ()))
      ((атом? rows) (0)
       (нехай ((row (перше rows)))
         (за-умовою
           ((однакові? path (інструменти-поле-запису (як-є path) row))
            (1)
            row)
           ((однакові? path (інструменти-поле-запису (як-є path) row))
            (0)
            (інструменти-знайти-рядок-за-шляхом path (решта rows)))))))))

(визначити інструменти-вердикт-повторних-шляхів
  (функція (rows)
    (за-умовою
      ((атом? rows) () (список (як-є repo-tooling-ok)))
      ((атом? rows) (1)
       (інструменти-порушення (як-є malformed-inventory-list) rows))
      ((атом? rows) (0)
       (нехай-послідовно ((row (перше rows))
              (path (інструменти-поле-запису (як-є path) row))
              (found (інструменти-знайти-рядок-за-шляхом path (решта rows))))
         (за-умовою
           ((атом? found) ()
            (інструменти-вердикт-повторних-шляхів (решта rows)))
           ((атом? found) (1)
            (інструменти-порушення (як-є malformed-row) path))
           ((атом? found) (0)
            (інструменти-порушення (як-є duplicate-path) path))))))))

(визначити інструменти-стан-наявності-шляху
  (функція (path observed)
    (за-умовою
      ((атом? observed) () (як-є absent))
      ((атом? observed) (1) (як-є malformed))
      ((атом? observed) (0)
       (нехай ((observed-path (рядок-додати "scripts/" (перше observed))))
         (за-умовою
           ((однакові? path observed-path) (як-є present))
           (так
            (інструменти-стан-наявності-шляху path (решта observed)))))))))

(визначити інструменти-вердикт-застарілого-шляху
  (функція (rows observed)
    (за-умовою
      ((атом? rows) () (список (як-є repo-tooling-ok)))
      ((атом? rows) (1)
       (інструменти-порушення (як-є malformed-inventory-list) rows))
      ((атом? rows) (0)
       (нехай-послідовно ((row (перше rows))
              (path (інструменти-поле-запису (як-є path) row))
              (state (інструменти-стан-наявності-шляху path observed)))
         (за-умовою
           ((тотожне? state (як-є present)) (1)
            (інструменти-вердикт-застарілого-шляху (решта rows) observed))
           ((тотожне? state (як-є absent)) (1)
            (інструменти-порушення (як-є stale-path) path))
           ((тотожне? state (як-є malformed)) (1)
            (інструменти-порушення (як-є malformed-observed-list) observed))))))))

(визначити інструменти-вердикт-покриття-спостережень
  (функція (rows observed)
    (за-умовою
      ((атом? observed) () (список (як-є repo-tooling-ok)))
      ((атом? observed) (1)
       (інструменти-порушення (як-є malformed-observed-list) observed))
      ((атом? observed) (0)
       (нехай-послідовно ((name (перше observed))
              (path (рядок-додати "scripts/" name))
              (found (інструменти-знайти-рядок-за-шляхом path rows)))
         (за-умовою
           ((атом? found) ()
            (інструменти-порушення (як-є unregistered-tool) path))
           ((атом? found) (1)
            (інструменти-порушення (як-є malformed-row) path))
           ((атом? found) (0)
            (інструменти-вердикт-покриття-спостережень rows (решта observed)))))))))

(визначити інструменти-вердикт-після-обов'язкової-перевірки
  (функція (rows observed)
    (нехай ((enum-verdict (інструменти-вердикт-допустимих-значень rows)))
      (за-умовою
        ((тотожне? (інструменти-стан-правильного-вердикту enum-verdict) (як-є yes))
         (1)
         (нехай ((migration-verdict (інструменти-вердикт-міграції-пайтона rows)))
           (за-умовою
             ((тотожне? (інструменти-стан-правильного-вердикту migration-verdict) (як-є yes))
              (1)
              (нехай ((duplicate-verdict (інструменти-вердикт-повторних-шляхів rows)))
                (за-умовою
                  ((тотожне? (інструменти-стан-правильного-вердикту duplicate-verdict) (як-є yes))
                   (1)
                   (нехай ((stale-verdict (інструменти-вердикт-застарілого-шляху rows observed)))
                     (за-умовою
                       ((тотожне? (інструменти-стан-правильного-вердикту stale-verdict) (як-є yes))
                        (1)
                        (інструменти-вердикт-покриття-спостережень rows observed))
                       ((тотожне? (інструменти-стан-правильного-вердикту stale-verdict) (як-є no))
                        (1)
                        stale-verdict))))
                  ((тотожне? (інструменти-стан-правильного-вердикту duplicate-verdict) (як-є no))
                   (1)
                   duplicate-verdict))))
             ((тотожне? (інструменти-стан-правильного-вердикту migration-verdict) (як-є no))
              (1)
              migration-verdict))))
        ((тотожне? (інструменти-стан-правильного-вердикту enum-verdict) (як-є no))
         (1)
         enum-verdict)))))

(визначити інструменти-загальний-вердикт
  (функція (rows observed)
    (нехай ((required-verdict (інструменти-вердикт-обов'язкових-записів rows)))
      (за-умовою
        ((тотожне? (інструменти-стан-правильного-вердикту required-verdict) (як-є yes))
         (1)
         (інструменти-вердикт-після-обов'язкової-перевірки rows observed))
        ((тотожне? (інструменти-стан-правильного-вердикту required-verdict) (як-є no))
         (1)
         required-verdict)))))

; ----- pure negative witnesses -----

(визначити інструменти-приклад-рядка-а
  (як-є
    (tool
      (path "scripts/a.lisp")
      (kind check)
      (language lisp)
      (role sample)
      (lifecycle active)
      (callers ())
      (authority-source (issue 382))
      (migration-issue ())
      (replacement ())
      (removal-condition ()))))

(визначити інструменти-приклад-рядка-в
  (як-є
    (tool
      (path "scripts/c.lisp")
      (kind helper)
      (language lisp)
      (role stale-sample)
      (lifecycle active)
      (callers ())
      (authority-source (issue 382))
      (migration-issue ())
      (replacement ())
      (removal-condition ()))))

(визначити інструменти-приклад-хибного-виду
  (як-є
    (tool
      (path "scripts/a.lisp")
      (kind mystery-kind)
      (language lisp)
      (role sample)
      (lifecycle active)
      (callers ())
      (authority-source (issue 382))
      (migration-issue ())
      (replacement ())
      (removal-condition ()))))

(визначити інструменти-приклад-хибної-мови
  (як-є
    (tool
      (path "scripts/a.lisp")
      (kind check)
      (language mystery-language)
      (role sample)
      (lifecycle active)
      (callers ())
      (authority-source (issue 382))
      (migration-issue ())
      (replacement ())
      (removal-condition ()))))

(визначити інструменти-приклад-хибного-стану
  (як-є
    (tool
      (path "scripts/a.lisp")
      (kind check)
      (language lisp)
      (role sample)
      (lifecycle parity-green)
      (callers ())
      (authority-source (issue 382))
      (migration-issue ())
      (replacement ())
      (removal-condition ()))))

(визначити інструменти-приклад-пайтона-без-власника
  (як-є
    (tool
      (path "scripts/a.py")
      (kind check)
      (language python)
      (role python-without-migration-owner)
      (lifecycle transitional)
      (callers ())
      (authority-source (issue 382))
      (migration-issue ())
      (replacement ())
      (removal-condition migration-issue-complete-and-callers-switched))))

(визначити інструменти-приклад-відсутньої-ролі
  (як-є
    (tool
      (path "scripts/a.lisp")
      (kind check)
      (language lisp)
      (lifecycle active)
      (callers ())
      (authority-source (issue 382))
      (migration-issue ())
      (replacement ())
      (removal-condition ()))))

(визначити інструменти-підтвердити-вердикт
  (функція (actual expected)
    (за-умовою
      ((однакові? actual expected)
       (список (як-є repo-tooling-selftest-ok)))
      (так
       (нехай ((shown
               (друкувати
                 (список
                   (як-є repo-tooling-selftest-failed)
                   actual
                   expected))))
         (перше (як-є ())))))))

(інструменти-підтвердити-вердикт
  (інструменти-загальний-вердикт (список інструменти-приклад-рядка-а) (як-є ("a.lisp" "b.lisp")))
  (як-є (інструменти-порушення unregistered-tool "scripts/b.lisp")))

(інструменти-підтвердити-вердикт
  (інструменти-загальний-вердикт
    (список інструменти-приклад-рядка-а інструменти-приклад-рядка-а)
    (як-є ("a.lisp")))
  (як-є (інструменти-порушення duplicate-path "scripts/a.lisp")))

(інструменти-підтвердити-вердикт
  (інструменти-загальний-вердикт
    (список інструменти-приклад-рядка-а інструменти-приклад-рядка-в)
    (як-є ("a.lisp")))
  (як-є (інструменти-порушення stale-path "scripts/c.lisp")))

(інструменти-підтвердити-вердикт
  (інструменти-загальний-вердикт (список інструменти-приклад-хибного-виду) (як-є ("a.lisp")))
  (як-є (інструменти-порушення invalid-kind mystery-kind)))

(інструменти-підтвердити-вердикт
  (інструменти-загальний-вердикт (список інструменти-приклад-хибної-мови) (як-є ("a.lisp")))
  (як-є (інструменти-порушення invalid-language mystery-language)))

(інструменти-підтвердити-вердикт
  (інструменти-загальний-вердикт (список інструменти-приклад-хибного-стану) (як-є ("a.lisp")))
  (як-є (інструменти-порушення invalid-lifecycle parity-green)))

(інструменти-підтвердити-вердикт
  (інструменти-загальний-вердикт (список інструменти-приклад-пайтона-без-власника) (як-є ("a.py")))
  (як-є (інструменти-порушення python-migration-unowned "scripts/a.py")))

(інструменти-підтвердити-вердикт
  (інструменти-загальний-вердикт (список інструменти-приклад-відсутньої-ролі) (як-є ("a.lisp")))
  (як-є (інструменти-порушення missing-field role)))

; ----- real repository observation -----

(визначити інструменти-рядки-обліку
  (функція (forms)
    (за-умовою
      ((атом? forms) () (як-є ()))
      ((атом? forms) (1) (як-є ()))
      ((атом? forms) (0)
       (нехай ((form (перше forms)))
         (за-умовою
           ((атом? form) ()
            (інструменти-рядки-обліку (решта forms)))
           ((атом? form) (1)
            (інструменти-рядки-обліку (решта forms)))
           ((атом? form) (0)
            (за-умовою
              ((тотожне? (перше form) (як-є tool)) (1)
               (сполучити form (інструменти-рядки-обліку (решта forms))))
              ((тотожне? (перше form) (як-є tool)) (0)
               (інструменти-рядки-обліку (решта forms)))))))))))

(визначити інструменти-спостережувані-сценарії
  (функція (entries)
    (за-умовою
      ((атом? entries) () (як-є ()))
      ((атом? entries) (1) (як-є ()))
      ((атом? entries) (0)
       (нехай ((name (перше entries)))
         (за-умовою
           ((однакові? name "tests")
            (інструменти-спостережувані-сценарії (решта entries)))
           (так
            (сполучити name (інструменти-спостережувані-сценарії (решта entries))))))))))

(визначити інструменти-чинні-форми
  (читати-всі (читати-файл "knowledge/repo-tooling-inventory.lisp")))

(визначити інструменти-чинні-рядки
  (інструменти-рядки-обліку інструменти-чинні-форми))

(визначити інструменти-чинні-спостереження
  (інструменти-спостережувані-сценарії (read-dir "scripts")))

(визначити інструменти-чинний-вердикт
  (інструменти-загальний-вердикт інструменти-чинні-рядки інструменти-чинні-спостереження))

(друкувати інструменти-чинний-вердикт)

(інструменти-підтвердити-вердикт
  інструменти-чинний-вердикт
  (як-є (repo-tooling-ok)))
