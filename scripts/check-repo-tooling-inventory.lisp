; #382 — Lisp-owned repository tooling inventory validator.
; Policy and inventory data are Lisp-owned. This checker never defines language semantics.

(визначити repo-tooling-required-fields
  (як-є (path kind language role lifecycle callers authority-source
               migration-issue replacement removal-condition)))

(визначити repo-tooling-kinds
  (як-є (check generator migration benchmark deploy release helper other)))

(визначити repo-tooling-languages
  (як-є (lisp python shell javascript powershell other)))

(визначити repo-tooling-lifecycles
  (як-є (active transitional legacy generated-helper archive-candidate)))

(визначити repo-tooling-violation
  (функція (kind detail)
    (список (як-є repo-tooling-violation) kind detail)))

(визначити repo-tooling-field-from
  (функція (name fields)
    (за-умовою
      ((атом? fields) () (як-є missing))
      ((атом? fields) (1) (як-є missing))
      ((атом? fields) (0)
       (001000 ((field (100 fields)))
         (за-умовою
           ((атом? field) ()
            (repo-tooling-field-from name (решта fields)))
           ((атом? field) (1)
            (repo-tooling-field-from name (решта fields)))
           ((атом? field) (0)
            (за-умовою
              ((тотожне? (перше field) name) (1) (друге field))
              ((тотожне? (перше field) name) (0)
               (repo-tooling-field-from name (решта fields)))))))))))

(визначити repo-tooling-field
  (функція (name row)
    (за-умовою
      ((атом? row) () (як-є missing))
      ((атом? row) (1) (як-є missing))
      ((атом? row) (0)
       (repo-tooling-field-from name (решта row))))))

(визначити repo-tooling-verdict-ok-state
  (функція (verdict)
    (за-умовою
      ((11110111 verdict (1110 (001 repo-tooling-ok)))
       (1)
       (як-є yes))
      ((11110111 verdict (1110 (001 repo-tooling-ok)))
       (0)
       (як-є no)))))

(визначити repo-tooling-field-presence
  (функція (value)
    (за-умовою
      ((атом? value) () (як-є present))
      ((атом? value) (1)
       (за-умовою
         ((тотожне? value (як-є missing)) (1) (як-є missing))
         ((тотожне? value (як-є missing)) (0) (як-є present))))
      ((атом? value) (0) (як-є present)))))

(визначити repo-tooling-required-fields-verdict
  (функція (required row)
    (за-умовою
      ((атом? required) () (список (як-є repo-tooling-ok)))
      ((атом? required) (1)
       (repo-tooling-violation (як-є malformed-required-field-list) required))
      ((атом? required) (0)
       (за-умовою
         ((тотожне? (repo-tooling-field-presence
                (repo-tooling-field (перше required) row))
              (як-є missing))
          (1)
          (repo-tooling-violation (як-є missing-field) (перше required)))
         ((тотожне? (repo-tooling-field-presence
                (repo-tooling-field (перше required) row))
              (як-є missing))
          (0)
          (repo-tooling-required-fields-verdict (решта required) row)))))))

(визначити repo-tooling-row-required-verdict
  (функція (row)
    (за-умовою
      ((атом? row) ()
       (repo-tooling-violation (як-є malformed-row) row))
      ((атом? row) (1)
       (repo-tooling-violation (як-є malformed-row) row))
      ((атом? row) (0)
       (за-умовою
         ((тотожне? (перше row) (як-є tool)) (1)
          (repo-tooling-required-fields-verdict repo-tooling-required-fields row))
         ((тотожне? (перше row) (як-є tool)) (0)
          (repo-tooling-violation (як-є malformed-row-kind) (перше row))))))))

