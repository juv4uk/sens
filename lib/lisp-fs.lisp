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

(00001001 fs-objects 00000101)
(00001001 fs-bindings 00101111)
(00001001 fs-revision 00110000)

(00001001 fs-empty
  (00001000 ()
    (00100111 (empty-content-store) map-empty 0)))

(00001001 fs-root-address
  (00001000 (fs)
    (knowledge-content-address
      (00100111 (00000001 wsm-fs-root)
            (fs-bindings fs)))))

; fs-write returns (new-fs content-address). The caller chooses whether to
; retain the old root, enabling immutable branching and rollback.
; fs-write повертає (new-fs content-address); викликач сам вирішує, чи
; зберігати старий корінь, тому branching і rollback лишаються можливими.
(00001001 fs-write
  (00001000 (fs name value)
    (10011100 ((address (knowledge-content-address value)))
      (00100111
        (00100111
          (content-store-put (fs-objects fs) value)
          (01101110 name address (fs-bindings fs))
          (00001100 1 (fs-revision fs)))
        address))))

; fs-read returns (found value address) or (not-found name).
; fs-read повертає (found value address) або (not-found name).
(00001001 fs-read
  (00001000 (fs name)
    (10011100 ((binding (01101101 name (fs-bindings fs))))
      (00000111
        ((00000010 binding) () (00100111 (00000001 not-found) name))
        ((00000010 binding)  (00100111 (00000001 not-found) name))
        (t
          (10011100 ((address (00000101 binding)))
            (00000111
              ((00100001 (content-store-contains? (fs-objects fs) address))
               (00100111 (00000001 not-found) name))
              (t
                ; map-get is a maybe-list, so unwrap exactly once. This
                ; preserves a legitimately stored nil value.
                ; map-get повертає maybe-список, тому знімаємо рівно одну
                ; оболонку й не втрачаємо законно збережений nil.
                (00100111 (00000001 found)
                      (00000101 (content-store-get (fs-objects fs) address))
                      address)))))))))

(00001001 fs-list
  (00001000 (fs)
    (01110000 (fs-bindings fs))))

(00001001 fs-contains?
  (00001000 (fs name)
    (10110001 (00000010 (01101101 name (fs-bindings fs))))))

; Versioned data-only envelopes. They are ordinary alists and are never
; evaluated by the filesystem layer.
; Версіоновані data-only оболонки є звичайними alist і ніколи не виконуються.
(00001001 *fs-format-version* (00000001 (0 1)))

(00001001 fs-object-package
  (00001000 (value)
    (00100111
      (00000100 (00000001 format) (00000001 wsm-fs-object))
      (00000100 (00000001 version) *fs-format-version*)
      (00000100 (00000001 address) (knowledge-content-address value))
      (00000100 (00000001 value) value))))

(00001001 fs-root-package
  (00001000 (fs)
    (00100111
      (00000100 (00000001 format) (00000001 wsm-fs-root))
      (00000100 (00000001 version) *fs-format-version*)
      (00000100 (00000001 revision) (fs-revision fs))
      (00000100 (00000001 bindings) (01110000 (fs-bindings fs)))
      (00000100 (00000001 objects) (fs-object-addresses (01110000 (fs-objects fs)))))))

(00001001 fs-object-addresses
  (00001000 (entries)
    (00000111
      ((00000010 entries) () (00000001 ()))
      ((00000010 entries)  (00000001 ()))
      (t (00000100 (00000101 (00000101 entries))
               (fs-object-addresses (00000110 entries)))))))

(00001001 fs-package-field
  (00001000 (name package)
    (10011100 ((entry (00101101 name package)))
      (00000111 ((00000010 entry) () (00000001 ()))
            ((00000010 entry)  (00000001 ())) (t (00000110 entry))))))

(00001001 fs-object-package-decision
  (00001000 (package)
    (00000111
      ((00000010 package) () (00100111 (00000001 rejected) (00000001 invalid-package)))
      ((00000010 package)  (00100111 (00000001 rejected) (00000001 invalid-package)))
      ((00100001 (00000011 (fs-package-field (00000001 format) package) (00000001 wsm-fs-object)))
       (00100111 (00000001 rejected) (00000001 invalid-format)))
      ((00100001 (00100010 (fs-package-field (00000001 version) package) *fs-format-version*))
       (00100111 (00000001 rejected) (00000001 unsupported-version)))
      ((00100001 (00100010 (fs-package-field (00000001 address) package)
                    (knowledge-content-address (fs-package-field (00000001 value) package))))
       (00100111 (00000001 rejected) (00000001 address-mismatch)))
      (t (00100111 (00000001 accepted) (fs-package-field (00000001 value) package))))))

