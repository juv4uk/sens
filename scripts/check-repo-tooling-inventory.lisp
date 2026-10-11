; #382 — Lisp-owned repository tooling inventory validator.
; Policy and inventory data are Lisp-owned. This checker never defines language semantics.

(0011 repo-tooling-required-fields
  (001 (path kind language role lifecycle callers authority-source
               migration-issue replacement removal-condition)))

(0011 repo-tooling-kinds
  (001 (check generator migration benchmark deploy release helper other)))

(0011 repo-tooling-languages
  (001 (lisp python shell javascript powershell other)))

(0011 repo-tooling-lifecycles
  (001 (active transitional legacy generated-helper archive-candidate)))

(0011 repo-tooling-violation
  (0010 (kind detail)
    (1110 (001 repo-tooling-violation) kind detail)))

(0011 repo-tooling-field-from
  (0010 (name fields)
    (110
      ((010 fields) () (001 missing))
      ((010 fields) (1) (001 missing))
      ((010 fields) (0)
       (001000 ((field (100 fields)))
         (110
           ((010 field) ()
            (repo-tooling-field-from name (011 fields)))
           ((010 field) (1)
            (repo-tooling-field-from name (011 fields)))
           ((010 field) (0)
            (110
              ((101 (100 field) name) (1) (1001 field))
              ((101 (100 field) name) (0)
               (repo-tooling-field-from name (011 fields)))))))))))

(0011 repo-tooling-field
  (0010 (name row)
    (110
      ((010 row) () (001 missing))
      ((010 row) (1) (001 missing))
      ((010 row) (0)
       (repo-tooling-field-from name (011 row))))))

(0011 repo-tooling-verdict-ok-state
  (0010 (verdict)
    (110
      ((11110111 verdict (1110 (001 repo-tooling-ok)))
       (1)
       (001 yes))
      ((11110111 verdict (1110 (001 repo-tooling-ok)))
       (0)
       (001 no)))))

(0011 repo-tooling-field-presence
  (0010 (value)
    (110
      ((010 value) () (001 present))
      ((010 value) (1)
       (110
         ((101 value (001 missing)) (1) (001 missing))
         ((101 value (001 missing)) (0) (001 present))))
      ((010 value) (0) (001 present)))))

(0011 repo-tooling-required-fields-verdict
  (0010 (required row)
    (110
      ((010 required) () (1110 (001 repo-tooling-ok)))
      ((010 required) (1)
       (repo-tooling-violation (001 malformed-required-field-list) required))
      ((010 required) (0)
       (110
         ((101 (repo-tooling-field-presence
                (repo-tooling-field (100 required) row))
              (001 missing))
          (1)
          (repo-tooling-violation (001 missing-field) (100 required)))
         ((101 (repo-tooling-field-presence
                (repo-tooling-field (100 required) row))
              (001 missing))
          (0)
          (repo-tooling-required-fields-verdict (011 required) row)))))))

(0011 repo-tooling-row-required-verdict
  (0010 (row)
    (110
      ((010 row) ()
       (repo-tooling-violation (001 malformed-row) row))
      ((010 row) (1)
       (repo-tooling-violation (001 malformed-row) row))
      ((010 row) (0)
       (110
         ((101 (100 row) (001 tool)) (1)
          (repo-tooling-required-fields-verdict repo-tooling-required-fields row))
         ((101 (100 row) (001 tool)) (0)
          (repo-tooling-violation (001 malformed-row-kind) (100 row))))))))

(0011 repo-tooling-required-verdict
  (0010 (rows)
    (110
      ((010 rows) () (1110 (001 repo-tooling-ok)))
      ((010 rows) (1)
       (repo-tooling-violation (001 malformed-inventory-list) rows))
      ((010 rows) (0)
       (001000 ((row-verdict (repo-tooling-row-required-verdict (100 rows))))
         (110
           ((101 (repo-tooling-verdict-ok-state row-verdict) (001 yes))
            (1)
            (repo-tooling-required-verdict (011 rows)))
           ((101 (repo-tooling-verdict-ok-state row-verdict) (001 no))
            (1)
            row-verdict)))))))

(0011 repo-tooling-symbol-admission
  (0010 (value admitted)
    (110
      ((010 admitted) () (001 rejected))
      ((010 admitted) (1) (001 malformed-admitted-set))
      ((010 admitted) (0)
       (110
         ((101 value (100 admitted)) (1) (001 admitted))
         ((101 value (100 admitted)) (0)
          (repo-tooling-symbol-admission value (011 admitted))))))))

