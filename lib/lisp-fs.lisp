; Experimental immutable filesystem-shaped store for WSM.
; This is a model of file objects and roots, not a disk driver or POSIX FS.
;
; Експериментальне незмінне сховище у формі файлової системи для WSM.
; Це модель об'єктів і коренів, а не драйвер диска та не POSIX-файлова система.
;
; A filesystem snapshot is (fs objects bindings revision). Objects are kept
; in the existing content-addressed store; bindings map names to addresses.
; Every write returns a new snapshot and its address. The previous snapshot
; is never mutated. Missing names return (not-found name), never bare nil.
;
; Snapshot: (fs objects bindings revision). Об'єкти живуть у наявному
; content-store; bindings зіставляє імена з адресами. Кожен запис повертає
; новий snapshot і адресу, попередній не змінюється. Відсутнє ім'я дає
; (not-found name), а не голий nil.

(def fs-objects car)
(def fs-bindings second)
(def fs-revision third)

(def fs-empty
  (lambda ()
    (list (empty-content-store) map-empty 0)))

(def fs-root-address
  (lambda (fs)
    (knowledge-content-address
      (list (quote wsm-fs-root)
            (fs-bindings fs)))))

; fs-write returns (new-fs content-address). The caller chooses whether to
; retain the old root, enabling immutable branching and rollback.
; fs-write повертає (new-fs content-address); викликач сам вирішує, чи
; зберігати старий корінь, тому branching і rollback лишаються можливими.
(def fs-write
  (lambda (fs name value)
    (let ((address (knowledge-content-address value)))
      (list
        (list
          (content-store-put (fs-objects fs) value)
          (map-insert name address (fs-bindings fs))
          (+ 1 (fs-revision fs)))
        address))))

; fs-read returns (found value address) or (not-found name).
; fs-read повертає (found value address) або (not-found name).
(def fs-read
  (lambda (fs name)
    (let ((binding (map-get name (fs-bindings fs))))
      (cond
        ((atom? binding) (list (quote not-found) name))
        (t
          (let ((address (car binding)))
            (cond
              ((not? (content-store-contains? (fs-objects fs) address))
               (list (quote not-found) name))
              (t
                ; map-get is a maybe-list, so unwrap exactly once. This
                ; preserves a legitimately stored nil value.
                ; map-get повертає maybe-список, тому знімаємо рівно одну
                ; оболонку й не втрачаємо законно збережений nil.
                (list (quote found)
                      (car (content-store-get (fs-objects fs) address))
                      address)))))))))

(def fs-list
  (lambda (fs)
    (map->list (fs-bindings fs))))

(def fs-contains?
  (lambda (fs name)
    (not? (atom? (map-get name (fs-bindings fs))))))

; Versioned data-only envelopes. They are ordinary alists and are never
; evaluated by the filesystem layer.
; Версіоновані data-only оболонки є звичайними alist і ніколи не виконуються.
(def *fs-format-version* (quote (0 1)))

(def fs-object-package
  (lambda (value)
    (list
      (cons (quote format) (quote wsm-fs-object))
      (cons (quote version) *fs-format-version*)
      (cons (quote address) (knowledge-content-address value))
      (cons (quote value) value))))

(def fs-root-package
  (lambda (fs)
    (list
      (cons (quote format) (quote wsm-fs-root))
      (cons (quote version) *fs-format-version*)
      (cons (quote revision) (fs-revision fs))
      (cons (quote bindings) (map->list (fs-bindings fs)))
      (cons (quote objects) (fs-object-addresses (map->list (fs-objects fs)))))))

(def fs-object-addresses
  (lambda (entries)
    (cond
      ((atom? entries) (quote ()))
      (t (cons (car (car entries))
               (fs-object-addresses (cdr entries)))))))

(def fs-package-field
  (lambda (name package)
    (let ((entry (assoc name package)))
      (cond ((atom? entry) (quote ())) (t (cdr entry))))))

(def fs-object-package-decision
  (lambda (package)
    (cond
      ((atom? package) (list (quote rejected) (quote invalid-package)))
      ((not? (eq? (fs-package-field (quote format) package) (quote wsm-fs-object)))
       (list (quote rejected) (quote invalid-format)))
      ((not? (equal? (fs-package-field (quote version) package) *fs-format-version*))
       (list (quote rejected) (quote unsupported-version)))
      ((not? (equal? (fs-package-field (quote address) package)
                    (knowledge-content-address (fs-package-field (quote value) package))))
       (list (quote rejected) (quote address-mismatch)))
      (t (list (quote accepted) (fs-package-field (quote value) package))))))

(def fs-serialize-object
  (lambda (value)
    (write-to-string (fs-object-package value))))

(def fs-deserialize-object
  (lambda (text)
    (fs-object-package-decision (read text))))