(00001001 fs-serialize-object
  (00001000 (value)
    (01001100 (fs-object-package value))))

(00001001 fs-deserialize-object
  (00001000 (text)
    (fs-object-package-decision (01001010 text))))

(00001001 fs-root-package-decision
  (00001000 (package)
    (00000111
      ((00000010 package) () (00100111 (00000001 rejected) (00000001 invalid-package)))
      ((00000010 package)  (00100111 (00000001 rejected) (00000001 invalid-package)))
      ((00100001 (00000011 (fs-package-field (00000001 format) package) (00000001 wsm-fs-root)))
       (00100111 (00000001 rejected) (00000001 invalid-format)))
      ((00100001 (00100010 (fs-package-field (00000001 version) package) *fs-format-version*))
       (00100111 (00000001 rejected) (00000001 unsupported-version)))
      ((00000011 (fs-package-field (00000001 revision) package) (00000001 ()))
       (00100111 (00000001 rejected) (00000001 invalid-revision)))
      ((00100001 (knowledge-proper-list? (fs-package-field (00000001 bindings) package)))
       (00100111 (00000001 rejected) (00000001 invalid-bindings)))
      ((00100001 (knowledge-proper-list? (fs-package-field (00000001 objects) package)))
       (00100111 (00000001 rejected) (00000001 invalid-objects)))
      (t (00100111 (00000001 accepted) package)))))

(00001001 fs-serialize-root
  (00001000 (fs)
    (01001100 (fs-root-package fs))))

(00001001 fs-deserialize-root
  (00001000 (text)
    (fs-root-package-decision (01001010 text))))

; Rebuild an in-memory snapshot from data-only envelopes. No envelope is
; evaluated. Missing referenced objects are rejected before a snapshot is
; returned, so reconstruction is atomic from the caller's perspective.
; Відновлює snapshot із data-only оболонок. Жодна оболонка не виконується.
; Відсутні object-и відхиляються до повернення snapshot, тому реконструкція
; атомарна з погляду викликачa.
(00001001 fs-build-object-store
  (00001000 (packages store)
    (00000111
      ((00000010 packages) () (00100111 (00000001 accepted) store))
      ((00000010 packages)  (00100111 (00000001 accepted) store))
      (t
        (10011100 ((decision (fs-object-package-decision (00000101 packages))))
          (00000111
            ((00100001 (00000011 (00000101 decision) (00000001 accepted))) decision)
            (t (fs-build-object-store
                 (00000110 packages)
                 (content-store-put store (00101111 decision))))))))))

(00001001 fs-all-addresses-present?
  (00001000 (addresses store)
    (00000111
      ((00000010 addresses) () t)
      ((00000010 addresses) (1) t)
      ((00100001 (content-store-contains? store (00000101 addresses))) (00000001 ()))
      (t (fs-all-addresses-present? (00000110 addresses) store)))))

(00001001 fs-binding-addresses-present?
  (00001000 (entries store)
    (00000111
      ((00000010 entries) () t)
      ((00000010 entries) (1) t)
      ((00100001 (content-store-contains? store (00000110 (00000101 entries)))) (00000001 ()))
      (t (fs-binding-addresses-present? (00000110 entries) store)))))

(00001001 fs-reconstruct-root
  (00001000 (root-package object-packages)
    (10011100 ((root-decision (fs-root-package-decision root-package)))
      (00000111
        ((00100001 (00000011 (00000101 root-decision) (00000001 accepted))) root-decision)
        (t
          (10011100 ((objects-decision
                  (fs-build-object-store object-packages (empty-content-store))))
            (00000111
              ((00100001 (00000011 (00000101 objects-decision) (00000001 accepted))) objects-decision)
              ((00100001 (fs-all-addresses-present?
                      (fs-package-field (00000001 objects) root-package)
                      (00101111 objects-decision)))
               (00100111 (00000001 rejected) (00000001 missing-object)))
              ((00100001 (fs-binding-addresses-present?
                      (fs-package-field (00000001 bindings) root-package)
                      (00101111 objects-decision)))
               (00100111 (00000001 rejected) (00000001 missing-object)))
              (t
                (00100111
                  (00000001 accepted)
                  (00100111
                    (00101111 objects-decision)
                    (10011100 ((bindings (fs-package-field (00000001 bindings) root-package)))
                      (fs-bindings-from-list bindings map-empty))
                    (fs-package-field (00000001 revision) root-package)))))))))))

