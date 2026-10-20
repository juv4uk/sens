; Файлова гвардія SENS. Вердикт допуска — лише виконуваний мовний код.
; Вхідні шляхи недовірені: це дані Git, а не джерело політики.

(визначити файлова-гвардія-поле
  (функція (key rows)
    (за-умовою
      ((атом? rows) (structural-kind empty-list) ())
      ((атом? rows) (structural-kind pair)
        (за-умовою
          ((тотожне? key (перше (перше rows))) (решта (перше rows)))
          (так (файлова-гвардія-поле key (решта rows)))))
      ((атом? rows) (structural-kind atom) ()))))

(визначити файлова-гвардія-заперечення
  (функція (bit)
    (за-умовою
      ((однакові? bit 1) 0)
      (так 1))))

(визначити файлова-гвардія-має-поле?
  (функція (key rows)
    (файлова-гвардія-заперечення (однакові? (знайти-за-ключем key rows) (як-є ())))))

(визначити файлова-гвардія-список-рядків?
  (функція (values)
    (за-умовою
      ((атом? values) (structural-kind empty-list) 1)
      ((атом? values) (structural-kind pair)
        (та (рядок? (перше values)) (файлова-гвардія-список-рядків? (решта values))))
      ((атом? values) (structural-kind atom) 0))))

(визначити файлова-гвардія-має-суфікс?
  (функція (text suffix)
    (за-умовою
      ((рядок-порожній? suffix) 1)
      ((рядок-порожній? text) 0)
      ((менше? (рядок-довжина text) (рядок-довжина suffix)) 0)
      ((однакові? (рядок-довжина text) (рядок-довжина suffix))
        (однакові? text suffix))
      (так (файлова-гвардія-має-суфікс? (рядок-решта text) suffix)))))

(визначити файлова-гвардія-канонічний-шлях?
  (функція (path)
    (та
      (рядок? path)
      (файлова-гвардія-заперечення (рядок-порожній? path))
      (файлова-гвардія-заперечення (рядок-префікс? "/" path))
      (файлова-гвардія-заперечення (рядок-містить? "\\" path))
      (файлова-гвардія-заперечення (рядок-містить? "//" path))
      (файлова-гвардія-заперечення (рядок-містить? "/../" path))
      (файлова-гвардія-заперечення (рядок-префікс? "../" path))
      (файлова-гвардія-заперечення (рядок-містить? "/./" path))
      (файлова-гвардія-заперечення (рядок-префікс? "./" path))
      (файлова-гвардія-заперечення (файлова-гвардія-має-суфікс? path "/.."))
      (файлова-гвардія-заперечення (файлова-гвардія-має-суфікс? path "/."))
      (файлова-гвардія-заперечення (однакові? path "."))
      (файлова-гвардія-заперечення (однакові? path "..")))))

(визначити файлова-гвардія-перелік-шляхів?
  (функція (paths)
    (за-умовою
      ((атом? paths) (structural-kind empty-list) 1)
      ((атом? paths) (structural-kind pair)
        (та
          (файлова-гвардія-канонічний-шлях? (перше paths))
          (файлова-гвардія-перелік-шляхів? (решта paths))))
      ((атом? paths) (structural-kind atom) 0))))

(визначити файлова-гвардія-перелік-шляхів-інструментів?
  (функція (paths)
    (за-умовою
      ((атом? paths) (structural-kind empty-list) 1)
      ((атом? paths) (structural-kind pair)
        (та
          (рядок-префікс? "tools/" (перше paths))
          (файлова-гвардія-перелік-шляхів-інструментів? (решта paths))))
      ((атом? paths) (structural-kind atom) 0))))

(визначити файлова-гвардія-кількість
  (функція (needle values)
    (за-умовою
      ((атом? values) (structural-kind empty-list) 0)
      ((атом? values) (structural-kind pair)
        (додати
          (за-умовою ((однакові? needle (перше values)) 1) (так 0))
          (файлова-гвардія-кількість needle (решта values))))
      ((атом? values) (structural-kind atom) 0))))

