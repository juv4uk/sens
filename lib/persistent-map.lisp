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

(визначити мапа-порожній (як-є ()))

(визначити мапа-вставити
  (функція (key value entries)
    (за-умовою
      ((порожній? entries)
       (список (сполучити key value)))
      ((тотожне? key (перше (перше entries)))
       (сполучити (сполучити key value) (решта entries)))
      (так
       (сполучити (перше entries)
            (внутрішня-мапа-вставити key value (решта entries)))))))

(визначити мапа-отримати
  (функція (key entries)
    (за-умовою
      ((порожній? entries) (як-є ()))
      ((тотожне? key (перше (перше entries)))
       (список (решта (перше entries))))
      (так
       (мапа-отримати key (решта entries))))))

; Exact D1 projection: presence is (010 (001 ())) form via NOT of empty get.
(визначити мапа-містить?
  (функція (key entries)
    (хибне? (атом? (мапа-отримати key entries)))))

(визначити мапа-список
  (функція (entries) entries))

; Приватні Lisp-owned механізми. Назви лишають зовнішній D9 resident
; fail-closed: residency сама по собі не створює mechanism.
(визначити внутрішня-мапа-вставити мапа-вставити)
(визначити внутрішня-мапа-отримати мапа-отримати)
(визначити внутрішня-мапа-містить мапа-містить?)
(визначити внутрішня-мапа-список мапа-список)

; Full укр names are the primary Lisp-owned closures for their ratified residents.
; Exact identities: MAP-EMPTY D9:101100011; MAP-INSERT D9:101101110;
; MAP-GET D9:101100101; MAP-CONTAINS? D9:101100010; MAP->LIST D9:101001100.
; The width belongs to the domain row; this library never executes raw bit strings.
(визначити внутрішня-мапа-порожній мапа-порожній)

; Історичні англійські входи — сумісні псевдоніми тих самих укр-замикань.
(визначити map-empty мапа-порожній)
(визначити map-insert мапа-вставити)
(визначити map-get мапа-отримати)
(визначити map-contains? мапа-містить?)
(визначити map->list мапа-список)
