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

(00001001 empty-content-store
  (00001000 () map-empty))

(00001001 content-store-put
  (00001000 (store value)
    (01101110 (knowledge-content-address value) value store)))

(00001001 content-store-get
  (00001000 (store address)
    (01101101 address store)))

(00001001 content-store-contains?
  (00001000 (store address)
    (01101111 address store)))

(00001001 content-store-put-world
  (00001000 (store world)
    (01101110 (world-content-address world)
                (world-address-content world)
                store)))

(00001001 content-store-size
  (00001000 (store)
    (00101000 (01110000 store))))