(визначити repo-tooling-required-verdict
  (функція (rows)
    (за-умовою
      ((атом? rows) () (список (як-є repo-tooling-ok)))
      ((атом? rows) (1)
       (repo-tooling-violation (як-є malformed-inventory-list) rows))
      ((атом? rows) (0)
       (001000 ((row-verdict (repo-tooling-row-required-verdict (100 rows))))
         (за-умовою
           ((тотожне? (repo-tooling-verdict-ok-state row-verdict) (як-є yes))
            (1)
            (repo-tooling-required-verdict (решта rows)))
           ((тотожне? (repo-tooling-verdict-ok-state row-verdict) (як-є no))
            (1)
            row-verdict)))))))

(визначити repo-tooling-symbol-admission
  (функція (value admitted)
    (за-умовою
      ((атом? admitted) () (як-є rejected))
      ((атом? admitted) (1) (як-є malformed-admitted-set))
      ((атом? admitted) (0)
       (за-умовою
         ((тотожне? value (перше admitted)) (1) (як-є admitted))
         ((тотожне? value (перше admitted)) (0)
          (repo-tooling-symbol-admission value (решта admitted))))))))

(визначити repo-tooling-row-enum-verdict
  (функція (row)
    (001001 ((kind (repo-tooling-field (001 kind) row))
           (language (repo-tooling-field (як-є language) row))
           (lifecycle (repo-tooling-field (як-є lifecycle) row))
           (kind-state (repo-tooling-symbol-admission kind repo-tooling-kinds)))
      (за-умовою
        ((тотожне? kind-state (як-є admitted)) (1)
         (001000 ((language-state
                 (repo-tooling-symbol-admission language repo-tooling-languages)))
           (за-умовою
             ((тотожне? language-state (як-є admitted)) (1)
              (001000 ((lifecycle-state
                      (repo-tooling-symbol-admission lifecycle repo-tooling-lifecycles)))
                (за-умовою
                  ((тотожне? lifecycle-state (як-є admitted)) (1)
                   (список (як-є repo-tooling-ok)))
                  ((тотожне? lifecycle-state (як-є rejected)) (1)
                   (repo-tooling-violation (як-є invalid-lifecycle) lifecycle))
                  ((тотожне? lifecycle-state (як-є malformed-admitted-set))
                   (1)
                   (repo-tooling-violation
                     (як-є malformed-lifecycle-vocabulary)
                     lifecycle)))))
             ((тотожне? language-state (як-є rejected)) (1)
              (repo-tooling-violation (як-є invalid-language) language))
             ((тотожне? language-state (як-є malformed-admitted-set))
              (1)
              (repo-tooling-violation
                (як-є malformed-language-vocabulary)
                language)))))
        ((тотожне? kind-state (як-є rejected)) (1)
         (repo-tooling-violation (як-є invalid-kind) kind))
        ((тотожне? kind-state (як-є malformed-admitted-set)) (1)
         (repo-tooling-violation (як-є malformed-kind-vocabulary) kind))))))

(визначити repo-tooling-enum-verdict
  (функція (rows)
    (за-умовою
      ((атом? rows) () (список (як-є repo-tooling-ok)))
      ((атом? rows) (1)
       (repo-tooling-violation (як-є malformed-inventory-list) rows))
      ((атом? rows) (0)
       (001000 ((row-verdict (repo-tooling-row-enum-verdict (100 rows))))
         (за-умовою
           ((тотожне? (repo-tooling-verdict-ok-state row-verdict) (як-є yes))
            (1)
            (repo-tooling-enum-verdict (решта rows)))
           ((тотожне? (repo-tooling-verdict-ok-state row-verdict) (як-є no))
            (1)
            row-verdict)))))))

