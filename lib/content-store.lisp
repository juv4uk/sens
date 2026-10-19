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

(визначити порожній-вміст-сховище
  (функція () мапа-порожній))

(визначити вміст-сховище-покласти
  (функція (сховище значення)
    (внутрішня-мапа-вставити (знання-вміст-адреса значення) значення сховище)))

(визначити вміст-сховище-отримати
  (функція (сховище адреса)
    (внутрішня-мапа-отримати адреса сховище)))

(визначити вміст-сховище-містить?
  (функція (сховище адреса)
    (внутрішня-мапа-містить адреса сховище)))

(визначити вміст-сховище-покласти-світ
  (функція (сховище світ)
    (внутрішня-мапа-вставити (знання-вміст-адреса (світ-адреса-вміст світ))
                (світ-адреса-вміст світ)
                сховище)))

(визначити вміст-сховище-розмір
  (функція (сховище)
    (внутрішня-довжина сховище)))

; Повні укр-імена — первинні Lisp-owned замикання ратифікованих D9-резидентів.
; Exact 9-bit identities live in lib/domains/d9.lisp; they are not call heads.
; D9:000010111 CONTENT-STORE-SIZE
; D9:000011110 CONTENT-STORE-CONTAINS?
; D9:000100000 CONTENT-STORE-GET
; D9:000100001 EMPTY-CONTENT-STORE
; D9:000101101 CONTENT-STORE-PUT
; D9:000111111 CONTENT-STORE-PUT-WORLD
; Підстановка лише змінює людську проєкцію: жодної нової диспетчеризації,
; числового перетворення, ширини-здогадки чи зміни тіла функцій.
;
; opt-in повна укр-поверхня: первинні D9-замикання вже названі укр; EN входи сумісні.
(визначити empty-content-store порожній-вміст-сховище)
(визначити content-store-put вміст-сховище-покласти)
(визначити content-store-get вміст-сховище-отримати)
(визначити content-store-contains? вміст-сховище-містить?)
(визначити content-store-put-world вміст-сховище-покласти-світ)
(визначити content-store-size вміст-сховище-розмір)
