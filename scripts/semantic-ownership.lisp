; scripts/semantic-ownership.lisp — Lisp-owned replacement candidate for #553.
; During migration, scripts/semantic-ownership.py remains the differential oracle.
; This file owns validation/report mechanics only. Authority data remains in
; knowledge/semantic-ownership.lisp and knowledge/meta-eval-evidence.lisp.

(def ownership-classes
  (quote
    (canon-ground canon-operation derived-tooling host-authorization
     host-mechanism host-observation lisp-owned necessary-form unknown)))

(def ownership-classes-sorted
  (quote
    (canon-ground canon-operation derived-tooling host-authorization
     host-mechanism host-observation lisp-owned necessary-form unknown)))

(def ownership-statuses
  (quote (confirmed partial broken unknown)))

(def ownership-statuses-sorted
  (quote (broken confirmed partial unknown)))

(def ownership-layers
  (quote
    (canon bootstrap stdlib reasoning knowledge self-hosting
     host-capability tooling)))

(def ownership-layers-sorted
  (quote
    (bootstrap canon host-capability knowledge reasoning self-hosting stdlib tooling)))

(def str+
  (lambda args
    (reduce (lambda (acc part) (string-append acc part)) "" args)))

(def token-text
  (lambda (value)
    (cond
      ((string? value) value)
      ((symbol? value) (symbol->string value))
      (t (write-to-string value)))))

(def dash?
  (lambda (value)
    (or (equal? value (quote -)) (equal? value "-"))))

(def ownership-ok (lambda () (list (quote semantic-ownership-ok))))

(def ownership-violation
  (lambda (kind detail)
    (list (quote semantic-ownership-violation) kind detail)))

(def ownership-ok?
  (lambda (verdict)
    (equal? verdict (ownership-ok))))

(def admitted?
  (lambda (value choices)
    (member? value choices)))

(def split-char-onto
  (lambda (text separator current out)
    (cond
      ((string-empty? text)
       (cond
         ((string-empty? current) (reverse out))
         (t (reverse (cons current out)))))
      ((equal? (string-first text) separator)
       (split-char-onto
         (string-rest text)
         separator
         ""
         (cond
           ((string-empty? current) out)
           (t (cons current out)))))
      (t
       (split-char-onto
         (string-rest text)
         separator
         (string-append current (string-first text))
         out)))))

(def split-char
  (lambda (text separator)
    (split-char-onto text separator "" (quote ()))))

(def path-items
  (lambda (value)
    (cond
      ((dash? value) (quote ()))
      ((string? value) (split-char value ";"))
      (t (quote ())))))

(def path-join
  (lambda (prefix name)
    (cond
      ((string-empty? prefix) name)
      (t (str+ prefix "/" name)))))

(def path-components-present?
  (lambda (prefix parts)
    (cond
      ((atom parts) t)
      (t
       (let* ((dir (cond ((string-empty? prefix) ".") (t prefix)))
              (entries (read-dir dir))
              (name (car parts)))
         (cond
           ((member? name entries)
            (cond
              ((atom (cdr parts)) t)
              (t
               (path-components-present?
                 (path-join prefix name)
                 (cdr parts)))))
           (t (quote ()))))))))

(def path-present?
  (lambda (path)
    (path-components-present? "" (split-char path "/"))))

(def paths-present-verdict
  (lambda (paths context)
    (cond
      ((atom paths) (ownership-ok))
      ((path-present? (car paths))
       (paths-present-verdict (cdr paths) context))
      (t
       (ownership-violation
         (quote missing-referenced-path)
         (list context (car paths)))))))

(def hex-char?
  (lambda (ch)
    (member? ch (quote ("0" "1" "2" "3" "4" "5" "6" "7" "8" "9"
                       "a" "b" "c" "d" "e" "f")))))

(def all-hex?
  (lambda (text)
    (cond
      ((string-empty? text) t)
      ((hex-char? (string-first text)) (all-hex? (string-rest text)))
      (t (quote ())))))

(def hex40?
  (lambda (value)
    (and
      (string? value)
      (equal? (string-length value) 40)
      (all-hex? value))))