(визначити файлова-гвардія-кількість-режимів
  (функція (path modes)
    (за-умовою
      ((атом? modes) (structural-kind empty-list) 0)
      ((атом? modes) (structural-kind pair)
        (додати
          (за-умовою ((однакові? path (перше (перше modes))) 1) (так 0))
          (файлова-гвардія-кількість-режимів path (решта modes))))
      ((атом? modes) (structural-kind atom) 0))))

(визначити файлова-гвардія-знайти-режим
  (функція (path modes)
    (за-умовою
      ((атом? modes) (structural-kind empty-list) ())
      ((атом? modes) (structural-kind pair)
        (за-умовою
          ((однакові? path (перше (перше modes))) (решта (перше modes)))
          (так (файлова-гвардія-знайти-режим path (решта modes)))))
      ((атом? modes) (structural-kind atom) ()))))

(визначити файлова-гвардія-рядки-режимів-коректні?
  (функція (modes paths)
    (за-умовою
      ((атом? modes) (structural-kind empty-list) 1)
      ((атом? modes) (structural-kind pair)
        (та
          (рядок? (перше (перше modes)))
          (рядок? (решта (перше modes)))
          (однакові? (файлова-гвардія-кількість (перше (перше modes)) paths) 1)
          (однакові? (файлова-гвардія-кількість-режимів (перше (перше modes)) modes) 1)
          (файлова-гвардія-рядки-режимів-коректні? (решта modes) paths)))
      ((атом? modes) (structural-kind atom) 0))))

(визначити файлова-гвардія-шляхи-мають-режим?
  (функція (paths modes)
    (за-умовою
      ((атом? paths) (structural-kind empty-list) 1)
      ((атом? paths) (structural-kind pair)
        (та
          (однакові? (файлова-гвардія-кількість-режимів (перше paths) modes) 1)
          (файлова-гвардія-шляхи-мають-режим? (решта paths) modes)))
      ((атом? paths) (structural-kind atom) 0))))

(визначити файлова-гвардія-режим-обовязковий?
  (функція (path)
    (або
      (рядок-префікс? "lib/" path)
      (рядок-префікс? "knowledge/" path)
      (рядок-префікс? "witnesses/" path)
      (та
        (рядок-префікс? "tools/" path)
        (файлова-гвардія-має-суфікс? path ".py")))))

(визначити файлова-гвардія-режим-допущений?
  (функція (path modes)
    (та
      (однакові? (файлова-гвардія-кількість-режимів path modes) 1)
      (або
        (однакові? (файлова-гвардія-знайти-режим path modes) "100644:blob")
        (однакові? (файлова-гвардія-знайти-режим path modes) "100755:blob")))))

; Existing paths with Git T status are not new paths.  Keep them out of
; extension admission and apply only the existing regular-blob invariant.
(визначити файлова-гвардія-перевірити-зміну-типу
  (функція (paths modes)
    (за-умовою
      ((атом? paths) (structural-kind empty-list) 1)
      ((атом? paths) (structural-kind pair)
        (нехай ((path (перше paths)))
          (за-умовою
            ((та (файлова-гвардія-режим-обовязковий? path) (файлова-гвардія-заперечення (файлова-гвардія-режим-допущений? path modes)))
              (файлова-гвардія-заборонити (як-є git-mode) (список path (файлова-гвардія-знайти-режим path modes))))
            (так (файлова-гвардія-перевірити-зміну-типу (решта paths) modes)))))
      ((атом? paths) (structural-kind atom)
        (файлова-гвардія-заборонити (як-є input) "typechanged-paths is not a proper list")))))

(визначити файлова-гвардія-шлях-рядка
  (функція (row)
    (файлова-гвардія-поле (як-є path) row)))

(визначити файлова-гвардія-кількість-рядків
  (функція (path rows)
    (за-умовою
      ((атом? rows) (structural-kind empty-list) 0)
      ((атом? rows) (structural-kind pair)
        (додати
          (за-умовою ((однакові? path (файлова-гвардія-шлях-рядка (перше rows))) 1) (так 0))
          (файлова-гвардія-кількість-рядків path (решта rows))))
      ((атом? rows) (structural-kind atom) 0))))