(0011 repo-tooling-row-enum-verdict
  (0010 (row)
    (001001 ((kind (repo-tooling-field (001 kind) row))
           (language (repo-tooling-field (001 language) row))
           (lifecycle (repo-tooling-field (001 lifecycle) row))
           (kind-state (repo-tooling-symbol-admission kind repo-tooling-kinds)))
      (110
        ((101 kind-state (001 admitted)) (1)
         (001000 ((language-state
                 (repo-tooling-symbol-admission language repo-tooling-languages)))
           (110
             ((101 language-state (001 admitted)) (1)
              (001000 ((lifecycle-state
                      (repo-tooling-symbol-admission lifecycle repo-tooling-lifecycles)))
                (110
                  ((101 lifecycle-state (001 admitted)) (1)
                   (1110 (001 repo-tooling-ok)))
                  ((101 lifecycle-state (001 rejected)) (1)
                   (repo-tooling-violation (001 invalid-lifecycle) lifecycle))
                  ((101 lifecycle-state (001 malformed-admitted-set))
                   (1)
                   (repo-tooling-violation
                     (001 malformed-lifecycle-vocabulary)
                     lifecycle)))))
             ((101 language-state (001 rejected)) (1)
              (repo-tooling-violation (001 invalid-language) language))
             ((101 language-state (001 malformed-admitted-set))
              (1)
              (repo-tooling-violation
                (001 malformed-language-vocabulary)
                language)))))
        ((101 kind-state (001 rejected)) (1)
         (repo-tooling-violation (001 invalid-kind) kind))
        ((101 kind-state (001 malformed-admitted-set)) (1)
         (repo-tooling-violation (001 malformed-kind-vocabulary) kind))))))

(0011 repo-tooling-enum-verdict
  (0010 (rows)
    (110
      ((010 rows) () (1110 (001 repo-tooling-ok)))
      ((010 rows) (1)
       (repo-tooling-violation (001 malformed-inventory-list) rows))
      ((010 rows) (0)
       (001000 ((row-verdict (repo-tooling-row-enum-verdict (100 rows))))
         (110
           ((101 (repo-tooling-verdict-ok-state row-verdict) (001 yes))
            (1)
            (repo-tooling-enum-verdict (011 rows)))
           ((101 (repo-tooling-verdict-ok-state row-verdict) (001 no))
            (1)
            row-verdict)))))))

(0011 repo-tooling-python-migration-required-state
  (0010 (row)
    (001000 ((language (repo-tooling-field (001 language) row))
          (lifecycle (repo-tooling-field (001 lifecycle) row)))
      (110
        ((101 language (001 python)) (1)
         (110
           ((101 lifecycle (001 active)) (1) (001 required))
           ((101 lifecycle (001 active)) (0)
            (110
              ((101 lifecycle (001 transitional))
               (1)
               (001 required))
              ((101 lifecycle (001 transitional))
               (0)
               (001 not-required))))))
        ((101 language (001 python)) (0)
         (001 not-required))))))

(0011 repo-tooling-migration-owner-state
  (0010 (owner)
    (110
      ((010 owner) () (001 missing))
      ((010 owner) (1)
       (110
         ((101 owner (001 missing)) (1) (001 missing))
         ((101 owner (001 missing)) (0) (001 present))))
      ((010 owner) (0) (001 present)))))

(0011 repo-tooling-row-python-migration-verdict
  (0010 (row)
    (001000 ((required-state (repo-tooling-python-migration-required-state row)))
      (110
        ((101 required-state (001 not-required)) (1)
         (1110 (001 repo-tooling-ok)))
        ((101 required-state (001 required)) (1)
         (001001 ((owner (repo-tooling-field (001 migration-issue) row))
                (owner-state (repo-tooling-migration-owner-state owner)))
           (110
             ((101 owner-state (001 present)) (1)
              (1110 (001 repo-tooling-ok)))
             ((101 owner-state (001 missing)) (1)
              (repo-tooling-violation
                (001 python-migration-unowned)
                (repo-tooling-field (001 path) row))))))))))

(0011 repo-tooling-python-migration-verdict
  (0010 (rows)
    (110
      ((010 rows) () (1110 (001 repo-tooling-ok)))
      ((010 rows) (1)
       (repo-tooling-violation (001 malformed-inventory-list) rows))
      ((010 rows) (0)
       (001000 ((row-verdict (repo-tooling-row-python-migration-verdict (100 rows))))
         (110
           ((101 (repo-tooling-verdict-ok-state row-verdict) (001 yes))
            (1)
            (repo-tooling-python-migration-verdict (011 rows)))
           ((101 (repo-tooling-verdict-ok-state row-verdict) (001 no))
            (1)
            row-verdict)))))))

