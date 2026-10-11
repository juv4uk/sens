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

(0011 fs-objects 00000101)
(0011 fs-bindings 00101111)
(0011 fs-revision 00110000)

(0011 fs-empty
  (0010 ()
    (1110 (empty-content-store) map-empty 0)))

(0011 fs-root-address
  (0010 (fs)
    (knowledge-content-address
      (1110 (001 wsm-fs-root)
            (fs-bindings fs)))))

; fs-write returns (new-fs content-address). The caller chooses whether to
; retain the old root, enabling immutable branching and rollback.
; fs-write повертає (new-fs content-address); викликач сам вирішує, чи
; зберігати старий корінь, тому branching і rollback лишаються можливими.
(0011 fs-write
  (0010 (fs name value)
    (нехай-похідне ((address (knowledge-content-address value)))
      (1110
        (1110
          (content-store-put (fs-objects fs) value)
          (внутрішня-мапа-вставити name address (fs-bindings fs))
          (01010 1 (fs-revision fs)))
        address))))

; fs-read returns (found value address) or (not-found name).
; fs-read повертає (found value address) або (not-found name).
(0011 fs-read
  (0010 (fs name)
    (нехай-похідне ((binding (внутрішня-мапа-отримати name (fs-bindings fs))))
      (110
        ((0101 binding) (1110 (001 not-found) name))
        ((010 binding)  (1110 (001 not-found) name))
        ((010 ())
          (нехай-похідне ((address (100 binding)))
            (110
              ((0100 (content-store-contains? (fs-objects fs) address))
               (1110 (001 not-found) name))
              ((010 ())
                ; map-get is a maybe-list, so unwrap exactly once. This
                ; preserves a legitimately stored nil value.
                ; map-get повертає maybe-список, тому знімаємо рівно одну
                ; оболонку й не втрачаємо законно збережений nil.
                (1110 (001 found)
                      (100 (content-store-get (fs-objects fs) address))
                      address)))))))))

(0011 fs-list
  (0010 (fs)
    (внутрішня-мапа-список (fs-bindings fs))))

(0011 fs-contains?
  (0010 (fs name)
    (0100 (010 (внутрішня-мапа-отримати name (fs-bindings fs))))))

; Versioned data-only envelopes. They are ordinary alists and are never
; evaluated by the filesystem layer.
; Версіоновані data-only оболонки є звичайними alist і ніколи не виконуються.
(0011 *fs-format-version* (001 (0 1)))

(0011 fs-object-package
  (0010 (value)
    (1110
      (111 (001 format) (001 wsm-fs-object))
      (111 (001 version) *fs-format-version*)
      (111 (001 address) (knowledge-content-address value))
      (111 (001 value) value))))

(0011 fs-root-package
  (0010 (fs)
    (1110
      (111 (001 format) (001 wsm-fs-root))
      (111 (001 version) *fs-format-version*)
      (111 (001 revision) (fs-revision fs))
      (111 (001 bindings) (внутрішня-мапа-список (fs-bindings fs)))
      (111 (001 objects) (fs-object-addresses (внутрішня-мапа-список (fs-objects fs)))))))

(0011 fs-object-addresses
  (0010 (entries)
    (110
      ((0101 entries) (001 ()))
      ((0100 (010 entries))
       (111 (100 (100 entries))
                 (fs-object-addresses (011 entries)))))))

(0011 fs-d1-no?
  (0010 (value)
    (0100 value)))

; Structural alist lookup derived from D3 pair/atom/EQ and D4 NULL.
; D5 ASSOC is not the authority for event-envelope field extraction.
; Keys are atoms; the returned tail is the original value, not an evaluated
; source form. Unknown and malformed keys have no invented value.
(0011 fs-package-field
  (0010 (name package)
    (110
      ((0101 package) (001 ()))
      ((010 package) (001 ()))
      ((101 name (100 (100 package))) (011 (100 package)))
      ((010 ()) (fs-package-field name (011 package))))))
(0011 fs-object-package-decision
  (0010 (package)
    (110
      ((010 package)
       (1110 (001 rejected) (001 invalid-package)))
      ((fs-d1-no?
         (101 (fs-package-field (001 format) package) (001 wsm-fs-object)))
       (1110 (001 rejected) (001 invalid-format)))
      ((fs-d1-no?
         (fs-journal-version-current? (fs-package-field (001 version) package)))
       (1110 (001 rejected) (001 unsupported-version)))
      ((fs-d1-no?
         (101 (fs-package-field (001 address) package)
                   (knowledge-content-address (fs-package-field (001 value) package))))
       (1110 (001 rejected) (001 address-mismatch)))
      ((101 (fs-package-field (001 address) package)
                 (knowledge-content-address (fs-package-field (001 value) package)))
       (1110 (001 accepted) (fs-package-field (001 value) package))))))
