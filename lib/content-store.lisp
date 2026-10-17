;; An immutable content-addressed store is a persistent map from the canonical
;; address defined in `lib/world.lisp` to ordinary my-lisp data. Re-inserting the
;; same content replaces the same key rather than growing the store. Worlds are
;; stored as `(world-history journal metadata)`, not with recursively duplicated
;; parent snapshots; navigation remains the responsibility of live World values.
;;
;; Migrated: pure surface composition over exact D1 map (lib/persistent-map.lisp)
;; and world/knowledge content addresses. No host truthiness. No new COND.
;; Width is identity; every bit of the domain address is valued.
;;
;; Reuses (2000+ surface):
;;   map-empty, внутрішня-мапа-вставити, внутрішня-мапа-отримати,
;;   внутрішня-мапа-містить, внутрішня-довжина,
;;   knowledge-content-address, world-content-address, world-address-content.
;;
;; Незмінний content-addressed store — persistent map від канонічної адреси з
;; `lib/world.lisp` до звичайних my-lisp-даних. Повторний однаковий вміст замінює
;; той самий ключ і не ростить store.
;;
;; Ein unveränderlicher content-addressed Store ist eine persistente Map von der
;; kanonischen Adresse aus `lib/world.lisp` zu gewöhnlichen my-lisp-Daten.

(0011 empty-content-store
  (функція () мапа-порожній))

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
    (внутрішня-довжина store)))

; D9:000101101 CONTENT-STORE-PUT and D9:000111111 CONTENT-STORE-PUT-WORLD.
; Source: knowledge/d9-semantic-layer-harvest-v1.json and this Lisp module.
; Both take (store value/world); their canonical content address is derived
; by the existing SENS code. Never alias either to three-argument MAP-INSERT.
; These are Ukrainian SENS surface bindings, not new D9 native opcodes.
(0011 вміст-сховище-покласти content-store-put)
(0011 вміст-сховище-покласти-світ content-store-put-world)
