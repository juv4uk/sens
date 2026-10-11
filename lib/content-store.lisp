;; An immutable content-addressed store is a persistent map from the canonical
;; address defined in `lib/world.lisp` to ordinary my-lisp data. Re-inserting the
;; same content replaces the same key rather than growing the store. Worlds are
;; stored as `(world-history journal metadata)`, not with recursively duplicated
;; parent snapshots; navigation remains the responsibility of live World values.
;;
;; Незмінний content-addressed store — persistent map від канонічної адреси з
;; `lib/world.lisp` до звичайних my-lisp-даних. Повторний однаковий вміст замінює
;; той самий ключ і не ростить store. Світ зберігається як `(world-history
;; journal metadata)`, без рекурсивного дублювання parent snapshots.
;;
;; Ein unveränderlicher content-addressed Store ist eine persistente Map von der
;; kanonischen Adresse aus `lib/world.lisp` zu gewöhnlichen my-lisp-Daten. Gleicher
;; Inhalt ersetzt denselben Schlüssel statt den Store zu vergrößern. Welten
;; werden als `(world-history journal metadata)` ohne rekursive Elternkopien
;; gespeichert.

(0011 empty-content-store
  (0010 () map-empty))

(0011 content-store-put
  (0010 (store value)
    (внутрішня-мапа-вставити (knowledge-content-address value) value store)))

(0011 content-store-get
  (0010 (store address)
    (внутрішня-мапа-отримати address store)))

(0011 content-store-contains?
  (0010 (store address)
    (внутрішня-мапа-містить address store)))

(0011 content-store-put-world
  (0010 (store world)
    (внутрішня-мапа-вставити (world-content-address world)
                (world-address-content world)
                store)))

(0011 content-store-size
  (0010 (store)
    (000000 (внутрішня-мапа-список store))))