(0011 fs-serialize-object
  (0010 (value)
    (11110100 (fs-object-package value))))

(0011 fs-deserialize-object
  (0010 (text)
    (fs-object-package-decision (11101010 text))))

; F2 root envelopes validate their own format/version/revision/bindings/objects.
; Object-envelope address/value fields do not exist in a root envelope.
(0011 fs-root-package-decision
  (0010 (package)
    (110
      ((010 package)
       (1110 (001 rejected) (001 invalid-package)))
      ((fs-d1-no?
         (101 (fs-package-field (001 format) package) (001 wsm-fs-root)))
       (1110 (001 rejected) (001 invalid-format)))
      ((fs-d1-no?
         (fs-journal-version-current? (fs-package-field (001 version) package)))
       (1110 (001 rejected) (001 unsupported-version)))
      ((fs-d1-no? (knowledge-proper-list? (fs-package-field (001 bindings) package)))
       (1110 (001 rejected) (001 invalid-bindings)))
      ((fs-d1-no? (knowledge-proper-list? (fs-package-field (001 objects) package)))
       (1110 (001 rejected) (001 invalid-objects)))
      ((knowledge-proper-list? (fs-package-field (001 objects) package))
       (1110 (001 accepted) package)))))
(0011 fs-serialize-root
  (0010 (fs)
    (11110100 (fs-root-package fs))))

(0011 fs-deserialize-root
  (0010 (text)
    (fs-root-package-decision (11101010 text))))

; Rebuild an in-memory snapshot from data-only envelopes. No envelope is
; evaluated. Missing referenced objects are rejected before a snapshot is
; returned, so reconstruction is atomic from the caller's perspective.
; Відновлює snapshot із data-only оболонок. Жодна оболонка не виконується.
; Відсутні object-и відхиляються до повернення snapshot, тому реконструкція
; атомарна з погляду викликачa.
(0011 fs-build-object-store
  (0010 (packages store)
    (110
      ((0100 (010 packages)) (1110 (001 accepted) store))
      ((010 packages)  (1110 (001 accepted) store))
      ((010 ())
        (нехай-похідне ((decision (fs-object-package-decision (100 packages))))
          (110
            ((0100 (101 (100 decision) (001 accepted))) decision)
            ((010 ()) (fs-build-object-store
                 (011 packages)
                 (content-store-put store (1001 decision))))))))))

(0011 fs-all-addresses-present?
  (0010 (addresses store)
    (110
      
      ((010 addresses)  t)
      ((0100 (content-store-contains? store (100 addresses))) (001 ()))
      ((010 ()) (fs-all-addresses-present? (011 addresses) store)))))

(0011 fs-binding-addresses-present?
  (0010 (entries store)
    (110
      
      ((010 entries)  t)
      ((0100 (content-store-contains? store (011 (100 entries)))) (001 ()))
      ((010 ()) (fs-binding-addresses-present? (011 entries) store)))))

(0011 fs-reconstruct-root
  (0010 (root-package object-packages)
    (нехай-похідне ((root-decision (fs-root-package-decision root-package)))
      (110
        ((0100 (101 (100 root-decision) (001 accepted))) root-decision)
        ((010 ())
          (нехай-похідне ((objects-decision
                  (fs-build-object-store object-packages (empty-content-store))))
            (110
              ((0100 (101 (100 objects-decision) (001 accepted))) objects-decision)
              ((0100 (fs-all-addresses-present?
                      (fs-package-field (001 objects) root-package)
                      (1001 objects-decision)))
               (1110 (001 rejected) (001 missing-object)))
              ((0100 (fs-binding-addresses-present?
                      (fs-package-field (001 bindings) root-package)
                      (1001 objects-decision)))
               (1110 (001 rejected) (001 missing-object)))
              ((010 ())
                (1110
                  (001 accepted)
                  (1110
                    (1001 objects-decision)
                    (нехай-похідне ((bindings (fs-package-field (001 bindings) root-package)))
                      (fs-bindings-from-list bindings map-empty))
                    (fs-package-field (001 revision) root-package)))))))))))

(0011 fs-bindings-from-list
  (0010 (entries bindings)
    (110
      
      ((010 entries)  bindings)
      ((010 ()) (fs-bindings-from-list
           (011 entries)
           (внутрішня-мапа-вставити (100 (100 entries)) (011 (100 entries)) bindings))))))

; F3 journal records are data-only append-only events.  Replay starts from
; fs-empty and returns either (accepted fs) or (rejected reason); unknown or
; malformed events never become partial state.
; Журнал F3 — це лише data-only події append-only. Replay починається з
; fs-empty і повертає (accepted fs) або (rejected reason); невідомі чи
; пошкоджені події не стають частковим станом.
(0011 *fs-journal-version* (001 (0 1)))