(визначити файлова-гвардія-знайти-рядок
  (функція (path rows)
    (за-умовою
      ((атом? rows) (structural-kind empty-list) ())
      ((атом? rows) (structural-kind pair)
        (за-умовою
          ((однакові? path (файлова-гвардія-шлях-рядка (перше rows))) (перше rows))
          (так (файлова-гвардія-знайти-рядок path (решта rows)))))
      ((атом? rows) (structural-kind atom) ()))))

(визначити файлова-гвардія-рядок-коректний?
  (функція (row)
    (нехай ((path (файлова-гвардія-поле (як-є path) row)))
      (нехай ((issue (файлова-гвардія-поле (як-є owner-issue) row)))
        (нехай ((plan (файлова-гвардія-поле (як-є migration_plan) row)))
          (та
            (файлова-гвардія-має-поле? (як-є path) row)
            (файлова-гвардія-має-поле? (як-є independence_status) row)
            (файлова-гвардія-має-поле? (як-є owner-issue) row)
            (файлова-гвардія-має-поле? (як-є migration_plan) row)
            (файлова-гвардія-канонічний-шлях? path)
            (рядок-префікс? "tools/" path)
            (файлова-гвардія-має-суфікс? path ".py")
            (однакові? (файлова-гвардія-поле (як-є independence_status) row) (як-є foreign))
            (рядок? issue)
            (рядок-префікс? "#" issue)
            (більше? (рядок-довжина issue) 1)
            (рядок? plan)
            (більше? (рядок-довжина plan) 40)
            (рядок-містить? "SENS" plan)
            (рядок-містить? "T5" plan)))))))

(визначити файлова-гвардія-сторонній-шлях?
  (функція (path rows)
    (та
      (однакові? (файлова-гвардія-кількість-рядків path rows) 1)
      (файлова-гвардія-рядок-коректний? (файлова-гвардія-знайти-рядок path rows)))))

(визначити файлова-гвардія-рядки-коректні?
  (функція (rows tracked)
    (за-умовою
      ((атом? rows) (structural-kind empty-list) 1)
      ((атом? rows) (structural-kind pair)
        (та
          (файлова-гвардія-рядок-коректний? (перше rows))
          (однакові? (файлова-гвардія-кількість-рядків (файлова-гвардія-шлях-рядка (перше rows)) rows) 1)
          (однакові? (файлова-гвардія-кількість (файлова-гвардія-шлях-рядка (перше rows)) tracked) 1)
          (файлова-гвардія-рядки-коректні? (решта rows) tracked)))
      ((атом? rows) (structural-kind atom) 0))))

(визначити файлова-гвардія-облік-охоплює-відстежувані?
  (функція (tracked rows)
    (за-умовою
      ((атом? tracked) (structural-kind empty-list) 1)
      ((атом? tracked) (structural-kind pair)
        (за-умовою
          ((файлова-гвардія-має-суфікс? (перше tracked) ".py")
            (та
              (файлова-гвардія-сторонній-шлях? (перше tracked) rows)
              (файлова-гвардія-облік-охоплює-відстежувані? (решта tracked) rows)))
          (так (файлова-гвардія-облік-охоплює-відстежувані? (решта tracked) rows))))
      ((атом? tracked) (structural-kind atom) 0))))

