; Персистентна map без прихованої арифметики.
;
; Migrated: COND fallback is the single exact D1:YES bit, never an extra D3 ATOM/QUOTE computation.
; Key equality is D3 EQ only. No host truthiness. Width is identity.
;
; Поточний числовий закон SENS допускає арифметику лише над явно
; кваліфікованими D24+ значеннями. Попередня AVL-реалізація зберігала
; host-подібні висоти 0/1/-1 і порівнювала codepoint через D5 LESSP.
; Після ратифікації D24+ це правильно стало недопустимим.
;
; Для семантики key->value балансування не є необхідним. Ця реалізація
; зберігає незмінність і structural sharing як список dotted entries:
;   (("a" . value-a) ("b" . value-b) ...)
; Вставка замінює перший рівний ключ або додає новий у хвіст. Рівність
; ключів належить D3 EQ; жоден порядок рядків, числова висота чи
; арифметичний literal не потрібні.
;
; Виконавчі голови цього файла навмисно обмежені D3/D4. Бітність є
; частиною identity: 0011/0010/0101/0100/1110 — D4; 110/101/111/100/011
; — D3. D9 map-residents тут не отримують автоматичної callability:
; нижні українські імена — Lisp-owned closures.

(0011 map-empty (001 ()))

(0011 map-insert
  (функція (key value entries)
    (за-умовою
      ((порожній? entries)
       (список (сполучити key value)))
      ((тотожне? key (перше (перше entries)))
       (сполучити (сполучити key value) (решта entries)))
      (#d1:1
       (сполучити (перше entries)
            (map-insert key value (решта entries)))))))

(0011 map-get
  (функція (key entries)
    (за-умовою
      ((порожній? entries) (як-є ()))
      ((тотожне? key (перше (перше entries)))
       (список (решта (перше entries))))
      (#d1:1
       (map-get key (решта entries))))))

; Exact D1 projection: presence is (010 (001 ())) form via NOT of empty get.
(0011 map-contains?
  (функція (key entries)
    (хибне? (атом? (map-get key entries)))))

(0011 map->list
  (функція (entries) entries))

; Приватні Lisp-owned механізми. Назви лишають зовнішній D9 resident
; fail-closed: residency сама по собі не створює mechanism.
(0011 внутрішня-мапа-вставити map-insert)
(0011 внутрішня-мапа-отримати map-get)
(0011 внутрішня-мапа-містить map-contains?)
(0011 внутрішня-мапа-список map->list)

; D9 resident projections over the existing immutable map mechanism.
; Exact identities: MAP-EMPTY D9:101100011; MAP-GET D9:101100101;
; MAP-CONTAINS? D9:101100010; MAP->LIST D9:101001100.
; These wrappers preserve the map's maybe-shaped lookup result and dotted-entry order.
(0011 внутрішня-мапа-порожній map-empty)
(0011 мапа-порожній внутрішня-мапа-порожній)
(0011 мапа-отримати внутрішня-мапа-отримати)
(0011 мапа-містить? внутрішня-мапа-містить)
(0011 мапа-список внутрішня-мапа-список)