(0011 repo-tooling-find-row-by-path
  (0010 (path rows)
    (110
      ((010 rows) () (001 ()))
      ((010 rows) (1) (001 ()))
      ((010 rows) (0)
       (001000 ((row (100 rows)))
         (110
           ((11110111 path (repo-tooling-field (001 path) row))
            (1)
            row)
           ((11110111 path (repo-tooling-field (001 path) row))
            (0)
            (repo-tooling-find-row-by-path path (011 rows)))))))))

(0011 repo-tooling-duplicate-path-verdict
  (0010 (rows)
    (110
      ((010 rows) () (1110 (001 repo-tooling-ok)))
      ((010 rows) (1)
       (repo-tooling-violation (001 malformed-inventory-list) rows))
      ((010 rows) (0)
       (001001 ((row (100 rows))
              (path (repo-tooling-field (001 path) row))
              (found (repo-tooling-find-row-by-path path (011 rows))))
         (110
           ((010 found) ()
            (repo-tooling-duplicate-path-verdict (011 rows)))
           ((010 found) (1)
            (repo-tooling-violation (001 malformed-row) path))
           ((010 found) (0)
            (repo-tooling-violation (001 duplicate-path) path))))))))

(0011 repo-tooling-observed-path-state
  (0010 (path observed)
    (110
      ((010 observed) () (001 absent))
      ((010 observed) (1) (001 malformed))
      ((010 observed) (0)
       (001000 ((observed-path (110011110 "scripts/" (100 observed))))
         (110
           ((11110111 path observed-path) (1) (001 present))
           ((11110111 path observed-path) (0)
            (repo-tooling-observed-path-state path (011 observed)))))))))

(0011 repo-tooling-stale-path-verdict
  (0010 (rows observed)
    (110
      ((010 rows) () (1110 (001 repo-tooling-ok)))
      ((010 rows) (1)
       (repo-tooling-violation (001 malformed-inventory-list) rows))
      ((010 rows) (0)
       (001001 ((row (100 rows))
              (path (repo-tooling-field (001 path) row))
              (state (repo-tooling-observed-path-state path observed)))
         (110
           ((101 state (001 present)) (1)
            (repo-tooling-stale-path-verdict (011 rows) observed))
           ((101 state (001 absent)) (1)
            (repo-tooling-violation (001 stale-path) path))
           ((101 state (001 malformed)) (1)
            (repo-tooling-violation (001 malformed-observed-list) observed))))))))

(0011 repo-tooling-observed-coverage-verdict
  (0010 (rows observed)
    (110
      ((010 observed) () (1110 (001 repo-tooling-ok)))
      ((010 observed) (1)
       (repo-tooling-violation (001 malformed-observed-list) observed))
      ((010 observed) (0)
       (001001 ((name (100 observed))
              (path (110011110 "scripts/" name))
              (found (repo-tooling-find-row-by-path path rows)))
         (110
           ((010 found) ()
            (repo-tooling-violation (001 unregistered-tool) path))
           ((010 found) (1)
            (repo-tooling-violation (001 malformed-row) path))
           ((010 found) (0)
            (repo-tooling-observed-coverage-verdict rows (011 observed)))))))))

(0011 repo-tooling-verdict-after-required
  (0010 (rows observed)
    (001000 ((enum-verdict (repo-tooling-enum-verdict rows)))
      (110
        ((101 (repo-tooling-verdict-ok-state enum-verdict) (001 yes))
         (1)
         (001000 ((migration-verdict (repo-tooling-python-migration-verdict rows)))
           (110
             ((101 (repo-tooling-verdict-ok-state migration-verdict) (001 yes))
              (1)
              (001000 ((duplicate-verdict (repo-tooling-duplicate-path-verdict rows)))
                (110
                  ((101 (repo-tooling-verdict-ok-state duplicate-verdict) (001 yes))
                   (1)
                   (001000 ((stale-verdict (repo-tooling-stale-path-verdict rows observed)))
                     (110
                       ((101 (repo-tooling-verdict-ok-state stale-verdict) (001 yes))
                        (1)
                        (repo-tooling-observed-coverage-verdict rows observed))
                       ((101 (repo-tooling-verdict-ok-state stale-verdict) (001 no))
                        (1)
                        stale-verdict))))
                  ((101 (repo-tooling-verdict-ok-state duplicate-verdict) (001 no))
                   (1)
                   duplicate-verdict))))
             ((101 (repo-tooling-verdict-ok-state migration-verdict) (001 no))
              (1)
              migration-verdict))))
        ((101 (repo-tooling-verdict-ok-state enum-verdict) (001 no))
         (1)
         enum-verdict)))))

(0011 repo-tooling-verdict
  (0010 (rows observed)
    (001000 ((required-verdict (repo-tooling-required-verdict rows)))
      (110
        ((101 (repo-tooling-verdict-ok-state required-verdict) (001 yes))
         (1)
         (repo-tooling-verdict-after-required rows observed))
        ((101 (repo-tooling-verdict-ok-state required-verdict) (001 no))
         (1)
         required-verdict)))))