(визначити файлова-гвардія-політика-коректна?
  (функція (policy)
    (та
      (однакові? (файлова-гвардія-поле (як-є schema) policy) (як-є file-authority-policy/1))
      (однакові? (файлова-гвардія-поле (як-є status) policy) (як-є owner-directed))
      (однакові? (файлова-гвардія-поле (як-є activation-git-commit) policy)
              "9c94727eb1c45378f3debccf633aad2366e13599")
      (однакові? (файлова-гвардія-поле (як-є governing-domains) policy)
              (як-є (D1 D2 D3 D4 D5 D6 D7 D8 D9)))
      (однакові? (файлова-гвардія-поле (як-є important-roots) policy)
              (як-є ("lib/" "knowledge/" "witnesses/")))
      (однакові? (файлова-гвардія-поле (як-є new-important-extensions) policy)
              (як-є (".lisp" ".sens")))
      (однакові? (файлова-гвардія-поле (як-є physical-sens) policy) (як-є packed-T5-only))
      (однакові? (файлова-гвардія-поле (як-є new-python-root) policy) "tools/")
      (однакові? (файлова-гвардія-поле (як-є new-python-independence-status) policy) (як-є foreign))
      (однакові? (файлова-гвардія-поле (як-є foreign-census) policy)
              "knowledge/foreign-tools-census.lisp")
      (однакові? (файлова-гвардія-поле (як-є file-guard) policy)
              "knowledge/file-authority-guard.lisp")
      (однакові? (файлова-гвардія-поле (як-є baseline-existing-paths) policy)
              (як-є grandfathered-migration-debt))
      (однакові? (файлова-гвардія-поле (як-є baseline-important-noncanonical-count) policy) 261)
      (однакові? (файлова-гвардія-поле (як-є baseline-python-count) policy) 741)
      (однакові? (файлова-гвардія-поле (як-є scope) policy) (як-є added-paths-in-Git-tree))
      (однакові? (файлова-гвардія-поле (як-є rename-or-copy) policy)
              (як-є treat-new-path-as-added))
      (однакові? (файлова-гвардія-поле (як-є failure) policy) (як-є fail-closed))
      (однакові? (файлова-гвардія-поле (як-є semantic-admission-from-extension) policy) (як-є ()))
      (однакові? (файлова-гвардія-поле (як-є semantic-admission-from-host-guard) policy) (як-є ())))))

(визначити файлова-гвардія-облік-коректний?
  (функція (census tracked)
    (нехай ((rows (файлова-гвардія-поле (як-є new-foreign-tools) census)))
      (та
        (однакові? (файлова-гвардія-поле (як-є schema) census) (як-є foreign-tools-census/1))
        (однакові? (файлова-гвардія-поле (як-є status) census) (як-є staged-migration))
        (однакові? (файлова-гвардія-поле (як-є authority) census)
                "knowledge/file-authority-policy.lisp")
        (однакові? (файлова-гвардія-поле (як-є per-file-census) census)
                "knowledge/foreign-tools-census.lisp")
        (однакові? (файлова-гвардія-поле (як-є new-python-without-entry) census) (як-є blocked))
        (однакові? (файлова-гвардія-поле (як-є new-python-outside-tools) census) (як-є blocked))
        (однакові? (файлова-гвардія-поле (як-є oracle-parity-before-host-retirement) census)
                (як-є required))
        (однакові? (файлова-гвардія-поле (як-є new-tool-does-not-own-semantics) census) 1)
        (файлова-гвардія-рядки-коректні? rows tracked)
        (файлова-гвардія-облік-охоплює-відстежувані? tracked rows)))))

(визначити файлова-гвардія-класифікувати
  (функція (path policy rows)
    (за-умовою
      ((файлова-гвардія-заперечення (файлова-гвардія-канонічний-шлях? path)) (як-є blocked-noncanonical-path))
      ((рядок-префікс? "lib/" path)
        (за-умовою
          ((або (файлова-гвардія-має-суфікс? path ".lisp") (файлова-гвардія-має-суфікс? path ".sens")) (як-є allowed))
          (так (як-є blocked-important-extension))))
      ((рядок-префікс? "knowledge/" path)
        (за-умовою
          ((або (файлова-гвардія-має-суфікс? path ".lisp") (файлова-гвардія-має-суфікс? path ".sens")) (як-є allowed))
          (так (як-є blocked-important-extension))))
      ((рядок-префікс? "witnesses/" path)
        (за-умовою
          ((або (файлова-гвардія-має-суфікс? path ".lisp") (файлова-гвардія-має-суфікс? path ".sens")) (як-є allowed))
          (так (як-є blocked-important-extension))))
      ((файлова-гвардія-має-суфікс? path ".py")
        (за-умовою
          ((рядок-префікс? "tools/" path)
            (за-умовою
              ((файлова-гвардія-сторонній-шлях? path rows) (як-є allowed))
              (так (як-є blocked-foreign-census))))
          (так (як-є blocked-python-outside-tools))))
      ((або
         (та (рядок-префікс? "tools/" path) (файлова-гвардія-має-суфікс? path ".sh"))
         (та (рядок-префікс? "scripts/" path) (файлова-гвардія-має-суфікс? path ".sh")))
        (як-є blocked-new-shell-tool))
      (так (як-є allowed)))))

