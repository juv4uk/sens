; tests/fixtures/semantic/eq-1bit-v1.lisp — #1709, закон #1705.
; Предикат тотожності атомів повертає рівно один біт у допустимій області
; аргументів та іменовану помилку поза нею.
;
;   однакові допустимі атоми  → 1 (ТАК)
;   різні допустимі атоми    → 0 (НІ)
;   хоча б один аргумент-пара → помилка типу Type, а не біт
;
; Пара не належить області визначення атомарного EQ. Тому
; відхилення пари не можна мовчки прирівнювати до відповіді НІ.
; Двійкові рядки, позначки `semantic-id` та імена тестових полів
; нижче — історичні дані, їхня фізична форма тут не змінюється.

((expect . expect-value)
 (expr . "(10110110 (00000001 alpha) (00000001 alpha))")
 (expected . (value (1)))
 (active . t)
 (name . "EQ того самого атома — YES")
 (semantic-id . 10110110)
 (governs . "#1705")
 (note . "Тот самий admitted atom -> 1 біт."))

((expect . expect-value)
 (expr . "(10110110 (00000001 alpha) (00000001 beta))")
 (expected . (value (0)))
 (active . t)
 (name . "EQ різних атомів — NO")
 (semantic-id . 10110110)
 (governs . "#1705")
 (note . "Різні admitted atoms -> 1 біт NO, не помилка."))

((expect . expect-error)
 (expr . "(10110110 (00100111 (00000001 1)) (00100111 (00000001 1)))")
 (expected . (error "Type"))
 (active . t)
 (name . "EQ пари — іменована помилка, не біт")
 (semantic-id . 10110110)
 (governs . "#1705 #1709")
 (note . "Пара поза admitted-діапазоном EQ: іменована помилка, а не 0 і не 1."))

((expect . expect-value)
 (expr . "(00000011 (00000001 alpha) (00000001 alpha))")
 (expected . (value (1)))
 (active . t)
 (name . "eq? того самого атома — YES")
 (semantic-id . 00000011)
 (governs . "#1705")
 (note . "Сигнатурний предикат EQP ділиться ту саму відповідь 1 біт."))

((expect . expect-value)
 (expr . "(00000011 (00000001 alpha) (00000001 beta))")
 (expected . (value (0)))
 (active . t)
 (name . "eq? різних атомів — NO")
 (semantic-id . 00000011)
 (governs . "#1705")
 (note . "Той самий закон, що й для answer-eq."))