(def fs-root-package-decision
  (lambda (package)
    (cond
      ((atom? package) (list (quote rejected) (quote invalid-package)))
      ((not? (eq? (fs-package-field (quote format) package) (quote wsm-fs-root)))
       (list (quote rejected) (quote invalid-format)))
      ((not? (equal? (fs-package-field (quote version) package) *fs-format-version*))
       (list (quote rejected) (quote unsupported-version)))
      ((eq? (fs-package-field (quote revision) package) (quote ()))
       (list (quote rejected) (quote invalid-revision)))
      ((not? (knowledge-proper-list? (fs-package-field (quote bindings) package)))
       (list (quote rejected) (quote invalid-bindings)))
      ((not? (knowledge-proper-list? (fs-package-field (quote objects) package)))
       (list (quote rejected) (quote invalid-objects)))
      (t (list (quote accepted) package)))))

(def fs-serialize-root
  (lambda (fs)
    (write-to-string (fs-root-package fs))))

(def fs-deserialize-root
  (lambda (text)
    (fs-root-package-decision (read text))))

; Rebuild an in-memory snapshot from data-only envelopes. No envelope is
; evaluated. Missing referenced objects are rejected before a snapshot is
; returned, so reconstruction is atomic from the caller's perspective.
; Відновлює snapshot із data-only оболонок. Жодна оболонка не виконується.
; Відсутні object-и відхиляються до повернення snapshot, тому реконструкція
; атомарна з погляду викликачa.
(def fs-build-object-store
  (lambda (packages store)
    (cond
      ((atom? packages) (list (quote accepted) store))
      (t
        (let ((decision (fs-object-package-decision (car packages))))
          (cond
            ((not? (eq? (car decision) (quote accepted))) decision)
            (t (fs-build-object-store
                 (cdr packages)
                 (content-store-put store (second decision))))))))))

(def fs-all-addresses-present?
  (lambda (addresses store)
    (cond
      ((atom? addresses) t)
      ((not? (content-store-contains? store (car addresses))) (quote ()))
      (t (fs-all-addresses-present? (cdr addresses) store)))))

(def fs-binding-addresses-present?
  (lambda (entries store)
    (cond
      ((atom? entries) t)
      ((not? (content-store-contains? store (cdr (car entries)))) (quote ()))
      (t (fs-binding-addresses-present? (cdr entries) store)))))

(def fs-reconstruct-root
  (lambda (root-package object-packages)
    (let ((root-decision (fs-root-package-decision root-package)))
      (cond
        ((not? (eq? (car root-decision) (quote accepted))) root-decision)
        (t
          (let ((objects-decision
                  (fs-build-object-store object-packages (empty-content-store))))
            (cond
              ((not? (eq? (car objects-decision) (quote accepted))) objects-decision)
              ((not? (fs-all-addresses-present?
                      (fs-package-field (quote objects) root-package)
                      (second objects-decision)))
               (list (quote rejected) (quote missing-object)))
              ((not? (fs-binding-addresses-present?
                      (fs-package-field (quote bindings) root-package)
                      (second objects-decision)))
               (list (quote rejected) (quote missing-object)))
              (t
                (list
                  (quote accepted)
                  (list
                    (second objects-decision)
                    (let ((bindings (fs-package-field (quote bindings) root-package)))
                      (fs-bindings-from-list bindings map-empty))
                    (fs-package-field (quote revision) root-package)))))))))))

(def fs-bindings-from-list
  (lambda (entries bindings)
    (cond
      ((atom? entries) bindings)
      (t (fs-bindings-from-list
           (cdr entries)
           (map-insert (car (car entries)) (cdr (car entries)) bindings))))))

; F3 journal records are data-only append-only events.  Replay starts from
; fs-empty and returns either (accepted fs) or (rejected reason); unknown or
; malformed events never become partial state.
; Журнал F3 — це лише data-only події append-only. Replay починається з
; fs-empty і повертає (accepted fs) або (rejected reason); невідомі чи
; пошкоджені події не стають частковим станом.
(def *fs-journal-version* (quote (0 1)))

(def fs-journal-event
  (lambda (op fields)
    (cons
      (cons (quote format) (quote wsm-fs-event))
      (cons
        (cons (quote version) *fs-journal-version*)
        (cons (cons (quote op) op) fields)))))

(def fs-journal-write-event
  (lambda (name value)
    (fs-journal-event
      (quote write)
      (list (cons (quote name) name) (cons (quote value) value)))))

(def fs-journal-bind-event
  (lambda (name address)
    (fs-journal-event
      (quote bind)
      (list (cons (quote name) name) (cons (quote address) address)))))

(def fs-journal-unbind-event
  (lambda (name)
    (fs-journal-event (quote unbind) (list (cons (quote name) name)))))

(def fs-journal-root-commit-event
  (lambda (root-package)
    (fs-journal-event
      (quote root-commit)
      (list (cons (quote root) root-package)))))

(def fs-journal-append
  (lambda (journal event)
    (append journal (list event))))