(визначити файлова-гвардія-перевірити-додані
  (функція (paths policy rows modes)
    (за-умовою
      ((атом? paths) (structural-kind empty-list) 1)
      ((атом? paths) (structural-kind pair)
        (нехай ((path (перше paths)))
          (за-умовою
            ((та (файлова-гвардія-режим-обовязковий? path) (файлова-гвардія-заперечення (файлова-гвардія-режим-допущений? path modes)))
              (файлова-гвардія-заборонити (як-є git-mode) (список path (файлова-гвардія-знайти-режим path modes))))
            (так
              (нехай ((verdict (файлова-гвардія-класифікувати path policy rows)))
                (за-умовою
                  ((однакові? verdict (як-є allowed))
                    (файлова-гвардія-перевірити-додані (решта paths) policy rows modes))
                  (так (файлова-гвардія-заборонити (як-є path) (список path verdict)))))))))
      ((атом? paths) (structural-kind atom)
        (файлова-гвардія-заборонити (як-є input) "added-paths is not a proper list")))))

(визначити файлова-гвардія-перевірити-відстежувані
  (функція (paths rows)
    (за-умовою
      ((атом? paths) (structural-kind empty-list) 1)
      ((атом? paths) (structural-kind pair)
        (нехай ((path (перше paths)))
          (за-умовою
            ((файлова-гвардія-заперечення (файлова-гвардія-канонічний-шлях? path))
              (файлова-гвардія-заборонити (як-є input-path) path))
            ((файлова-гвардія-заперечення (рядок-префікс? "tools/" path))
              (файлова-гвардія-заборонити (як-є tracked-tools-path) path))
            (так (файлова-гвардія-перевірити-відстежувані (решта paths) rows)))))
      ((атом? paths) (structural-kind atom)
        (файлова-гвардія-заборонити (як-є input) "tracked-tools-paths is not a proper list")))))

(визначити файлова-гвардія-перевірити-рівність
  (функція (label actual expected)
    (за-умовою
      ((однакові? actual expected) 1)
      (так (файлова-гвардія-заборонити (як-є self-test) label)))))

(визначити файлова-гвардія-приклад-правильний
  (як-є
    (((path . "tools/fixture.py")
      (independence_status . foreign)
      (owner-issue . "#5397")
      (migration_plan . "Move file policy into executable SENS T5; keep Git facts as untrusted transport and prove hosted positive and negative parity before retiring Python.")))))

(визначити файлова-гвардія-приклад-помилковий-стан
  (як-є
    (((path . "tools/fixture.py")
      (independence_status . local)
      (owner-issue . "#5397")
      (migration_plan . "Move file policy into executable SENS T5; keep Git facts as untrusted transport and prove hosted positive and negative parity before retiring Python.")))))