(00001001 fs-bindings-from-list
  (00001000 (entries bindings)
    (00000111
      ((00000010 entries) () bindings)
      ((00000010 entries) (1) bindings)
      (t (fs-bindings-from-list
           (00000110 entries)
           (01101110 (00000101 (00000101 entries)) (00000110 (00000101 entries)) bindings))))))

; F3 journal records are data-only append-only events.  Replay starts from
; fs-empty and returns either (accepted fs) or (rejected reason); unknown or
; malformed events never become partial state.
; Журнал F3 — це лише data-only події append-only. Replay починається з
; fs-empty і повертає (accepted fs) або (rejected reason); невідомі чи
; пошкоджені події не стають частковим станом.
(00001001 *fs-journal-version* (00000001 (0 1)))

(00001001 fs-journal-event
  (00001000 (op fields)
    (00000100
      (00000100 (00000001 format) (00000001 wsm-fs-event))
      (00000100
        (00000100 (00000001 version) *fs-journal-version*)
        (00000100 (00000100 (00000001 op) op) fields)))))

(00001001 fs-journal-write-event
  (00001000 (name value)
    (fs-journal-event
      (00000001 write)
      (00100111 (00000100 (00000001 name) name) (00000100 (00000001 value) value)))))

(00001001 fs-journal-bind-event
  (00001000 (name address)
    (fs-journal-event
      (00000001 bind)
      (00100111 (00000100 (00000001 name) name) (00000100 (00000001 address) address)))))

(00001001 fs-journal-unbind-event
  (00001000 (name)
    (fs-journal-event (00000001 unbind) (00100111 (00000100 (00000001 name) name)))))

(00001001 fs-journal-root-commit-event
  (00001000 (root-package)
    (fs-journal-event
      (00000001 root-commit)
      (00100111 (00000100 (00000001 root) root-package)))))

(00001001 fs-journal-append
  (00001000 (journal event)
    (00101001 journal (00100111 event))))

(00001001 fs-journal-event-decision
  (00001000 (event)
    (00000111
      ((00000010 event) () (00100111 (00000001 rejected) (00000001 invalid-event)))
      ((00000010 event)  (00100111 (00000001 rejected) (00000001 invalid-event)))
      ((00100001 (00000011 (fs-package-field (00000001 format) event) (00000001 wsm-fs-event)))
       (00100111 (00000001 rejected) (00000001 invalid-format)))
      ((00100001 (00100010 (fs-package-field (00000001 version) event) *fs-journal-version*))
       (00100111 (00000001 rejected) (00000001 unsupported-version)))
      ((00000011 (fs-package-field (00000001 op) event) (00000001 ()))
       (00100111 (00000001 rejected) (00000001 missing-operation)))
      ((10011010 (00000011 (fs-package-field (00000001 op) event) (00000001 write))
            (10011011 (00100001 (10110001 (00000010 (00101101 (00000001 name) event))))
                (00100001 (10110001 (00000010 (00101101 (00000001 value) event))))))
       (00100111 (00000001 rejected) (00000001 incomplete-write)))
      ((10011010 (00000011 (fs-package-field (00000001 op) event) (00000001 bind))
            (10011011 (00100001 (10110001 (00000010 (00101101 (00000001 name) event))))
                (00100001 (10110001 (00000010 (00101101 (00000001 address) event))))))
       (00100111 (00000001 rejected) (00000001 incomplete-bind)))
      ((10011010 (00000011 (fs-package-field (00000001 op) event) (00000001 unbind))
            (00100001 (10110001 (00000010 (00101101 (00000001 name) event)))))
       (00100111 (00000001 rejected) (00000001 incomplete-unbind)))
      ((10011010 (00000011 (fs-package-field (00000001 op) event) (00000001 root-commit))
            (00100001 (10110001 (00000010 (00101101 (00000001 root) event)))))
       (00100111 (00000001 rejected) (00000001 incomplete-root-commit)))
      (t (00100111 (00000001 accepted) event)))))

(00001001 fs-bindings-without
  (00001000 (entries name result)
    (00000111
      ((00000010 entries) () result)
      ((00000010 entries) (1) result)
      ((00100010 (00000101 (00000101 entries)) name)
       (fs-bindings-without (00000110 entries) name result))
      (t
        (fs-bindings-without
          (00000110 entries)
          name
          (01101110 (00000101 (00000101 entries)) (00000110 (00000101 entries)) result))))))