(def fs-journal-event-decision
  (lambda (event)
    (cond
      ((atom? event) (list (quote rejected) (quote invalid-event)))
      ((not? (eq? (fs-package-field (quote format) event) (quote wsm-fs-event)))
       (list (quote rejected) (quote invalid-format)))
      ((not? (equal? (fs-package-field (quote version) event) *fs-journal-version*))
       (list (quote rejected) (quote unsupported-version)))
      ((eq? (fs-package-field (quote op) event) (quote ()))
       (list (quote rejected) (quote missing-operation)))
      ((and (eq? (fs-package-field (quote op) event) (quote write))
            (or (atom? (assoc (quote name) event))
                (atom? (assoc (quote value) event))))
       (list (quote rejected) (quote incomplete-write)))
      ((and (eq? (fs-package-field (quote op) event) (quote bind))
            (or (atom? (assoc (quote name) event))
                (atom? (assoc (quote address) event))))
       (list (quote rejected) (quote incomplete-bind)))
      ((and (eq? (fs-package-field (quote op) event) (quote unbind))
            (atom? (assoc (quote name) event)))
       (list (quote rejected) (quote incomplete-unbind)))
      ((and (eq? (fs-package-field (quote op) event) (quote root-commit))
            (atom? (assoc (quote root) event)))
       (list (quote rejected) (quote incomplete-root-commit)))
      (t (list (quote accepted) event)))))

(def fs-bindings-without
  (lambda (entries name result)
    (cond
      ((atom? entries) result)
      ((equal? (car (car entries)) name)
       (fs-bindings-without (cdr entries) name result))
      (t
        (fs-bindings-without
          (cdr entries)
          name
          (map-insert (car (car entries)) (cdr (car entries)) result))))))

(def fs-unbind
  (lambda (fs name)
    (list
      (fs-objects fs)
      (fs-bindings-without (map->list (fs-bindings fs)) name map-empty)
      (+ 1 (fs-revision fs)))))

(def fs-journal-replay-event
  (lambda (fs event)
    (let ((decision (fs-journal-event-decision event)))
      (cond
        ((not? (eq? (car decision) (quote accepted))) decision)
        (t
          (let ((op (fs-package-field (quote op) event)))
            (cond
              ((eq? op (quote write))
               (let ((written (fs-write fs
                                        (fs-package-field (quote name) event)
                                        (fs-package-field (quote value) event))))
                 (list (quote accepted) (car written))))
              ((eq? op (quote bind))
               (let ((address (fs-package-field (quote address) event)))
                 (cond
                   ((not? (content-store-contains? (fs-objects fs) address))
                    (list (quote rejected) (quote missing-object)))
                   (t
                     (list
                       (quote accepted)
                       (list
                         (fs-objects fs)
                         (map-insert (fs-package-field (quote name) event)
                                     address
                                     (fs-bindings fs))
                         (+ 1 (fs-revision fs))))))))
              ((eq? op (quote unbind))
               (list (quote accepted)
                     (fs-unbind fs (fs-package-field (quote name) event))))
              ((eq? op (quote root-commit))
               (cond
                 ((equal? (fs-root-package fs)
                          (fs-package-field (quote root) event))
                  (list (quote accepted) fs))
                 (t (list (quote rejected) (quote root-mismatch)))))
              (t (list (quote rejected) (quote unknown-event))))))))))

(def fs-journal-replay-onto
  (lambda (journal fs)
    (cond
      ((atom? journal) (list (quote accepted) fs))
      (t
        (let ((decision (fs-journal-replay-event fs (car journal))))
          (cond
            ((not? (eq? (car decision) (quote accepted))) decision)
            (t (fs-journal-replay-onto (cdr journal) (second decision)))))))))

(def fs-journal-replay
  (lambda (journal)
    (fs-journal-replay-onto journal (fs-empty))))

(def fs-serialize-journal
  (lambda (journal)
    (write-to-string journal)))

(def fs-deserialize-journal
  (lambda (text)
    (fs-journal-replay (read text))))

; F4 commit boundary model. Objects and journal may be written first, but a
; snapshot becomes visible only when the root-pointer stage completes.
; Модель межі commit F4. Objects і journal можна записати раніше, але
; snapshot стає видимим лише після завершення root-pointer.
(def fs-commit-stage?
  (lambda (stage)
    (cond
      ((eq? stage (quote objects)) t)
      ((eq? stage (quote journal)) t)
      ((eq? stage (quote root-pointer)) t)
      (t (quote ())))))

(def fs-recover-commit
  (lambda (old-fs new-fs completed-stage)
    (cond
      ((not? (fs-commit-stage? completed-stage))
       (list (quote rejected) (quote unknown-commit-stage)))
      ((eq? completed-stage (quote root-pointer))
       (list (quote recovered) new-fs))
      (t (list (quote recovered) old-fs)))))

(def fs-recover-root-package
  (lambda (old-package candidate-package completed-stage)
    (cond
      ((not? (eq? completed-stage (quote root-pointer)))
       (list (quote recovered) old-package))
      (t
        (let ((decision (fs-root-package-decision candidate-package)))
          (cond
            ((eq? (car decision) (quote accepted))
             (list (quote recovered) candidate-package))
            (t (list (quote recovered) old-package (quote rejected-candidate)))))))))