(def ownership-row?
  (lambda (form)
    (and (not (atom form)) (eq (car form) (quote ownership)))))

(def migration-row?
  (lambda (form)
    (and (not (atom form)) (eq (car form) (quote migration)))))

(def meta-row?
  (lambda (form)
    (and (not (atom form)) (eq (car form) (quote row)))))

(def collect-tagged
  (lambda (forms predicate)
    (cond
      ((atom forms) (quote ()))
      ((predicate (car forms))
       (cons (car forms) (collect-tagged (cdr forms) predicate)))
      (t (collect-tagged (cdr forms) predicate)))))

(def ownership-key (lambda (row) (nth 1 row)))
(def ownership-semantic-id (lambda (row) (nth 2 row)))
(def ownership-class (lambda (row) (nth 3 row)))
(def ownership-layer (lambda (row) (nth 4 row)))
(def ownership-status (lambda (row) (nth 5 row)))
(def ownership-policy (lambda (row) (nth 6 row)))
(def ownership-behavior (lambda (row) (nth 7 row)))
(def ownership-implementation-paths (lambda (row) (nth 8 row)))
(def ownership-evidence-paths (lambda (row) (nth 9 row)))
(def ownership-previous-owner (lambda (row) (nth 10 row)))
(def ownership-migration-ref (lambda (row) (nth 11 row)))

(def migration-key (lambda (row) (nth 1 row)))
(def migration-from-owner (lambda (row) (nth 2 row)))
(def migration-to-owner (lambda (row) (nth 3 row)))
(def migration-status (lambda (row) (nth 4 row)))
(def migration-commit (lambda (row) (nth 5 row)))
(def migration-behavior (lambda (row) (nth 6 row)))
(def migration-evidence-paths (lambda (row) (nth 7 row)))

(def row-key
  (lambda (row)
    (cond
      ((ownership-row? row) (ownership-key row))
      ((migration-row? row) (migration-key row))
      (t (quote unknown)))))

(def ownership-row-shape-verdict
  (lambda (row)
    (cond
      ((equal? (length row) 12) (ownership-ok))
      (t
       (ownership-violation
         (quote malformed-ownership-row)
         (cond
           ((> (length row) 1) (ownership-key row))
           (t (quote ?))))))))

(def migration-row-shape-verdict
  (lambda (row)
    (cond
      ((equal? (length row) 8) (ownership-ok))
      (t
       (ownership-violation
         (quote malformed-migration-row)
         (cond
           ((> (length row) 1) (migration-key row))
           (t (quote ?))))))))

(def ownership-row-enum-verdict
  (lambda (row)
    (cond
      ((not (admitted? (ownership-class row) ownership-classes))
       (ownership-violation
         (quote invalid-owner-class)
         (list (ownership-key row) (ownership-class row))))
      ((not (admitted? (ownership-layer row) ownership-layers))
       (ownership-violation
         (quote invalid-layer)
         (list (ownership-key row) (ownership-layer row))))
      ((not (admitted? (ownership-status row) ownership-statuses))
       (ownership-violation
         (quote invalid-status)
         (list (ownership-key row) (ownership-status row))))
      ((not (member? (ownership-policy row) (quote (yes no))))
       (ownership-violation
         (quote invalid-policy-candidate)
         (list (ownership-key row) (ownership-policy row))))
      (t (ownership-ok)))))

(def ownership-row-pairing-verdict
  (lambda (row)
    (let ((previous-missing (dash? (ownership-previous-owner row)))
          (migration-missing (dash? (ownership-migration-ref row))))
      (cond
        ((and previous-missing migration-missing) (ownership-ok))
        ((and (not previous-missing) (not migration-missing))
         (cond
           ((hex40? (ownership-migration-ref row)) (ownership-ok))
           (t
            (ownership-violation
              (quote invalid-migration-ref)
              (ownership-key row)))))
        (t
         (ownership-violation
           (quote unpaired-previous-owner-migration-ref)
           (ownership-key row)))))))