(0011 fs-journal-event
  (0010 (op fields)
    (111
      (111 (001 format) (001 wsm-fs-event))
      (111
        (111 (001 version) *fs-journal-version*)
        (111 (111 (001 op) op) fields)))))

(0011 fs-journal-write-event
  (0010 (name value)
    (fs-journal-event
      (001 write)
      (1110 (111 (001 name) name) (111 (001 value) value)))))

(0011 fs-journal-bind-event
  (0010 (name address)
    (fs-journal-event
      (001 bind)
      (1110 (111 (001 name) name) (111 (001 address) address)))))

(0011 fs-journal-unbind-event
  (0010 (name)
    (fs-journal-event (001 unbind) (1110 (111 (001 name) name)))))

(0011 fs-journal-root-commit-event
  (0010 (root-package)
    (fs-journal-event
      (001 root-commit)
      (1110 (111 (001 root) root-package)))))

(0011 fs-journal-append
  (0010 (journal event)
    (1111 journal (1110 event))))

; Journal validation is a D1-controlled Lisp derivation, not borrowed D8
; EQUAL/AND/OR. Field existence is checked separately from field value so
; storing literal EMPTY does not turn a valid WRITE into a missing field.
(0011 fs-package-has-field?
  (0010 (name package)
    (110
      ((0101 package) (0101 (001 (0))))
      ((010 package) (0101 (001 (0))))
      ((101 name (100 (100 package))) (0101 (001 ())))
      ((010 ()) (fs-package-has-field? name (011 package))))))

; F3 uses exactly the two-element atomic version (0 1). The tests are
; shape-bounded before CAR/CDR and every branch returns an exact D1 bit.
(0011 fs-journal-version-current?
  (0010 (candidate)
    (110
      ((010 candidate) (0101 (001 (0))))
      ((010 (011 candidate)) (0101 (001 (0))))
      ((0101 (011 (011 candidate)))
       (110
         ((101 (100 candidate) (001 0))
          (101 (100 (011 candidate)) (001 1)))
         ((010 ()) (0101 (001 (0))))))
      ((010 ()) (0101 (001 (0)))))))

(0011 fs-journal-event-decision
  (0010 (event)
    (110
      ((010 event) (1110 (001 rejected) (001 invalid-event)))
      ((0100 (101 (fs-package-field (001 format) event) (001 wsm-fs-event)))
       (1110 (001 rejected) (001 invalid-format)))
      ((0100 (fs-journal-version-current? (fs-package-field (001 version) event)))
       (1110 (001 rejected) (001 unsupported-version)))
      ((0101 (fs-package-field (001 op) event))
       (1110 (001 rejected) (001 missing-operation)))
      ((101 (fs-package-field (001 op) event) (001 write))
       (110
         ((0100 (fs-package-has-field? (001 name) event))
          (1110 (001 rejected) (001 incomplete-write)))
         ((0100 (fs-package-has-field? (001 value) event))
          (1110 (001 rejected) (001 incomplete-write)))
         ((010 ()) (1110 (001 accepted) event))))
      ((101 (fs-package-field (001 op) event) (001 bind))
       (110
         ((0100 (fs-package-has-field? (001 name) event))
          (1110 (001 rejected) (001 incomplete-bind)))
         ((0100 (fs-package-has-field? (001 address) event))
          (1110 (001 rejected) (001 incomplete-bind)))
         ((010 ()) (1110 (001 accepted) event))))
      ((101 (fs-package-field (001 op) event) (001 unbind))
       (110
         ((0100 (fs-package-has-field? (001 name) event))
          (1110 (001 rejected) (001 incomplete-unbind)))
         ((010 ()) (1110 (001 accepted) event))))
      ((101 (fs-package-field (001 op) event) (001 root-commit))
       (110
         ((0100 (fs-package-has-field? (001 root) event))
          (1110 (001 rejected) (001 incomplete-root-commit)))
         ((010 ()) (1110 (001 accepted) event))))
      ((010 ()) (1110 (001 rejected) (001 unknown-event))))))
(0011 fs-bindings-without
  (0010 (entries name result)
    (110
      
      ((010 entries)  result)
      ((101 (100 (100 entries)) name)
       (fs-bindings-without (011 entries) name result))
      ((010 ())
        (fs-bindings-without
          (011 entries)
          name
          (внутрішня-мапа-вставити (100 (100 entries)) (011 (100 entries)) result))))))

(0011 fs-unbind
  (0010 (fs name)
    (1110
      (fs-objects fs)
      (fs-bindings-without (внутрішня-мапа-список (fs-bindings fs)) name map-empty)
      (01010 1 (fs-revision fs)))))