(визначити файлова-гвардія-самоперевірка
  (функція (real-rows)
    (та
      (файлова-гвардія-перевірити-рівність "native lisp" (файлова-гвардія-класифікувати "lib/native.lisp" *file-authority-policy* real-rows) (як-є allowed))
      (файлова-гвардія-перевірити-рівність "native physical SENS" (файлова-гвардія-класифікувати "lib/native.sens" *file-authority-policy* real-rows) (як-є allowed))
      (файлова-гвардія-перевірити-рівність "new JSON is blocked" (файлова-гвардія-класифікувати "knowledge/new.json" *file-authority-policy* real-rows) (як-є blocked-important-extension))
      (файлова-гвардія-перевірити-рівність "FASL is not native source" (файлова-гвардія-класифікувати "lib/legacy.lisp.fasl" *file-authority-policy* real-rows) (як-є blocked-important-extension))
      (файлова-гвардія-перевірити-рівність "witness extension is blocked" (файлова-гвардія-класифікувати "witnesses/new.rs" *file-authority-policy* real-rows) (як-є blocked-important-extension))
      (файлова-гвардія-перевірити-рівність "Python outside tools is blocked" (файлова-гвардія-класифікувати "scripts/new.py" *file-authority-policy* real-rows) (як-є blocked-python-outside-tools))
      (файлова-гвардія-перевірити-рівність "unregistered Python is blocked" (файлова-гвардія-класифікувати "tools/unlisted.py" *file-authority-policy* real-rows) (як-є blocked-foreign-census))
      (файлова-гвардія-перевірити-рівність "registered Python is admitted" (файлова-гвардія-класифікувати "tools/fixture.py" *file-authority-policy* файлова-гвардія-приклад-правильний) (як-є allowed))
      (файлова-гвардія-перевірити-рівність "non-foreign census is blocked" (файлова-гвардія-класифікувати "tools/fixture.py" *file-authority-policy* файлова-гвардія-приклад-помилковий-стан) (як-є blocked-foreign-census))
      (файлова-гвардія-перевірити-рівність "duplicate census row is blocked"
        (файлова-гвардія-класифікувати "tools/fixture.py" *file-authority-policy* (append файлова-гвардія-приклад-правильний файлова-гвардія-приклад-правильний))
        (як-є blocked-foreign-census))
      (файлова-гвардія-перевірити-рівність "regular Git blob is admitted"
        (файлова-гвардія-режим-допущений? "lib/example.sens" (як-є (("lib/example.sens" . "100644:blob")))) 1)
      (файлова-гвардія-перевірити-рівність "symlink disguised as SENS is blocked"
        (файлова-гвардія-режим-допущений? "lib/example.sens" (як-є (("lib/example.sens" . "120000:blob")))) 0)
      (файлова-гвардія-перевірити-рівність "gitlink disguised as SENS is blocked"
        (файлова-гвардія-режим-допущений? "lib/example.sens" (як-є (("lib/example.sens" . "160000:commit")))) 0)
      (файлова-гвардія-перевірити-рівність "missing Git mode is blocked"
        (файлова-гвардія-режим-допущений? "lib/example.sens" (як-є ())) 0)
      (файлова-гвардія-перевірити-рівність "new shell tooling is blocked" (файлова-гвардія-класифікувати "tools/new.sh" *file-authority-policy* real-rows) (як-є blocked-new-shell-tool))
      (файлова-гвардія-перевірити-рівність "ordinary docs data is outside this policy" (файлова-гвардія-класифікувати "docs/research.json" *file-authority-policy* real-rows) (як-є allowed))
      (файлова-гвардія-перевірити-рівність "missing policy is invalid" (файлова-гвардія-політика-коректна? (як-є ())) 0)
      (файлова-гвардія-перевірити-рівність "missing census is invalid" (файлова-гвардія-облік-коректний? (як-є ()) (як-є ("tools/fixture.py"))) 0))))