(def ownership-row-evidence-verdict
  (lambda (row check-paths)
    (let ((implementation
            (path-items (ownership-implementation-paths row)))
          (evidence
            (path-items (ownership-evidence-paths row))))
      (cond
        ((and
           (eq (ownership-status row) (quote confirmed))
           (atom evidence))
         (ownership-violation
           (quote confirmed-ownership-missing-evidence)
           (ownership-key row)))
        (check-paths
         (let ((implementation-verdict
                 (paths-present-verdict implementation (ownership-key row))))
           (cond
             ((ownership-ok? implementation-verdict)
              (paths-present-verdict evidence (ownership-key row)))
             (t implementation-verdict))))
        (t (ownership-ok))))))

(def migration-row-verdict
  (lambda (row check-paths)
    (cond
      ((not (admitted? (migration-status row) ownership-statuses))
       (ownership-violation
         (quote invalid-migration-status)
         (list (migration-key row) (migration-status row))))
      ((and
         (eq (migration-status row) (quote confirmed))
         (not (hex40? (migration-commit row))))
       (ownership-violation
         (quote confirmed-migration-invalid-sha)
         (migration-key row)))
      (t
       (let ((evidence (path-items (migration-evidence-paths row))))
         (cond
           ((and
              (eq (migration-status row) (quote confirmed))
              (atom evidence))
            (ownership-violation
              (quote confirmed-migration-missing-evidence)
              (migration-key row)))
           (check-paths
            (paths-present-verdict evidence (migration-key row)))
           (t (ownership-ok))))))))

(def validate-ownership-rows
  (lambda (rows seen-keys seen-semantic check-paths)
    (cond
      ((atom rows) (ownership-ok))
      (t
       (let* ((row (car rows))
              (shape (ownership-row-shape-verdict row)))
         (cond
           ((not (ownership-ok? shape)) shape)
           ((member? (ownership-key row) seen-keys)
            (ownership-violation
              (quote duplicate-key)
              (ownership-key row)))
           ((and
              (not (dash? (ownership-semantic-id row)))
              (member? (ownership-semantic-id row) seen-semantic))
            (ownership-violation
              (quote duplicate-semantic-id)
              (ownership-semantic-id row)))
           (t
            (let ((enum-verdict (ownership-row-enum-verdict row)))
              (cond
                ((not (ownership-ok? enum-verdict)) enum-verdict)
                (t
                 (let ((pairing-verdict
                         (ownership-row-pairing-verdict row)))
                   (cond
                     ((not (ownership-ok? pairing-verdict))
                      pairing-verdict)
                     (t
                      (let ((evidence-verdict
                              (ownership-row-evidence-verdict row check-paths)))
                        (cond
                          ((not (ownership-ok? evidence-verdict))
                           evidence-verdict)
                          (t
                           (validate-ownership-rows
                             (cdr rows)
                             (cons (ownership-key row) seen-keys)
                             (cond
                               ((dash? (ownership-semantic-id row))
                                seen-semantic)
                               (t
                                (cons
                                  (ownership-semantic-id row)
                                  seen-semantic)))
                             check-paths))))))))))))))))))

(def collect-keys
  (lambda (rows)
    (cond
      ((atom rows) (quote ()))
      (t (cons (row-key (car rows)) (collect-keys (cdr rows)))))))

(def validate-migration-rows
  (lambda (rows seen-keys check-paths)
    (cond
      ((atom rows) (ownership-ok))
      (t
       (let* ((row (car rows))
              (shape (migration-row-shape-verdict row)))
         (cond
           ((not (ownership-ok? shape)) shape)
           ((member? (migration-key row) seen-keys)
            (ownership-violation
              (quote duplicate-key)
              (migration-key row)))
           (t
            (let ((row-verdict (migration-row-verdict row check-paths)))
              (cond
                ((not (ownership-ok? row-verdict)) row-verdict)
                (t
                 (validate-migration-rows
                   (cdr rows)
                   (cons (migration-key row) seen-keys)
                   check-paths)))))))))))