(00001001 fs-unbind
  (00001000 (fs name)
    (00100111
      (fs-objects fs)
      (fs-bindings-without (01110000 (fs-bindings fs)) name map-empty)
      (00001100 1 (fs-revision fs)))))

(00001001 fs-journal-replay-event
  (00001000 (fs event)
    (10011100 ((decision (fs-journal-event-decision event)))
      (00000111
        ((00100001 (00000011 (00000101 decision) (00000001 accepted))) decision)
        (t
          (10011100 ((op (fs-package-field (00000001 op) event)))
            (00000111
              ((00000011 op (00000001 write))
               (10011100 ((written (fs-write fs
                                        (fs-package-field (00000001 name) event)
                                        (fs-package-field (00000001 value) event))))
                 (00100111 (00000001 accepted) (00000101 written))))
              ((00000011 op (00000001 bind))
               (10011100 ((address (fs-package-field (00000001 address) event)))
                 (00000111
                   ((00100001 (content-store-contains? (fs-objects fs) address))
                    (00100111 (00000001 rejected) (00000001 missing-object)))
                   (t
                     (00100111
                       (00000001 accepted)
                       (00100111
                         (fs-objects fs)
                         (01101110 (fs-package-field (00000001 name) event)
                                     address
                                     (fs-bindings fs))
                         (00001100 1 (fs-revision fs))))))))
              ((00000011 op (00000001 unbind))
               (00100111 (00000001 accepted)
                     (fs-unbind fs (fs-package-field (00000001 name) event))))
              ((00000011 op (00000001 root-commit))
               (00000111
                 ((00100010 (fs-root-package fs)
                          (fs-package-field (00000001 root) event))
                  (00100111 (00000001 accepted) fs))
                 (t (00100111 (00000001 rejected) (00000001 root-mismatch)))))
              (t (00100111 (00000001 rejected) (00000001 unknown-event))))))))))

(00001001 fs-journal-replay-onto
  (00001000 (journal fs)
    (00000111
      ((00000010 journal) () (00100111 (00000001 accepted) fs))
      ((00000010 journal)  (00100111 (00000001 accepted) fs))
      (t
        (10011100 ((decision (fs-journal-replay-event fs (00000101 journal))))
          (00000111
            ((00100001 (00000011 (00000101 decision) (00000001 accepted))) decision)
            (t (fs-journal-replay-onto (00000110 journal) (00101111 decision)))))))))

(00001001 fs-journal-replay
  (00001000 (journal)
    (fs-journal-replay-onto journal (fs-empty))))

(00001001 fs-serialize-journal
  (00001000 (journal)
    (01001100 journal)))

(00001001 fs-deserialize-journal
  (00001000 (text)
    (fs-journal-replay (01001010 text))))

; F4 commit boundary model. Objects and journal may be written first, but a
; snapshot becomes visible only when the root-pointer stage completes.
; Модель межі commit F4. Objects і journal можна записати раніше, але
; snapshot стає видимим лише після завершення root-pointer.
(00001001 fs-commit-stage?
  (00001000 (stage)
    (00000111
      ((00000011 stage (00000001 objects)) t)
      ((00000011 stage (00000001 journal)) t)
      ((00000011 stage (00000001 root-pointer)) t)
      (t (00000001 ())))))

(00001001 fs-recover-commit
  (00001000 (old-fs new-fs completed-stage)
    (00000111
      ((00100001 (fs-commit-stage? completed-stage))
       (00100111 (00000001 rejected) (00000001 unknown-commit-stage)))
      ((00000011 completed-stage (00000001 root-pointer))
       (00100111 (00000001 recovered) new-fs))
      (t (00100111 (00000001 recovered) old-fs)))))

(00001001 fs-recover-root-package
  (00001000 (old-package candidate-package completed-stage)
    (00000111
      ((00100001 (00000011 completed-stage (00000001 root-pointer)))
       (00100111 (00000001 recovered) old-package))
      (t
        (10011100 ((decision (fs-root-package-decision candidate-package)))
          (00000111
            ((00000011 (00000101 decision) (00000001 accepted))
             (00100111 (00000001 recovered) candidate-package))
            (t (00100111 (00000001 recovered) old-package (00000001 rejected-candidate)))))))))