(визначити файлова-гвардія-заборонити
  (функція (kind subject)
    (за-умовою
      ((однакові? kind (як-є policy)) (sens_file_authority_fail_policy_5397 subject))
      ((однакові? kind (як-є census)) (sens_file_authority_fail_census_5397 subject))
      ((однакові? kind (як-є input)) (sens_file_authority_fail_input_5397 subject))
      ((однакові? kind (як-є self-test)) (sens_file_authority_fail_self_test_5397 subject))
      ((однакові? kind (як-є missing-policy)) (sens_file_authority_fail_missing_policy_5397 subject))
      ((однакові? kind (як-є missing-census)) (sens_file_authority_fail_missing_census_5397 subject))
      ((однакові? kind (як-є missing-guard)) (sens_file_authority_fail_missing_guard_5397 subject))
      ((однакові? kind (як-є input-path)) (sens_file_authority_fail_input_path_5397 subject))
      ((однакові? kind (як-є tracked-tools-path)) (sens_file_authority_fail_tracked_tools_path_5397 subject))
      ((однакові? kind (як-є path)) (sens_file_authority_fail_path_5397 subject))
      ((однакові? kind (як-є git-mode)) (sens_file_authority_fail_git_mode_5405 subject))
      (так (sens_file_authority_fail_unknown_5397 subject)))))

(визначити файлова-гвардія-вимагати
  (функція (condition kind subject)
    (за-умовою
      ((однакові? condition 1) 1)
      (так (файлова-гвардія-заборонити kind subject)))))

(визначити файлова-гвардія-виконати
  (функція (input)
    (нехай ((input-ok
            (файлова-гвардія-вимагати
              (та
                (однакові? (файлова-гвардія-поле (як-є schema) input) (як-є file-authority-input/1))
                (файлова-гвардія-перелік-шляхів? (файлова-гвардія-поле (як-є added-paths) input))
                (файлова-гвардія-рядки-режимів-коректні?
                  (файлова-гвардія-поле (як-є added-modes) input)
                  (файлова-гвардія-поле (як-є added-paths) input))
                (файлова-гвардія-шляхи-мають-режим?
                  (файлова-гвардія-поле (як-є added-paths) input)
                  (файлова-гвардія-поле (як-є added-modes) input))
                (файлова-гвардія-перелік-шляхів? (файлова-гвардія-поле (як-є typechanged-paths) input))
                (файлова-гвардія-рядки-режимів-коректні?
                  (файлова-гвардія-поле (як-є typechanged-modes) input)
                  (файлова-гвардія-поле (як-є typechanged-paths) input))
                (файлова-гвардія-шляхи-мають-режим?
                  (файлова-гвардія-поле (як-є typechanged-paths) input)
                  (файлова-гвардія-поле (як-є typechanged-modes) input))
                (файлова-гвардія-перелік-шляхів? (файлова-гвардія-поле (як-є tracked-tools-paths) input))
                (файлова-гвардія-перелік-шляхів-інструментів? (файлова-гвардія-поле (як-є tracked-tools-paths) input)))
              (як-є input) "Git path transport")))
      (нехай ((policy-ok
              (файлова-гвардія-вимагати
                (файлова-гвардія-політика-коректна? *file-authority-policy*)
                (як-є policy) "knowledge/file-authority-policy.lisp")))
        (нехай ((census-ok
                (файлова-гвардія-вимагати
                  (файлова-гвардія-облік-коректний?
                    *foreign-tools-census*
                    (файлова-гвардія-поле (як-є tracked-tools-paths) input))
                  (як-є census) "knowledge/foreign-tools-census.lisp")))
          (нехай ((tests-ok
                  (файлова-гвардія-вимагати
                    (файлова-гвардія-самоперевірка (файлова-гвардія-поле (як-є new-foreign-tools) *foreign-tools-census*))
                    (як-є self-test) "positive/negative SENS witnesses")))
            (нехай ((added-ok
                    (файлова-гвардія-перевірити-додані
                      (файлова-гвардія-поле (як-є added-paths) input)
                      *file-authority-policy*
                      (файлова-гвардія-поле (як-є new-foreign-tools) *foreign-tools-census*)
                      (файлова-гвардія-поле (як-є added-modes) input))))
              (нехай ((typechanged-ok
                      (файлова-гвардія-перевірити-зміну-типу
                        (файлова-гвардія-поле (як-є typechanged-paths) input)
                        (файлова-гвардія-поле (як-є typechanged-modes) input))))
                (нехай ((tracked-ok
                        (файлова-гвардія-перевірити-відстежувані
                          (файлова-гвардія-поле (як-є tracked-tools-paths) input)
                          (файлова-гвардія-поле (як-є new-foreign-tools) *foreign-tools-census*))))
                  (друкувати
                  (список
                    (як-є SENS_FILE_AUTHORITY_PASS)
                    (як-є new-paths)
                    (довжина (файлова-гвардія-поле (як-є added-paths) input))
                    (як-є tracked-tool-paths)
                    (довжина (файлова-гвардія-поле (як-є tracked-tools-paths) input)))))))))))))

