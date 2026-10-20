; Дослідницькі дані для #223 -- НЕ семантика мови.
; Гілка: research/223-many-valued-logic
;
; Мета: фіксовані чотиризначні таблиці Белнапа, щоб майбутня реалізація
; my-lisp могла звірятися з опублікованими фактами ґратки.
; Ці форми — ЛИШЕ ДАНІ. Їх не можна встановлювати в шлях диспетчеризації
; Core4/W4 і вони не повинні змінювати EVAL звичайних форм SENS.
;
; Кодування (чотири значення):
;   neither     -- немає інформації (прогалина)
;   false-only  -- лише негативна підтримка
;   true-only   -- лише позитивна підтримка
;   both        -- конфлікт (надлишок)
;
; Посилання на ґратку — стандартний Belnap FOUR / A4:
;   порядок істини:   false-only < neither,both < true-only
;   порядок знання:   neither < false-only,true-only < both
;
; Без оцінювача, без макросів читання, без нових викликних голів.
; Будь-який код, що споживає ці таблиці, живе поза Core4 і поза
; багатшою логікою my-lisp і не встановлює жодної семантики оцінювача.

(визначити research-belnap-four-values
  (як-є
    (neither
     false-only
     true-only
     both)))

; Форма: (state positive-support negative-support)
; Порожні списки підтримки — структурні порожні списки, не FALSE.
(визначити research-belnap-support-shapes
  (як-є
    ((neither    ()       ())
     (false-only ()       (not-p))
     (true-only  (p)      ())
     (both       (p)      (not-p)))))

; Відношення покриття для ґратки істини (порядок апроксимації).
; Пара (a b) означає: a безпосередньо <=_truth b.
(визначити research-belnap-truth-covers
  (як-є
    ((false-only neither)
     (false-only both)
     (neither true-only)
     (both true-only))))

; Відношення покриття для ґратки знання (порядок інформації).
; Пара (a b) означає: a безпосередньо <=_knowledge b.
(визначити research-belnap-knowledge-covers
  (як-є
    ((neither false-only)
     (neither true-only)
     (false-only both)
     (true-only both))))

; Заперечення міняє місцями позитивну й негативну підтримку;
; прогалину й надлишок інформації лишає нерухомими.
; Форма: (input output)
(визначити research-belnap-negation
  (як-є
    ((neither neither)
     (false-only true-only)
     (true-only false-only)
     (both both))))

; Кон'юнкція ґратки істини (meet за <=_truth).
; Форма кожного рядка: (left right result).
(визначити research-belnap-truth-meet
  (як-є
    ((neither neither neither)
     (neither false-only false-only)
     (neither true-only neither)
     (neither both false-only)
     (false-only neither false-only)
     (false-only false-only false-only)
     (false-only true-only false-only)
     (false-only both false-only)
     (true-only neither neither)
     (true-only false-only false-only)
     (true-only true-only true-only)
     (true-only both both)
     (both neither false-only)
     (both false-only false-only)
     (both true-only both)
     (both both both))))

; Диз'юнкція ґратки істини (join за <=_truth).
(визначити research-belnap-truth-join
  (як-є
    ((neither neither neither)
     (neither false-only neither)
     (neither true-only true-only)
     (neither both true-only)
     (false-only neither neither)
     (false-only false-only false-only)
     (false-only true-only true-only)
     (false-only both both)
     (true-only neither true-only)
     (true-only false-only true-only)
     (true-only true-only true-only)
     (true-only both true-only)
     (both neither true-only)
     (both false-only both)
     (both true-only true-only)
     (both both both))))

; Meet ґратки знання / консенсус: лишити лише спільну для обох інформацію.
(визначити research-belnap-knowledge-meet
  (як-є
    ((neither neither neither)
     (neither false-only neither)
     (neither true-only neither)
     (neither both neither)
     (false-only neither neither)
     (false-only false-only false-only)
     (false-only true-only neither)
     (false-only both false-only)
     (true-only neither neither)
     (true-only false-only neither)
     (true-only true-only true-only)
     (true-only both true-only)
     (both neither neither)
     (both false-only false-only)
     (both true-only true-only)
     (both both both))))

; Join ґратки знання / накопичення інформації: об'єднати підтримку.
(визначити research-belnap-knowledge-join
  (як-є
    ((neither neither neither)
     (neither false-only false-only)
     (neither true-only true-only)
     (neither both both)
     (false-only neither false-only)
     (false-only false-only false-only)
     (false-only true-only both)
     (false-only both both)
     (true-only neither true-only)
     (true-only false-only both)
     (true-only true-only true-only)
     (true-only both both)
     (both neither both)
     (both false-only both)
     (both true-only both)
     (both both both))))

; Межові випадки, які майбутній шар my-lisp не повинен трактувати як відповіді Core4.
; Форма: (tag expected-result-description)
; expected — схожий на коментар список символів, не обчислюється.
(визначити research-belnap-invalid-boundary-cases
  (як-є
    ((outer-no-answer
       expected ())

     (note conflict-does-not-explode)

     (no-richer-answer
       expected ()))))