(def meta-unresolved-required
  (lambda (forms out)
    (cond
      ((atom forms) (reverse out))
      ((meta-row? (car forms))
       (let ((row (car forms)))
         (cond
           ((not (equal? (length row) 8))
            (list
              (list
                (quote malformed-meta-eval-row)
                (cond ((> (length row) 1) (nth 1 row)) (t (quote ?))))))
           ((and
              (eq (nth 2 row) (quote yes))
              (not (eq (nth 3 row) (quote confirmed))))
            (meta-unresolved-required
              (cdr forms)
              (cons (list (nth 1 row) (nth 3 row)) out)))
           (t (meta-unresolved-required (cdr forms) out)))))
      (t (meta-unresolved-required (cdr forms) out)))))

(def find-ownership-key
  (lambda (key rows)
    (cond
      ((atom rows) (quote ()))
      ((eq key (ownership-key (car rows))) (car rows))
      (t (find-ownership-key key (cdr rows))))))

(def cross-evidence-verdict
  (lambda (ownership meta-forms)
    (let ((meta-owner (find-ownership-key (quote meta-evaluator) ownership)))
      (cond
        ((atom meta-owner) (ownership-ok))
        ((not (eq (ownership-status meta-owner) (quote confirmed)))
         (ownership-ok))
        (t
         (let ((unresolved
                 (meta-unresolved-required meta-forms (quote ()))))
           (cond
             ((atom unresolved) (ownership-ok))
             ((eq (car (car unresolved)) (quote malformed-meta-eval-row))
              (ownership-violation
                (quote malformed-meta-eval-row)
                (car unresolved)))
             (t
              (ownership-violation
                (quote unresolved-required-meta-evidence)
                unresolved)))))))))

(def validate-ownership-inventory
  (lambda (forms meta-forms check-paths)
    (let* ((ownership (collect-tagged forms ownership-row?))
           (migrations (collect-tagged forms migration-row?)))
      (cond
        ((atom ownership)
         (ownership-violation (quote empty-ownership-inventory) (quote ())))
        (t
         (let ((ownership-verdict
                 (validate-ownership-rows
                   ownership
                   (quote ())
                   (quote ())
                   check-paths)))
           (cond
             ((not (ownership-ok? ownership-verdict))
              ownership-verdict)
             (t
              (let ((migration-verdict
                      (validate-migration-rows
                        migrations
                        (collect-keys ownership)
                        check-paths)))
                (cond
                  ((not (ownership-ok? migration-verdict))
                   migration-verdict)
                  (t
                   (cross-evidence-verdict ownership meta-forms))))))))))))

; ---------- deterministic report ----------

(def row-key-text
  (lambda (row)
    (token-text (row-key row))))

(def insert-row-sorted-onto
  (lambda (row before after)
    (cond
      ((atom after) (reverse-onto before (list row)))
      ((string<? (row-key-text row) (row-key-text (car after)))
       (reverse-onto before (cons row after)))
      (t
       (insert-row-sorted-onto
         row
         (cons (car after) before)
         (cdr after))))))

(def insert-row-sorted
  (lambda (row sorted)
    (insert-row-sorted-onto row (quote ()) sorted)))

(def sort-rows-onto
  (lambda (rows sorted)
    (cond
      ((atom rows) sorted)
      (t
       (sort-rows-onto
         (cdr rows)
         (insert-row-sorted (car rows) sorted))))))

(def sort-rows
  (lambda (rows)
    (sort-rows-onto rows (quote ()))))

(def count-owner-attr
  (lambda (rows accessor wanted count)
    (cond
      ((atom rows) count)
      ((eq (accessor (car rows)) wanted)
       (count-owner-attr (cdr rows) accessor wanted (+ count 1)))
      (t
       (count-owner-attr (cdr rows) accessor wanted count)))))

(def render-count-table-rows
  (lambda (categories rows accessor)
    (cond
      ((atom categories) "")
      (t
       (let* ((category (car categories))
              (count (count-owner-attr rows accessor category 0)))
         (str+
           (cond
             ((equal? count 0) "")
             (t
              (str+
                "| `" (token-text category) "` | "
                (number->string count)
                " |\n")))
           (render-count-table-rows
             (cdr categories)
             rows
             accessor)))))))

(def render-count-table
  (lambda (categories rows accessor)
    (str+
      "| категорія | аудитовані рядки |\n"
      "|---|---:|\n"
      (render-count-table-rows categories rows accessor))))