(за-умовою
  ((однакові? (файлова-гвардія-поле (як-є policy) *file-authority-source-status*) (як-є missing))
    (файлова-гвардія-заборонити (як-є missing-policy) "knowledge/file-authority-policy.lisp"))
  ((однакові? (файлова-гвардія-поле (як-є census) *file-authority-source-status*) (як-є missing))
    (файлова-гвардія-заборонити (як-є missing-census) "knowledge/foreign-tools-census.lisp"))
  ((однакові? (файлова-гвардія-поле (як-є guard) *file-authority-source-status*) (як-є missing))
    (файлова-гвардія-заборонити (як-є missing-guard) "knowledge/file-authority-guard.lisp"))
  (так (файлова-гвардія-виконати *file-authority-input*)))

; Сумісні історичні імена для наявних зовнішніх споживачів.
(визначити fg-field файлова-гвардія-поле)
(визначити fg-not файлова-гвардія-заперечення)
(визначити fg-has-field? файлова-гвардія-має-поле?)
(визначити fg-string-list? файлова-гвардія-список-рядків?)
(визначити fg-suffix? файлова-гвардія-має-суфікс?)
(визначити fg-path-canonical? файлова-гвардія-канонічний-шлях?)
(визначити fg-path-list? файлова-гвардія-перелік-шляхів?)
(визначити fg-tools-path-list? файлова-гвардія-перелік-шляхів-інструментів?)
(визначити fg-count файлова-гвардія-кількість)
(визначити fg-mode-count файлова-гвардія-кількість-режимів)
(визначити fg-find-mode файлова-гвардія-знайти-режим)
(визначити fg-mode-rows-valid? файлова-гвардія-рядки-режимів-коректні?)
(визначити fg-paths-have-mode? файлова-гвардія-шляхи-мають-режим?)
(визначити fg-mode-required? файлова-гвардія-режим-обовязковий?)
(визначити fg-mode-allowed? файлова-гвардія-режим-допущений?)
(визначити fg-check-typechanged файлова-гвардія-перевірити-зміну-типу)
(визначити fg-row-path файлова-гвардія-шлях-рядка)
(визначити fg-count-row файлова-гвардія-кількість-рядків)
(визначити fg-find-row файлова-гвардія-знайти-рядок)
(визначити fg-row-valid? файлова-гвардія-рядок-коректний?)
(визначити fg-foreign-path? файлова-гвардія-сторонній-шлях?)
(визначити fg-rows-valid? файлова-гвардія-рядки-коректні?)
(визначити fg-census-covers-tracked? файлова-гвардія-облік-охоплює-відстежувані?)
(визначити fg-policy-valid? файлова-гвардія-політика-коректна?)
(визначити fg-census-valid? файлова-гвардія-облік-коректний?)
(визначити fg-classify файлова-гвардія-класифікувати)
(визначити fg-check-added файлова-гвардія-перевірити-додані)
(визначити fg-check-tracked файлова-гвардія-перевірити-відстежувані)
(визначити fg-test-equal файлова-гвардія-перевірити-рівність)
(визначити fg-fixture-good файлова-гвардія-приклад-правильний)
(визначити fg-fixture-bad-status файлова-гвардія-приклад-помилковий-стан)
(визначити fg-self-test файлова-гвардія-самоперевірка)
(визначити fg-block файлова-гвардія-заборонити)
(визначити fg-require файлова-гвардія-вимагати)
(визначити fg-run файлова-гвардія-виконати)
