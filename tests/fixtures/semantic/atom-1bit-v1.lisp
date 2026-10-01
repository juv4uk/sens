; tests/fixtures/semantic/atom-1bit-v1.lisp — #1709, закон #1704.
; ATOM відповідає рівно одним бітом для кожного admitted аргументу:
;   ()      -> 1   (пустий список НЕ є парою)
;   non-pair-> 1
;   pair    -> 0
; Жодних винятків і жодного третього представлення. Порожній список — це
; non-pair, тому той самий закон, що й для будь-якого іншого не-пари.
;
; ATOM answers with exactly one bit for every admitted argument:
;   ()      -> 1   (the empty list is NOT a pair)
;   non-pair-> 1
;   pair    -> 0
; No exceptions, no third presentation. The empty list is a non-pair, so it
; follows the same law as any other non-pair.

((expect . expect-value)
 (expr . "(10110101 5)")
 (expected . (value (1)))
 (active . t)
 (name . "ATOM цілого — YES")
 (semantic-id . 10110101)
 (governs . "#1704")
 (note . "Ціле — не пара, тому YES."))

((expect . expect-value)
 (expr . "(10110101 (00000001 (alpha beta)))")
 (expected . (value (0)))
 (active . t)
 (name . "ATOM пари — NO")
 (semantic-id . 10110101)
 (governs . "#1704")
 (note . "Пара — NO; це єдина категорія, яка відповідає 0."))

((expect . expect-value)
 (expr . "(10110101 (00000001 ()))")
 (expected . (value (1)))
 (active . ())
 (name . "ATOM пустого списку — YES, не третє представлення")
 (semantic-id . 10110101)
 (governs . "#1704 #1713")
 (note . "Неактивний: поточний рантайм відповідає (). Головний конфлікт #1709 з runtime."))

((expect . expect-value)
 (expr . "(00000010 (00000001 (alpha beta)))")
 (expected . (value (0)))
 (active . t)
 (name . "atom? пари — NO")
 (semantic-id . 00000010)
 (governs . "#1704")
 (note . "Сигнатурний предикат ATOMP ділиться ту саму відповідь 1 біт."))