(def select-ownership
  (lambda (rows predicate out)
    (cond
      ((atom rows) (reverse out))
      ((predicate (car rows))
       (select-ownership (cdr rows) predicate (cons (car rows) out)))
      (t (select-ownership (cdr rows) predicate out)))))

(def select-migrations
  (lambda (rows predicate out)
    (cond
      ((atom rows) (reverse out))
      ((predicate (car rows))
       (select-migrations (cdr rows) predicate (cons (car rows) out)))
      (t (select-migrations (cdr rows) predicate out)))))

(def ownership-confirmed?
  (lambda (row)
    (eq (ownership-status row) (quote confirmed))))

(def migration-confirmed?
  (lambda (row)
    (eq (migration-status row) (quote confirmed))))

(def migration-host-to-lisp?
  (lambda (row)
    (and
      (migration-confirmed? row)
      (eq (migration-to-owner row) (quote lisp-owned))
      (not (eq (migration-from-owner row) (quote lisp-owned))))))

(def ownership-host-policy-candidate?
  (lambda (row)
    (and
      (eq (ownership-class row) (quote host-mechanism))
      (eq (ownership-policy row) (quote yes)))))

(def ownership-legitimate-host?
  (lambda (row)
    (and
      (eq (ownership-status row) (quote confirmed))
      (eq (ownership-policy row) (quote no))
      (member?
        (ownership-class row)
        (quote (host-observation host-authorization host-mechanism))))))

(def ownership-unknown?
  (lambda (row)
    (eq (ownership-status row) (quote unknown))))

(def render-host-policy
  (lambda (rows)
    (cond
      ((atom rows) "- немає\n")
      (t
       (str+
         "- `" (token-text (ownership-key (car rows))) "` — "
         (ownership-behavior (car rows))
         " (`" (token-text (ownership-status (car rows))) "`)\n"
         (render-host-policy (cdr rows)))))))

(def render-migrations
  (lambda (rows)
    (cond
      ((atom rows) "- немає\n")
      (t
       (str+
         "- `" (token-text (migration-key (car rows))) "` — `"
         (token-text (migration-from-owner (car rows))) "` → `"
         (token-text (migration-to-owner (car rows))) "` у `"
         (token-text (migration-commit (car rows))) "`: "
         (migration-behavior (car rows))
         "\n"
         (render-migrations (cdr rows)))))))