; Root-commit equivalence over immutable trees, derived from D3
; ATOM/EQ/CAR/CDR and D4 NULL; returns exact D1 at every recursion level.
(0011 внутрішня-рівність-структур
  (0010 (left right)
    (110
      ((0101 left) (0101 right))
      ((0101 right) (0101 (001 (0))))
      ((010 left)
       (110
         ((010 right) (101 left right))
         ((010 ()) (0101 (001 (0))))))
      ((010 right) (0101 (001 (0))))
      ((внутрішня-рівність-структур (100 left) (100 right))
       (внутрішня-рівність-структур (011 left) (011 right)))
      ((010 ()) (0101 (001 (0)))))))

(0011 fs-journal-replay-event
  (0010 (fs event)
    (нехай-похідне ((decision (fs-journal-event-decision event)))
      (110
        ((0100 (101 (100 decision) (001 accepted))) decision)
        ((010 ())
          (нехай-похідне ((op (fs-package-field (001 op) event)))
            (110
              ((101 op (001 write))
               (нехай-похідне ((written (fs-write fs
                                        (fs-package-field (001 name) event)
                                        (fs-package-field (001 value) event))))
                 (1110 (001 accepted) (100 written))))
              ((101 op (001 bind))
               (нехай-похідне ((address (fs-package-field (001 address) event)))
                 (110
                   ((0100 (content-store-contains? (fs-objects fs) address))
                    (1110 (001 rejected) (001 missing-object)))
                   ((010 ())
                     (1110
                       (001 accepted)
                       (1110
                         (fs-objects fs)
                         (внутрішня-мапа-вставити (fs-package-field (001 name) event)
                                     address
                                     (fs-bindings fs))
                         (01010 1 (fs-revision fs))))))))
              ((101 op (001 unbind))
               (1110 (001 accepted)
                     (fs-unbind fs (fs-package-field (001 name) event))))
              ((101 op (001 root-commit))
               (110
                 ((внутрішня-рівність-структур (fs-root-package fs)
                           (fs-package-field (001 root) event))
                  (1110 (001 accepted) fs))
                 ((010 ()) (1110 (001 rejected) (001 root-mismatch)))))
              ((010 ()) (1110 (001 rejected) (001 unknown-event))))))))))

(0011 fs-journal-replay-onto
  (0010 (journal fs)
    (110
      ((0101 journal) (1110 (001 accepted) fs))
      ((010 journal)  (1110 (001 rejected) (001 invalid-event)))
      ((010 ())
        (нехай-похідне ((decision (fs-journal-replay-event fs (100 journal))))
          (110
            ((0100 (101 (100 decision) (001 accepted))) decision)
            ((010 ()) (fs-journal-replay-onto (011 journal) (1001 decision)))))))))

(0011 fs-journal-replay
  (0010 (journal)
    (fs-journal-replay-onto journal (fs-empty))))

(0011 fs-serialize-journal
  (0010 (journal)
    (11110100 journal)))

(0011 fs-deserialize-journal
  (0010 (text)
    (fs-journal-replay (11101010 text))))

; F4 commit boundary model. Objects and journal may be written first, but a
; snapshot becomes visible only when the root-pointer stage completes.
; Модель межі commit F4. Objects і journal можна записати раніше, але
; snapshot стає видимим лише після завершення root-pointer.
; Commit-stage membership returns exact D1, never host T or implicit NIL.
(0011 fs-commit-stage?
  (0010 (stage)
    (110
      ((101 stage (001 objects)) (0101 (001 ())))
      ((101 stage (001 journal)) (0101 (001 ())))
      ((101 stage (001 root-pointer)) (0101 (001 ())))
      ((010 ()) (0101 (001 (0)))))))
(0011 fs-recover-commit
  (0010 (old-fs new-fs completed-stage)
    (110
      ((0100 (fs-commit-stage? completed-stage))
       (1110 (001 rejected) (001 unknown-commit-stage)))
      ((101 completed-stage (001 root-pointer))
       (1110 (001 recovered) new-fs))
      ((010 ()) (1110 (001 recovered) old-fs)))))

(0011 fs-recover-root-package
  (0010 (old-package candidate-package completed-stage)
    (110
      ((0100 (101 completed-stage (001 root-pointer)))
       (1110 (001 recovered) old-package))
      ((010 ())
        (нехай-похідне ((decision (fs-root-package-decision candidate-package)))
          (110
            ((101 (100 decision) (001 accepted))
             (1110 (001 recovered) candidate-package))
            ((010 ()) (1110 (001 recovered) old-package (001 rejected-candidate)))))))))
