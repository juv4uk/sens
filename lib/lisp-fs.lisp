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

; Міграція трьох селекторів: точна ширина є семантичною адресою.
; W8:00000101/00101111/00110000 — лише архівне походження;
; чинний закон: D3:100 CAR, D4:1001 CADR, D5:10011 CADDR.
; Функції є похідними SENS-LAMBDA, без історичного byte dispatch.
(визначити фс-об'єкти
  (функція (fs) (перше fs)))
(визначити фс-зв'язки
  (функція (fs) (друге fs)))
(визначити фс-ревізія
  (функція (fs) (третє fs)))

(визначити фс-порожній
  (функція ()
    (список (порожній-вміст-сховище) мапа-порожній 0)))

(визначити фс-корінь-адреса
  (функція (fs)
    (знання-вміст-адреса
      (список (як-є wsm-fs-root)
            (фс-зв'язки fs)))))

; fs-write returns (new-fs content-address). The caller chooses whether to
; retain the old root, enabling immutable branching and rollback.
; fs-write повертає (new-fs content-address); викликач сам вирішує, чи
; зберігати старий корінь, тому branching і rollback лишаються можливими.
(визначити фс-записати
  (функція (fs name value)
    (нехай-похідне ((address (знання-вміст-адреса value)))
      (список
        (список
          (вміст-сховище-покласти (фс-об'єкти fs) value)
          (внутрішня-мапа-вставити name address (фс-зв'язки fs))
          (додати-1 (фс-ревізія fs)))
        address))))

; fs-read returns (found value address) or (not-found name).
; fs-read повертає (found value address) або (not-found name).
(визначити фс-читати
  (функція (fs name)
    (нехай-похідне ((binding (внутрішня-мапа-отримати name (фс-зв'язки fs))))
      (за-умовою
        ((порожній? binding) (список (як-є not-found) name))
        ((атом? binding)  (список (як-є not-found) name))
        ((атом? ())
          (нехай-похідне ((address (перше binding)))
            (за-умовою
              ((хибне? (вміст-сховище-містить? (фс-об'єкти fs) address))
               (список (як-є not-found) name))
              ((атом? ())
                ; map-get is a maybe-list, so unwrap exactly once. This
                ; preserves a legitimately stored nil value.
                ; map-get повертає maybe-список, тому знімаємо рівно одну
                ; оболонку й не втрачаємо законно збережений nil.
                (список (як-є found)
                      (перше (вміст-сховище-отримати (фс-об'єкти fs) address))
                      address)))))))))

(визначити фс-список
  (функція (fs)
    (внутрішня-мапа-список (фс-зв'язки fs))))

(визначити фс-містить?
  (функція (fs name)
    (хибне? (атом? (внутрішня-мапа-отримати name (фс-зв'язки fs))))))

; Versioned data-only envelopes. They are ordinary alists and are never
; evaluated by the filesystem layer.
; Версіоновані data-only оболонки є звичайними alist і ніколи не виконуються.
(визначити *fs-format-version* (як-є (ні 1)))

(визначити фс-об'єкт-пакет
  (функція (value)
    (список
      (сполучити (як-є format) (як-є wsm-fs-object))
      (сполучити (як-є version) *fs-format-version*)
      (сполучити (як-є address) (знання-вміст-адреса value))
      (сполучити (як-є value) value))))

(визначити фс-корінь-пакет
  (функція (fs)
    (список
      (сполучити (як-є format) (як-є wsm-fs-root))
      (сполучити (як-є version) *fs-format-version*)
      (сполучити (як-є revision) (фс-ревізія fs))
      (сполучити (як-є bindings) (внутрішня-мапа-список (фс-зв'язки fs)))
      (сполучити (як-є objects) (фс-об'єкт-адреси (внутрішня-мапа-список (фс-об'єкти fs)))))))

(визначити фс-об'єкт-адреси
  (функція (entries)
    (за-умовою
      ((порожній? entries) (як-є ()))
      ((хибне? (атом? entries))
       (сполучити (перше (перше entries))
                 (фс-об'єкт-адреси (решта entries)))))))

(визначити fs-d1-no?
  (функція (value)
    (хибне? value)))

; Structural alist lookup derived from D3 pair/atom/EQ and D4 NULL.
; D5 ASSOC is not the authority for event-envelope field extraction.
; Keys are atoms; the returned tail is the original value, not an evaluated
; source form. Unknown and malformed keys have no invented value.
; Селектори застосовуються лише до перевіреного alist-entry.
; Некоректні записи ніколи не стають читабельними полями, навіть поза
; fs-journal-event-decision. Немає host truth і немає нового D24 механізму.
(визначити fs-package-field
  (функція (name package)
    (за-умовою
      ((порожній? package) (як-є ()))
      ((атом? package) (як-є ()))
      ((атом? (перше package)) (як-є ()))
      ((порожній? (перше (перше package))) (як-є ()))
      ((хибне? (атом? (перше (перше package)))) (як-є ()))
      ((тотожне? name (перше (перше package))) (решта (перше package)))
      (так (фс-пакет-поле name (решта package))))))
(визначити fs-object-package-decision
  (функція (package)
    (за-умовою
      ((атом? package)
       (список (як-є rejected) (як-є invalid-package)))
      ((хибне?
         (тотожне? (фс-пакет-поле (як-є format) package) (як-є wsm-fs-object)))
       (список (як-є rejected) (як-є invalid-format)))
      ((хибне?
         (фс-версія-журналу-чинна? (фс-пакет-поле (як-є version) package)))
       (список (як-є rejected) (як-є unsupported-version)))
      ((хибне?
         (тотожне? (фс-пакет-поле (як-є address) package)
                   (знання-вміст-адреса (фс-пакет-поле (як-є value) package))))
       (список (як-є rejected) (як-є address-mismatch)))
      ((тотожне? (фс-пакет-поле (як-є address) package)
                 (знання-вміст-адреса (фс-пакет-поле (як-є value) package)))
       (список (як-є accepted) (фс-пакет-поле (як-є value) package))))))
(визначити fs-serialize-object
  (функція (value)
    (значення-у-текст (фс-об'єкт-пакет value))))

(визначити fs-deserialize-object
  (функція (text)
    (рішення-щодо-пакета-об'єкта-файлової-системи (прочитати text))))

; F2 root envelopes validate their own format/version/revision/bindings/objects.
; Object-envelope address/value fields do not exist in a root envelope.
; The historical knowledge proper-list checker returns host T and cannot
; control exact D3 COND. Derive a local D1 proper-list law: NIL is proper,
; pair tails recurse, non-NIL atoms are improper.
(визначити внутрішній-правильний-список?
  (функція (value)
    (за-умовою
      ((порожній? value) (порожній? (як-є ())))
      ((атом? value) (порожній? (як-є (ні))))
      ((атом? ()) (внутрішній-правильний-список? (решта value))))))

(визначити fs-root-package-decision
  (функція (package)
    (за-умовою
      ((атом? package)
       (список (як-є rejected) (як-є invalid-package)))
      ((хибне?
         (тотожне? (фс-пакет-поле (як-є format) package) (як-є wsm-fs-root)))
       (список (як-є rejected) (як-є invalid-format)))
      ((хибне?
         (фс-версія-журналу-чинна? (фс-пакет-поле (як-є version) package)))
       (список (як-є rejected) (як-є unsupported-version)))
      ((хибне? (внутрішній-правильний-список? (фс-пакет-поле (як-є bindings) package)))
       (список (як-є rejected) (як-є invalid-bindings)))
      ((хибне? (внутрішній-правильний-список? (фс-пакет-поле (як-є objects) package)))
       (список (як-є rejected) (як-є invalid-objects)))
      ((внутрішній-правильний-список? (фс-пакет-поле (як-є objects) package))
       (список (як-є accepted) package)))))
(визначити fs-serialize-root
  (функція (fs)
    (значення-у-текст (фс-корінь-пакет fs))))

(визначити fs-deserialize-root
  (функція (text)
    (рішення-щодо-кореневого-пакета-файлової-системи (прочитати text))))

; Rebuild an in-memory snapshot from data-only envelopes. No envelope is
; evaluated. Missing referenced objects are rejected before a snapshot is
; returned, so reconstruction is atomic from the caller's perspective.
; Відновлює snapshot із data-only оболонок. Жодна оболонка не виконується.
; Відсутні object-и відхиляються до повернення snapshot, тому реконструкція
; атомарна з погляду викликачa.
; Terminate ONLY at structural NIL. A nonempty proper list must
; validate and insert every package; a non-NIL atom is rejected. The prior
; NOT(ATOM packages) branch silently accepted every nonempty list.
(визначити fs-build-object-store
  (функція (packages store)
    (за-умовою
      ((порожній? packages) (список (як-є accepted) store))
      ((атом? packages) (список (як-є rejected) (як-є invalid-object-packages)))
      ((атом? ())
        (нехай-похідне ((decision (рішення-щодо-пакета-об'єкта-файлової-системи (перше packages))))
          (за-умовою
            ((хибне? (тотожне? (перше decision) (як-є accepted))) decision)
            ((атом? ()) (фс-побудувати-об'єкт-сховище
                 (решта packages)
                 (вміст-сховище-покласти store (друге decision))))))))))

; All-addresses checks are exact D1 folds: NIL returns YES; improper
; tails and missing content return NO. No host T, structural EMPTY, or
; permissive truth coercion may leave these predicates.
(визначити fs-all-addresses-present?
  (функція (addresses store)
    (за-умовою
      ((порожній? addresses) (порожній? (як-є ())))
      ((атом? addresses) (порожній? (як-є (ні))))
      ((хибне? (вміст-сховище-містить? store (перше addresses)))
       (порожній? (як-є (ні))))
      ((атом? ()) (усі-адреси-об'єктів-файлової-системи-наявні? (решта addresses) store)))))

(визначити fs-binding-addresses-present?
  (функція (entries store)
    (за-умовою
      ((порожній? entries) (порожній? (як-є ())))
      ((атом? entries) (порожній? (як-є (ні))))
      ((хибне? (вміст-сховище-містить? store (решта (перше entries))))
       (порожній? (як-є (ні))))
      ((атом? ()) (усі-адреси-зв'язувань-у-файловій-системі-наявні? (решта entries) store)))))

(визначити fs-reconstruct-root
  (функція (root-package object-packages)
    (нехай-похідне ((root-decision (рішення-щодо-кореневого-пакета-файлової-системи root-package)))
      (за-умовою
        ((хибне? (тотожне? (перше root-decision) (як-є accepted))) root-decision)
        ((атом? ())
          (нехай-похідне ((objects-decision
                  (фс-побудувати-об'єкт-сховище object-packages (порожній-вміст-сховище))))
            (за-умовою
              ((хибне? (тотожне? (перше objects-decision) (як-є accepted))) objects-decision)
              ((хибне? (усі-адреси-об'єктів-файлової-системи-наявні?
                      (фс-пакет-поле (як-є objects) root-package)
                      (друге objects-decision)))
               (список (як-є rejected) (як-є missing-object)))
              ((хибне? (усі-адреси-зв'язувань-у-файловій-системі-наявні?
                      (фс-пакет-поле (як-є bindings) root-package)
                      (друге objects-decision)))
               (список (як-є rejected) (як-є missing-object)))
              ((атом? ())
                (список
                  (як-є accepted)
                  (список
                    (друге objects-decision)
                    (нехай-похідне ((bindings (фс-пакет-поле (як-є bindings) root-package)))
                      (фс-зв'язки-з-список bindings мапа-порожній))
                    (фс-пакет-поле (як-є revision) root-package)))))))))))

(визначити fs-bindings-from-list
  (функція (entries bindings)
    (за-умовою
      
      ((атом? entries)  bindings)
      ((атом? ()) (фс-зв'язки-з-список
           (решта entries)
           (внутрішня-мапа-вставити (перше (перше entries)) (решта (перше entries)) bindings))))))

; F3 journal records are data-only append-only events.  Replay starts from
; fs-empty and returns either (accepted fs) or (rejected reason); unknown or
; malformed events never become partial state.
; Журнал F3 — це лише data-only події append-only. Replay починається з
; fs-empty і повертає (accepted fs) або (rejected reason); невідомі чи
; пошкоджені події не стають частковим станом.
(визначити *fs-journal-version* (як-є (ні 1)))

(визначити fs-journal-event
  (функція (op fields)
    (сполучити
      (сполучити (як-є format) (як-є wsm-fs-event))
      (сполучити
        (сполучити (як-є version) *fs-journal-version*)
        (сполучити (сполучити (як-є op) op) fields)))))

(визначити fs-journal-write-event
  (функція (name value)
    (фс-журнал-подія
      (як-є write)
      (список (сполучити (як-є name) name) (сполучити (як-є value) value)))))

(визначити fs-journal-bind-event
  (функція (name address)
    (фс-журнал-подія
      (як-є bind)
      (список (сполучити (як-є name) name) (сполучити (як-є address) address)))))

(визначити fs-journal-unbind-event
  (функція (name)
    (фс-журнал-подія (як-є unbind) (список (сполучити (як-є name) name)))))

(визначити fs-journal-root-commit-event
  (функція (root-package)
    (фс-журнал-подія
      (як-є root-commit)
      (список (сполучити (як-є root) root-package)))))

(визначити fs-journal-append
  (функція (journal event)
    (приєднати journal (список event))))

; Journal validation is a D1-controlled Lisp derivation, not borrowed D8
; EQUAL/AND/OR. Field existence is checked separately from field value so
; storing literal EMPTY does not turn a valid WRITE into a missing field.
; Exact D1:1/0. Не довіряємо nested CAR без перевірки форми.
(визначити фс-пакет-має-поле?
  (функція (name package)
    (за-умовою
      ((порожній? package) ні)
      ((атом? package) ні)
      ((атом? (перше package)) ні)
      ((порожній? (перше (перше package))) ні)
      ((хибне? (атом? (перше (перше package)))) ні)
      ((тотожне? name (перше (перше package))) так)
      (так (фс-пакет-має-поле? name (решта package))))))

; F3 uses exactly the two-element atomic version (0 1). The tests are
; shape-bounded before CAR/CDR and every branch returns an exact D1 bit.
(визначити фс-версія-журналу-чинна?
  (функція (candidate)
    (за-умовою
      ((атом? candidate) (порожній? (як-є (ні))))
      ((атом? (решта candidate)) (порожній? (як-є (ні))))
      ((порожній? (решта (решта candidate)))
       (за-умовою
         ((тотожне? (перше candidate) (як-є 0))
          (тотожне? (перше (решта candidate)) (як-є 1)))
         ((атом? ()) (порожній? (як-є (ні))))))
      ((атом? ()) (порожній? (як-є (ні)))))))

; Структурна форма alist перевіряється ДО селекторів полів.
; Пара (ключ . дані), ключ — непорожній атом, значення може бути EMPTY.
; D1-вердикт належить самому SENS; ратифікації нової координати немає.
(визначити фс-журнал-список-пар?
  (функція (entries)
    (за-умовою
      ((порожній? entries) так)
      ((атом? entries) ні)
      ((атом? (перше entries)) ні)
      ((порожній? (перше (перше entries))) ні)
      ((хибне? (атом? (перше (перше entries)))) ні)
      (так (фс-журнал-список-пар? (решта entries))))))

(визначити рішення-щодо-події-журналу-файлової-системи
  (функція (event)
    (за-умовою
      ; Загальний порожній alist коректний як структура, але не як подія.
      ((порожній? event) (список (як-є rejected) (як-є invalid-event)))
      ((хибне? (фс-журнал-список-пар? event))
       (список (як-є rejected) (як-є invalid-event)))
      ((хибне? (тотожне? (фс-пакет-поле (як-є format) event) (як-є wsm-fs-event)))
       (список (як-є rejected) (як-є invalid-format)))
      ((хибне? (фс-версія-журналу-чинна? (фс-пакет-поле (як-є version) event)))
       (список (як-є rejected) (як-є unsupported-version)))
      ((порожній? (фс-пакет-поле (як-є op) event))
       (список (як-є rejected) (як-є missing-operation)))
      ((тотожне? (фс-пакет-поле (як-є op) event) (як-є write))
       (за-умовою
         ((хибне? (фс-пакет-має-поле? (як-є name) event))
          (список (як-є rejected) (як-є incomplete-write)))
         ((хибне? (фс-пакет-має-поле? (як-є value) event))
          (список (як-є rejected) (як-є incomplete-write)))
         ((атом? ()) (список (як-є accepted) event))))
      ((тотожне? (фс-пакет-поле (як-є op) event) (як-є bind))
       (за-умовою
         ((хибне? (фс-пакет-має-поле? (як-є name) event))
          (список (як-є rejected) (як-є incomplete-bind)))
         ((хибне? (фс-пакет-має-поле? (як-є address) event))
          (список (як-є rejected) (як-є incomplete-bind)))
         ((атом? ()) (список (як-є accepted) event))))
      ((тотожне? (фс-пакет-поле (як-є op) event) (як-є unbind))
       (за-умовою
         ((хибне? (фс-пакет-має-поле? (як-є name) event))
          (список (як-є rejected) (як-є incomplete-unbind)))
         ((атом? ()) (список (як-є accepted) event))))
      ((тотожне? (фс-пакет-поле (як-є op) event) (як-є root-commit))
       (за-умовою
         ((хибне? (фс-пакет-має-поле? (як-є root) event))
          (список (як-є rejected) (як-є incomplete-root-commit)))
         ((атом? ()) (список (як-є accepted) event))))
      ((атом? ()) (список (як-є rejected) (як-є unknown-event))))))
(визначити фс-зв'язки-без-імені
  (функція (entries name result)
    (за-умовою
      
      ((атом? entries)  result)
      ((тотожне? (перше (перше entries)) name)
       (фс-зв'язки-без-імені (решта entries) name result))
      ((атом? ())
        (фс-зв'язки-без-імені
          (решта entries)
          name
          (внутрішня-мапа-вставити (перше (перше entries)) (решта (перше entries)) result))))))

(визначити fs-unbind
  (функція (fs name)
    (список
      (фс-об'єкти fs)
      (фс-зв'язки-без-імені (внутрішня-мапа-список (фс-зв'язки fs)) name мапа-порожній)
      (додати-1 (фс-ревізія fs)))))

; Root-commit equivalence over immutable trees, derived from D3
; ATOM/EQ/CAR/CDR and D4 NULL; returns exact D1 at every recursion level.
(визначити внутрішня-рівність-структур
  (функція (left right)
    (за-умовою
      ((порожній? left) (порожній? right))
      ((порожній? right) (порожній? (як-є (ні))))
      ((атом? left)
       (за-умовою
         ((атом? right) (тотожне? left right))
         ((атом? ()) (порожній? (як-є (ні))))))
      ((атом? right) (порожній? (як-є (ні))))
      ((внутрішня-рівність-структур (перше left) (перше right))
       (внутрішня-рівність-структур (решта left) (решта right)))
      ((атом? ()) (порожній? (як-є (ні)))))))

(визначити фс-журнал-відтворити-подію
  (функція (fs event)
    (нехай-похідне ((decision (рішення-щодо-події-журналу-файлової-системи event)))
      (за-умовою
        ((хибне? (тотожне? (перше decision) (як-є accepted))) decision)
        ((атом? ())
          (нехай-похідне ((op (фс-пакет-поле (як-є op) event)))
            (за-умовою
              ((тотожне? op (як-є write))
               (нехай-похідне ((written (фс-записати fs
                                        (фс-пакет-поле (як-є name) event)
                                        (фс-пакет-поле (як-є value) event))))
                 (список (як-є accepted) (перше written))))
              ((тотожне? op (як-є bind))
               (нехай-похідне ((address (фс-пакет-поле (як-є address) event)))
                 (за-умовою
                   ((хибне? (вміст-сховище-містить? (фс-об'єкти fs) address))
                    (список (як-є rejected) (як-є missing-object)))
                   ((атом? ())
                     (список
                       (як-є accepted)
                       (список
                         (фс-об'єкти fs)
                         (внутрішня-мапа-вставити (фс-пакет-поле (як-є name) event)
                                     address
                                     (фс-зв'язки fs))
                         (додати-1 (фс-ревізія fs))))))))
              ((тотожне? op (як-є unbind))
               (список (як-є accepted)
                     (фс-розв'язати fs (фс-пакет-поле (як-є name) event))))
              ((тотожне? op (як-є root-commit))
               (за-умовою
                 ((внутрішня-рівність-структур (фс-корінь-пакет fs)
                           (фс-пакет-поле (як-є root) event))
                  (список (як-є accepted) fs))
                 ((атом? ()) (список (як-є rejected) (як-є root-mismatch)))))
              ((атом? ()) (список (як-є rejected) (як-є unknown-event))))))))))

(визначити фс-журнал-відтворити-на-стан
  (функція (journal fs)
    (за-умовою
      ((порожній? journal) (список (як-є accepted) fs))
      ((атом? journal)  (список (як-є rejected) (як-є invalid-event)))
      ((атом? ())
        (нехай-похідне ((decision (фс-журнал-відтворити-подію fs (перше journal))))
          (за-умовою
            ((хибне? (тотожне? (перше decision) (як-є accepted))) decision)
            ((атом? ()) (фс-журнал-відтворити-на-стан (решта journal) (друге decision)))))))))

(визначити fs-journal-replay
  (функція (journal)
    (фс-журнал-відтворити-на-стан journal (фс-порожній))))

(визначити fs-serialize-journal
  (функція (journal)
    (значення-у-текст journal)))

(визначити fs-deserialize-journal
  (функція (text)
    (фс-журнал-повторити (прочитати text))))

; F4 commit boundary model. Objects and journal may be written first, but a
; snapshot becomes visible only when the root-pointer stage completes.
; Модель межі commit F4. Objects і journal можна записати раніше, але
; snapshot стає видимим лише після завершення root-pointer.
; Commit-stage membership returns exact D1, never host T or implicit NIL.
(визначити фс-етап-коміту?
  (функція (stage)
    (за-умовою
      ((тотожне? stage (як-є objects)) (порожній? (як-є ())))
      ((тотожне? stage (як-є journal)) (порожній? (як-є ())))
      ((тотожне? stage (як-є root-pointer)) (порожній? (як-є ())))
      ((атом? ()) (порожній? (як-є (ні)))))))
(визначити fs-recover-commit
  (функція (old-fs new-fs completed-stage)
    (за-умовою
      ((хибне? (фс-етап-коміту? completed-stage))
       (список (як-є rejected) (як-є unknown-commit-stage)))
      ((тотожне? completed-stage (як-є root-pointer))
       (список (як-є recovered) new-fs))
      ((атом? ()) (список (як-є recovered) old-fs)))))

(визначити fs-recover-root-package
  (функція (old-package candidate-package completed-stage)
    (за-умовою
      ((хибне? (тотожне? completed-stage (як-є root-pointer)))
       (список (як-є recovered) old-package))
      ((атом? ())
        (нехай-похідне ((decision (рішення-щодо-кореневого-пакета-файлової-системи candidate-package)))
          (за-умовою
            ((тотожне? (перше decision) (як-є accepted))
             (список (як-є recovered) candidate-package))
            ((атом? ()) (список (як-є recovered) old-package (як-є rejected-candidate)))))))))

; Ratified D9 exact-width FS surfaces; donor closures above own semantics.
; The file system here is immutable SENS data, not a host syscall or new opcode.
; D9:001010000
(визначити fs-objects фс-об'єкти)
; D9:010000001
(визначити fs-bindings фс-зв'язки)
; D9:010010101
(визначити fs-revision фс-ревізія)
; D9:001011011
(визначити fs-empty фс-порожній)
; D9:010001100
(визначити fs-root-address фс-корінь-адреса)
; D9:010010110
(визначити fs-list фс-список)
; D9:010100001
(визначити fs-contains? фс-містить?)
; D9:010100010
(визначити fs-object-package фс-об'єкт-пакет)
; D9:001011111
(визначити fs-root-package фс-корінь-пакет)
; D9:001101011
(визначити фс-журнал-подія fs-journal-event)
; D9:001011001
(визначити фс-журнал-додати fs-journal-append)
; D9:001111100
(визначити фс-серіалізувати-журнал fs-serialize-journal)

; D9 canonical Ukrainian SENS aliases for persistent functional FS laws.
; No unqualified domain conversion, new machine mechanisms or host I/O path.
; D9:010000010
(визначити fs-write фс-записати)
; D9:010110011
(визначити fs-read фс-читати)
; D9:001010100
(визначити fs-object-addresses фс-об'єкт-адреси)
; D9:010101111
(визначити фс-пакет-поле fs-package-field)
; D9:010010111
(визначити фс-серіалізувати-об'єкт fs-serialize-object)
; D9:101000110
(визначити фс-десеріалізувати-об'єкт fs-deserialize-object)
; D9:010011000
(визначити фс-серіалізувати-корінь fs-serialize-root)
; D9:001110011
(визначити фс-десеріалізувати-корінь fs-deserialize-root)
; D9:001100100
(визначити фс-побудувати-об'єкт-сховище fs-build-object-store)
; D9:010101000
(визначити фс-відновити-корінь fs-reconstruct-root)
; D9:001010110
(визначити фс-зв'язки-з-список fs-bindings-from-list)
; D9:001100000
(визначити фс-розв'язати fs-unbind)

; D9: точні 9-бітні ідентичності — lib/domains/d9.lisp.
; Чинні закони залишаються в SENS-донорі вище, не в Rust чи Zig.
; Ці DEFINE зв'язують українські поверхні; це не автоматичний D9 opcode.
; D9:001100111
(визначити фс-журнал-записати-подія fs-journal-write-event)
; D9:001111111
(визначити фс-журнал-зв'язати-подія fs-journal-bind-event)
; D9:001001010
(визначити фс-журнал-розв'язати-подія fs-journal-unbind-event)
; D9:001100101
(визначити фс-журнал-корінь-коміт-подія fs-journal-root-commit-event)
; D9:010110111
(визначити фс-журнал-повторити fs-journal-replay)
; D9:010111010
(визначити фс-десеріалізувати-журнал fs-deserialize-journal)

; opt-in повна укр-поверхня: exact identity = lib/domains/d*.lisp; DEFINE-аліас, без нової диспетчеризації.
(визначити усі-адреси-об'єктів-файлової-системи-наявні? fs-all-addresses-present?)
(визначити усі-адреси-зв'язувань-у-файловій-системі-наявні? fs-binding-addresses-present?)
(визначити рішення-щодо-пакета-об'єкта-файлової-системи fs-object-package-decision)
(визначити рішення-щодо-кореневого-пакета-файлової-системи fs-root-package-decision)

; Українські визначення функцій сховища належать бібліотеці вмісту.
; Тут вони повторно не визначаються через історичні англійські псевдоніми.
; Назву доступу до адреси знань лишено як наявну міжбібліотечну межу.
(визначити знання-вміст-адреса knowledge-content-address)

; Сумісність історичних викликачів D10: те саме Lisp-замикання, не новий закон.
(визначити fs-journal-event-decision рішення-щодо-події-журналу-файлової-системи)

; Історичні псевдоніми сумісності; викличні голови тепер українські.
(визначити fs-package-has-field? фс-пакет-має-поле?)
(визначити fs-journal-version-current? фс-версія-журналу-чинна?)
(визначити fs-bindings-without фс-зв'язки-без-імені)
(визначити fs-journal-alist? фс-журнал-список-пар?)
(визначити fs-journal-replay-onto фс-журнал-відтворити-на-стан)
(визначити fs-journal-replay-event фс-журнал-відтворити-подію)
(визначити fs-commit-stage? фс-етап-коміту?)