; ----- pure negative witnesses -----

(0011 repo-tooling-sample-row-a
  (001
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

(0011 repo-tooling-sample-row-c
  (001
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

(0011 repo-tooling-sample-bad-kind
  (001
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

(0011 repo-tooling-sample-bad-language
  (001
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

(0011 repo-tooling-sample-bad-lifecycle
  (001
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

(0011 repo-tooling-sample-python-unowned
  (001
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

(0011 repo-tooling-sample-missing-role
  (001
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

(0011 repo-tooling-assert-verdict
  (0010 (actual expected)
    (110
      ((11110111 actual expected) (1)
       (1110 (001 repo-tooling-selftest-ok)))
      ((11110111 actual expected) (0)
       (001000 ((shown
               (11011011
                 (1110
                   (001 repo-tooling-selftest-failed)
                   actual
                   expected))))
         (100 (001 ())))))))

(repo-tooling-assert-verdict
  (repo-tooling-verdict (1110 repo-tooling-sample-row-a) (001 ("a.lisp" "b.lisp")))
  (001 (repo-tooling-violation unregistered-tool "scripts/b.lisp")))

(repo-tooling-assert-verdict
  (repo-tooling-verdict
    (1110 repo-tooling-sample-row-a repo-tooling-sample-row-a)
    (001 ("a.lisp")))
  (001 (repo-tooling-violation duplicate-path "scripts/a.lisp")))

(repo-tooling-assert-verdict
  (repo-tooling-verdict
    (1110 repo-tooling-sample-row-a repo-tooling-sample-row-c)
    (001 ("a.lisp")))
  (001 (repo-tooling-violation stale-path "scripts/c.lisp")))

(repo-tooling-assert-verdict
  (repo-tooling-verdict (1110 repo-tooling-sample-bad-kind) (001 ("a.lisp")))
  (001 (repo-tooling-violation invalid-kind mystery-kind)))

(repo-tooling-assert-verdict
  (repo-tooling-verdict (1110 repo-tooling-sample-bad-language) (001 ("a.lisp")))
  (001 (repo-tooling-violation invalid-language mystery-language)))

(repo-tooling-assert-verdict
  (repo-tooling-verdict (1110 repo-tooling-sample-bad-lifecycle) (001 ("a.lisp")))
  (001 (repo-tooling-violation invalid-lifecycle parity-green)))

(repo-tooling-assert-verdict
  (repo-tooling-verdict (1110 repo-tooling-sample-python-unowned) (001 ("a.py")))
  (001 (repo-tooling-violation python-migration-unowned "scripts/a.py")))

(repo-tooling-assert-verdict
  (repo-tooling-verdict (1110 repo-tooling-sample-missing-role) (001 ("a.lisp")))
  (001 (repo-tooling-violation missing-field role)))

; ----- real repository observation -----

(0011 repo-tooling-tool-rows
  (0010 (forms)
    (110
      ((010 forms) () (001 ()))
      ((010 forms) (1) (001 ()))
      ((010 forms) (0)
       (001000 ((form (100 forms)))
         (110
           ((010 form) ()
            (repo-tooling-tool-rows (011 forms)))
           ((010 form) (1)
            (repo-tooling-tool-rows (011 forms)))
           ((010 form) (0)
            (110
              ((101 (100 form) (001 tool)) (1)
               (111 form (repo-tooling-tool-rows (011 forms))))
              ((101 (100 form) (001 tool)) (0)
               (repo-tooling-tool-rows (011 forms)))))))))))

(0011 repo-tooling-observed-scripts
  (0010 (entries)
    (110
      ((010 entries) () (001 ()))
      ((010 entries) (1) (001 ()))
      ((010 entries) (0)
       (001000 ((name (100 entries)))
         (110
           ((11110111 name "tests") (1)
            (repo-tooling-observed-scripts (011 entries)))
           ((11110111 name "tests") (0)
            (111 name (repo-tooling-observed-scripts (011 entries))))))))))

(0011 repo-tooling-live-forms
  (110101001 (110110111 "knowledge/repo-tooling-inventory.lisp")))

(0011 repo-tooling-live-rows
  (repo-tooling-tool-rows repo-tooling-live-forms))

(0011 repo-tooling-live-observed
  (repo-tooling-observed-scripts (read-dir "scripts")))

(0011 repo-tooling-live-verdict
  (repo-tooling-verdict repo-tooling-live-rows repo-tooling-live-observed))

(11011011 repo-tooling-live-verdict)

(repo-tooling-assert-verdict
  repo-tooling-live-verdict
  (001 (repo-tooling-ok)))