(def render-ownership-rows
  (lambda (rows)
    (cond
      ((atom rows) "")
      (t
       (let ((row (car rows)))
         (str+
           "| `" (token-text (ownership-key row)) "` | `"
           (cond
             ((dash? (ownership-semantic-id row)) "—")
             (t (token-text (ownership-semantic-id row))))
           "` | `" (token-text (ownership-class row))
           "` | `" (token-text (ownership-layer row))
           "` | `" (token-text (ownership-status row))
           "` | " (ownership-behavior row) " |\n"
           (render-ownership-rows (cdr rows)))))))

(def render-semantic-ownership-report
  (lambda (ownership migrations)
    (let* ((confirmed-ownership
             (select-ownership ownership ownership-confirmed? (quote ())))
           (confirmed-migrations
             (select-migrations migrations migration-confirmed? (quote ())))
           (host-to-lisp
             (select-migrations migrations migration-host-to-lisp? (quote ())))
           (host-policy
             (sort-rows
               (select-ownership
                 ownership
                 ownership-host-policy-candidate?
                 (quote ()))))
           (legitimate-host
             (select-ownership ownership ownership-legitimate-host? (quote ())))
           (unknown
             (select-ownership ownership ownership-unknown? (quote ())))
           (sorted-ownership (sort-rows ownership))
           (sorted-migrations (sort-rows confirmed-migrations)))
      (str+
        "# Звіт про семантичну власність\n\n"
        "> Згенеровано детерміновано з `knowledge/semantic-ownership.lisp`.\n"
        "> Звіт рахує **аудитовані поведінки/відповідальності**, а не LOC і не повноту всієї мови.\n"
        "> Жодне число нижче не є «відсотком self-hosting».\n\n"
        "## Підсумок\n\n"
        "- Аудитованих ownership rows: **" (number->string (length ownership)) "**\n"
        "- Підтверджених ownership rows: **" (number->string (length confirmed-ownership)) "**\n"
        "- Часткових ownership rows: **"
        (number->string
          (count-owner-attr ownership ownership-status (quote partial) 0))
        "**\n"
        "- Підтверджених host/Rust→Lisp semantic migrations: **"
        (number->string (length host-to-lisp))
        "**\n"
        "- Підтверджених записів migration ledger загалом: **"
        (number->string (length confirmed-migrations))
        "**\n"
        "- Залишкових host semantic-policy candidates: **"
        (number->string (length host-policy))
        "**\n"
        "- Підтверджених host mechanism/observation/authorization rows, не позначених policy candidate: **"
        (number->string (length legitimate-host))
        "**\n"
        "- Ownership rows зі статусом unknown: **"
        (number->string (length unknown))
        "**\n\n"
        "## Класи власності\n\n"
        (render-count-table ownership-classes-sorted ownership ownership-class)
        "\n"
        "## Шари\n\n"
        (render-count-table ownership-layers-sorted ownership ownership-layer)
        "\n"
        "## Епістемічний статус\n\n"
        (render-count-table ownership-statuses-sorted ownership ownership-status)
        "\n"
        "## Кандидати на перевірку host-policy ownership\n\n"
        (render-host-policy host-policy)
        "\n"
        "## Підтверджений журнал міграцій\n\n"
        (render-migrations sorted-migrations)
        "\n"
        "## Аудитовані поведінки\n\n"
        "| key | semantic id | owner | layer | status | поведінка |\n"
        "|---|---|---|---|---|---|\n"
        (render-ownership-rows sorted-ownership)
        "\n"
        "## Правило інтерпретації\n\n"
        "Знаменник кожного числа — лише checked-in аудитований інвентар вище. "
        "Більша кількість `lisp-owned` сама по собі не є прогресом, а host-owned "
        "observation чи authorization boundary сама по собі не є боргом. Зміна ownership "
        "є прогресом лише тоді, коли вона прибирає дубльовану семантичну владу або "
        "переносить policy до шару, який може нею володіти без послаблення evidence.\n"))))

; ---------- pure adversarial witnesses ----------

(def sample-ownership
  (lambda (key sid owner-class layer status policy evidence previous migration)
    (list
      (quote ownership)
      key
      sid
      owner-class
      layer
      status
      policy
      "sample behavior"
      "-"
      evidence
      previous
      migration)))

(def sample-migration
  (lambda (key status commit evidence)
    (list
      (quote migration)
      key
      (quote host-mechanism)
      (quote lisp-owned)
      status
      commit
      "sample migration"
      evidence)))

(def sample-meta-confirmed
  (list
    (quote row)
    (quote sample-meta)
    (quote yes)
    (quote confirmed)
    "a" "b" "c" "d"))

(def sample-meta-unresolved
  (list
    (quote row)
    (quote sample-meta)
    (quote yes)
    (quote partial)
    "a" "b" "c" "d"))

(def sample-good-sha "0123456789abcdef0123456789abcdef01234567")

(def semantic-ownership-assert
  (lambda (actual expected)
    (cond
      ((equal? actual expected)
       (list (quote semantic-ownership-selftest-ok)))
      (t
       (let ((shown
               (print
                 (list
                   (quote semantic-ownership-selftest-failed)
                   actual
                   expected))))
         (car (quote ())))))))

(semantic-ownership-assert
  (validate-ownership-inventory
    (list
      (sample-ownership
        (quote a) "00000001" (quote lisp-owned) (quote stdlib)
        (quote confirmed) (quote no) "README.md" (quote -) (quote -)))
    (list sample-meta-confirmed)
    (quote ()))
  (ownership-ok))

(semantic-ownership-assert
  (validate-ownership-inventory
    (list
      (sample-ownership
        (quote a) "00000001" (quote lisp-owned) (quote stdlib)
        (quote confirmed) (quote no) "README.md" (quote -) (quote -))
      (sample-ownership
        (quote b) "00000001" (quote lisp-owned) (quote stdlib)
        (quote confirmed) (quote no) "README.md" (quote -) (quote -)))
    (list sample-meta-confirmed)
    (quote ()))
  (ownership-violation (quote duplicate-semantic-id) "00000001"))

(semantic-ownership-assert
  (validate-ownership-inventory
    (list
      (sample-ownership
        (quote a) "00000001" (quote impossible-class) (quote stdlib)
        (quote confirmed) (quote no) "README.md" (quote -) (quote -)))
    (list sample-meta-confirmed)
    (quote ()))
  (ownership-violation
    (quote invalid-owner-class)
    (list (quote a) (quote impossible-class))))

(semantic-ownership-assert
  (validate-ownership-inventory
    (list
      (sample-ownership
        (quote a) "00000001" (quote lisp-owned) (quote impossible-layer)
        (quote confirmed) (quote no) "README.md" (quote -) (quote -)))
    (list sample-meta-confirmed)
    (quote ()))
  (ownership-violation
    (quote invalid-layer)
    (list (quote a) (quote impossible-layer))))

(semantic-ownership-assert
  (validate-ownership-inventory
    (list
      (sample-ownership
        (quote a) "00000001" (quote lisp-owned) (quote stdlib)
        (quote impossible-status) (quote no) "README.md" (quote -) (quote -)))
    (list sample-meta-confirmed)
    (quote ()))
  (ownership-violation
    (quote invalid-status)
    (list (quote a) (quote impossible-status))))

(semantic-ownership-assert
  (validate-ownership-inventory
    (list
      (sample-ownership
        (quote a) "00000001" (quote lisp-owned) (quote stdlib)
        (quote confirmed) (quote no) "-" (quote -) (quote -)))
    (list sample-meta-confirmed)
    (quote ()))
  (ownership-violation
    (quote confirmed-ownership-missing-evidence)
    (quote a)))

(semantic-ownership-assert
  (validate-ownership-inventory
    (list
      (sample-ownership
        (quote a) "00000001" (quote lisp-owned) (quote stdlib)
        (quote confirmed) (quote no) "README.md"
        (quote host-mechanism) "not-a-full-sha"))
    (list sample-meta-confirmed)
    (quote ()))
  (ownership-violation (quote invalid-migration-ref) (quote a)))

(semantic-ownership-assert
  (validate-ownership-inventory
    (list
      (sample-ownership
        (quote meta-evaluator) "00000001" (quote lisp-owned) (quote self-hosting)
        (quote confirmed) (quote no) "README.md" (quote -) (quote -)))
    (list sample-meta-unresolved)
    (quote ()))
  (ownership-violation
    (quote unresolved-required-meta-evidence)
    (list (list (quote sample-meta) (quote partial)))))

; ---------- live repository ----------

(def live-forms
  (read-all (read-file "knowledge/semantic-ownership.lisp")))

(def live-meta-forms
  (read-all (read-file "knowledge/meta-eval-evidence.lisp")))

(def live-ownership
  (collect-tagged live-forms ownership-row?))

(def live-migrations
  (collect-tagged live-forms migration-row?))

(def live-verdict
  (validate-ownership-inventory live-forms live-meta-forms t))

(cond
  ((ownership-ok? live-verdict)
   (let* ((generated
            (render-semantic-ownership-report
              live-ownership
              live-migrations))
          (report-path "docs/semantic-ownership-report.md"))
     (cond
       ((and
          (not (atom *argv*))
          (equal? (car *argv*) "--write"))
        (write-file report-path generated)
        (print
          (str+
            "semantic ownership: "
            (number->string (length live-ownership))
            " rows, "
            (number->string (length live-migrations))
            " migrations, report written")))
       (t
        (let ((current (read-file report-path)))
          (cond
            ((equal? current generated)
             (print
               (str+
                 "semantic ownership: "
                 (number->string (length live-ownership))
                 " rows, "
                 (number->string (length live-migrations))
                 " migrations, report synchronized")))
            (t
             (let ((shown
                     (print
                       (ownership-violation
                         (quote report-drift)
                         "docs/semantic-ownership-report.md"))))
               (car (quote ())))))))))
  (t
   (let ((shown (print live-verdict)))
     (car (quote ())))))