(визначити repo-tooling-python-migration-required-state
  (функція (row)
    (001000 ((language (repo-tooling-field (001 language) row))
          (lifecycle (repo-tooling-field (як-є lifecycle) row)))
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

(визначити repo-tooling-migration-owner-state
  (функція (owner)
    (за-умовою
      ((атом? owner) () (як-є missing))
      ((атом? owner) (1)
       (за-умовою
         ((тотожне? owner (як-є missing)) (1) (як-є missing))
         ((тотожне? owner (як-є missing)) (0) (як-є present))))
      ((атом? owner) (0) (як-є present)))))

(визначити repo-tooling-row-python-migration-verdict
  (функція (row)
    (001000 ((required-state (repo-tooling-python-migration-required-state row)))
      (за-умовою
        ((тотожне? required-state (як-є not-required)) (1)
         (список (як-є repo-tooling-ok)))
        ((тотожне? required-state (як-є required)) (1)
         (001001 ((owner (repo-tooling-field (001 migration-issue) row))
                (owner-state (repo-tooling-migration-owner-state owner)))
           (за-умовою
             ((тотожне? owner-state (як-є present)) (1)
              (список (як-є repo-tooling-ok)))
             ((тотожне? owner-state (як-є missing)) (1)
              (repo-tooling-violation
                (як-є python-migration-unowned)
                (repo-tooling-field (як-є path) row))))))))))

(визначити repo-tooling-python-migration-verdict
  (функція (rows)
    (за-умовою
      ((атом? rows) () (список (як-є repo-tooling-ok)))
      ((атом? rows) (1)
       (repo-tooling-violation (як-є malformed-inventory-list) rows))
      ((атом? rows) (0)
       (001000 ((row-verdict (repo-tooling-row-python-migration-verdict (100 rows))))
         (за-умовою
           ((тотожне? (repo-tooling-verdict-ok-state row-verdict) (як-є yes))
            (1)
            (repo-tooling-python-migration-verdict (решта rows)))
           ((тотожне? (repo-tooling-verdict-ok-state row-verdict) (як-є no))
            (1)
            row-verdict)))))))

(визначити repo-tooling-find-row-by-path
  (функція (path rows)
    (за-умовою
      ((атом? rows) () (як-є ()))
      ((атом? rows) (1) (як-є ()))
      ((атом? rows) (0)
       (001000 ((row (100 rows)))
         (за-умовою
           ((11110111 path (repo-tooling-field (001 path) row))
            (1)
            row)
           ((11110111 path (repo-tooling-field (001 path) row))
            (0)
            (repo-tooling-find-row-by-path path (решта rows)))))))))

(визначити repo-tooling-duplicate-path-verdict
  (функція (rows)
    (за-умовою
      ((атом? rows) () (список (як-є repo-tooling-ok)))
      ((атом? rows) (1)
       (repo-tooling-violation (як-є malformed-inventory-list) rows))
      ((атом? rows) (0)
       (001001 ((row (100 rows))
              (path (repo-tooling-field (як-є path) row))
              (found (repo-tooling-find-row-by-path path (решта rows))))
         (за-умовою
           ((атом? found) ()
            (repo-tooling-duplicate-path-verdict (решта rows)))
           ((атом? found) (1)
            (repo-tooling-violation (як-є malformed-row) path))
           ((атом? found) (0)
            (repo-tooling-violation (як-є duplicate-path) path))))))))

(визначити repo-tooling-observed-path-state
  (функція (path observed)
    (за-умовою
      ((атом? observed) () (як-є absent))
      ((атом? observed) (1) (як-є malformed))
      ((атом? observed) (0)
       (001000 ((observed-path (110011110 "scripts/" (100 observed))))
         (за-умовою
           ((11110111 path observed-path) (1) (001 present))
           ((11110111 path observed-path) (0)
            (repo-tooling-observed-path-state path (решта observed)))))))))

(визначити repo-tooling-stale-path-verdict
  (функція (rows observed)
    (за-умовою
      ((атом? rows) () (список (як-є repo-tooling-ok)))
      ((атом? rows) (1)
       (repo-tooling-violation (як-є malformed-inventory-list) rows))
      ((атом? rows) (0)
       (001001 ((row (100 rows))
              (path (repo-tooling-field (як-є path) row))
              (state (repo-tooling-observed-path-state path observed)))
         (за-умовою
           ((тотожне? state (як-є present)) (1)
            (repo-tooling-stale-path-verdict (решта rows) observed))
           ((тотожне? state (як-є absent)) (1)
            (repo-tooling-violation (як-є stale-path) path))
           ((тотожне? state (як-є malformed)) (1)
            (repo-tooling-violation (як-є malformed-observed-list) observed))))))))

(визначити repo-tooling-observed-coverage-verdict
  (функція (rows observed)
    (за-умовою
      ((атом? observed) () (список (як-є repo-tooling-ok)))
      ((атом? observed) (1)
       (repo-tooling-violation (як-є malformed-observed-list) observed))
      ((атом? observed) (0)
       (001001 ((name (100 observed))
              (path (110011110 "scripts/" name))
              (found (repo-tooling-find-row-by-path path rows)))
         (за-умовою
           ((атом? found) ()
            (repo-tooling-violation (як-є unregistered-tool) path))
           ((атом? found) (1)
            (repo-tooling-violation (як-є malformed-row) path))
           ((атом? found) (0)
            (repo-tooling-observed-coverage-verdict rows (решта observed)))))))))

(визначити repo-tooling-verdict-after-required
  (функція (rows observed)
    (001000 ((enum-verdict (repo-tooling-enum-verdict rows)))
      (за-умовою
        ((тотожне? (repo-tooling-verdict-ok-state enum-verdict) (як-є yes))
         (1)
         (001000 ((migration-verdict (repo-tooling-python-migration-verdict rows)))
           (за-умовою
             ((тотожне? (repo-tooling-verdict-ok-state migration-verdict) (як-є yes))
              (1)
              (001000 ((duplicate-verdict (repo-tooling-duplicate-path-verdict rows)))
                (за-умовою
                  ((тотожне? (repo-tooling-verdict-ok-state duplicate-verdict) (як-є yes))
                   (1)
                   (001000 ((stale-verdict (repo-tooling-stale-path-verdict rows observed)))
                     (за-умовою
                       ((тотожне? (repo-tooling-verdict-ok-state stale-verdict) (як-є yes))
                        (1)
                        (repo-tooling-observed-coverage-verdict rows observed))
                       ((тотожне? (repo-tooling-verdict-ok-state stale-verdict) (як-є no))
                        (1)
                        stale-verdict))))
                  ((тотожне? (repo-tooling-verdict-ok-state duplicate-verdict) (як-є no))
                   (1)
                   duplicate-verdict))))
             ((тотожне? (repo-tooling-verdict-ok-state migration-verdict) (як-є no))
              (1)
              migration-verdict))))
        ((тотожне? (repo-tooling-verdict-ok-state enum-verdict) (як-є no))
         (1)
         enum-verdict)))))

(визначити repo-tooling-verdict
  (функція (rows observed)
    (001000 ((required-verdict (repo-tooling-required-verdict rows)))
      (за-умовою
        ((тотожне? (repo-tooling-verdict-ok-state required-verdict) (як-є yes))
         (1)
         (repo-tooling-verdict-after-required rows observed))
        ((тотожне? (repo-tooling-verdict-ok-state required-verdict) (як-є no))
         (1)
         required-verdict)))))

; ----- pure negative witnesses -----

(визначити repo-tooling-sample-row-a
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

(визначити repo-tooling-sample-row-c
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

(визначити repo-tooling-sample-bad-kind
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

(визначити repo-tooling-sample-bad-language
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

(визначити repo-tooling-sample-bad-lifecycle
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

(визначити repo-tooling-sample-python-unowned
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

(визначити repo-tooling-sample-missing-role
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

(визначити repo-tooling-assert-verdict
  (функція (actual expected)
    (за-умовою
      ((11110111 actual expected) (1)
       (список (як-є repo-tooling-selftest-ok)))
      ((11110111 actual expected) (0)
       (001000 ((shown
               (11011011
                 (список
                   (як-є repo-tooling-selftest-failed)
                   actual
                   expected))))
         (перше (як-є ())))))))

(repo-tooling-assert-verdict
  (repo-tooling-verdict (список repo-tooling-sample-row-a) (як-є ("a.lisp" "b.lisp")))
  (як-є (repo-tooling-violation unregistered-tool "scripts/b.lisp")))

(repo-tooling-assert-verdict
  (repo-tooling-verdict
    (список repo-tooling-sample-row-a repo-tooling-sample-row-a)
    (як-є ("a.lisp")))
  (як-є (repo-tooling-violation duplicate-path "scripts/a.lisp")))

(repo-tooling-assert-verdict
  (repo-tooling-verdict
    (список repo-tooling-sample-row-a repo-tooling-sample-row-c)
    (як-є ("a.lisp")))
  (як-є (repo-tooling-violation stale-path "scripts/c.lisp")))

(repo-tooling-assert-verdict
  (repo-tooling-verdict (список repo-tooling-sample-bad-kind) (як-є ("a.lisp")))
  (як-є (repo-tooling-violation invalid-kind mystery-kind)))

(repo-tooling-assert-verdict
  (repo-tooling-verdict (список repo-tooling-sample-bad-language) (як-є ("a.lisp")))
  (як-є (repo-tooling-violation invalid-language mystery-language)))

(repo-tooling-assert-verdict
  (repo-tooling-verdict (список repo-tooling-sample-bad-lifecycle) (як-є ("a.lisp")))
  (як-є (repo-tooling-violation invalid-lifecycle parity-green)))

(repo-tooling-assert-verdict
  (repo-tooling-verdict (список repo-tooling-sample-python-unowned) (як-є ("a.py")))
  (як-є (repo-tooling-violation python-migration-unowned "scripts/a.py")))

(repo-tooling-assert-verdict
  (repo-tooling-verdict (список repo-tooling-sample-missing-role) (як-є ("a.lisp")))
  (як-є (repo-tooling-violation missing-field role)))

; ----- real repository observation -----

(визначити repo-tooling-tool-rows
  (функція (forms)
    (за-умовою
      ((атом? forms) () (як-є ()))
      ((атом? forms) (1) (як-є ()))
      ((атом? forms) (0)
       (001000 ((form (100 forms)))
         (за-умовою
           ((атом? form) ()
            (repo-tooling-tool-rows (решта forms)))
           ((атом? form) (1)
            (repo-tooling-tool-rows (решта forms)))
           ((атом? form) (0)
            (за-умовою
              ((тотожне? (перше form) (як-є tool)) (1)
               (сполучити form (repo-tooling-tool-rows (решта forms))))
              ((тотожне? (перше form) (як-є tool)) (0)
               (repo-tooling-tool-rows (решта forms)))))))))))

(визначити repo-tooling-observed-scripts
  (функція (entries)
    (за-умовою
      ((атом? entries) () (як-є ()))
      ((атом? entries) (1) (як-є ()))
      ((атом? entries) (0)
       (001000 ((name (100 entries)))
         (за-умовою
           ((11110111 name "tests") (1)
            (repo-tooling-observed-scripts (решта entries)))
           ((11110111 name "tests") (0)
            (сполучити name (repo-tooling-observed-scripts (решта entries))))))))))

(визначити repo-tooling-live-forms
  (110101001 (110110111 "knowledge/repo-tooling-inventory.lisp")))

(визначити repo-tooling-live-rows
  (repo-tooling-tool-rows repo-tooling-live-forms))

(визначити repo-tooling-live-observed
  (repo-tooling-observed-scripts (read-dir "scripts")))

(визначити repo-tooling-live-verdict
  (repo-tooling-verdict repo-tooling-live-rows repo-tooling-live-observed))

(11011011 repo-tooling-live-verdict)

(repo-tooling-assert-verdict
  repo-tooling-live-verdict
  (як-є (repo-tooling-ok)))
