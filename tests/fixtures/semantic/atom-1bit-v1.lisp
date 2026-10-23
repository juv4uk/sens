; tests/fixtures/semantic/atom-1bit-v1.lisp — #1709, закон #1704.
; Українська проєкція Д3:010. Предикат атомарності → рівно один біт Д1.
; Старі десяткові SID8 не визначають семантичну адресу.

((expect . expect-value)
 (expr . "(атом? число-один)")
 (expected . (value (1)))
 (active . t)
 (name . "ATOM цілого — YES")
 (semantic-id . "D3:010")
 (governs . "#1704")
 (note . "Ціле — не пара, тому YES."))

((expect . expect-value)
 (expr . "(атом? (як-є (alpha beta)))")
 (expected . (value (0)))
 (active . t)
 (name . "ATOM пари — NO")
 (semantic-id . "D3:010")
 (governs . "#1704")
 (note . "Пара — NO."))

((expect . expect-value)
 (expr . "(атом? (як-є ()))")
 (expected . (value (1)))
 (active . ())
 (name . "ATOM пустого списку — YES")
 (semantic-id . "D3:010")
 (governs . "#1704 #1713")
 (note . "Неактивний доки runtime не дає 1 для ()."))

((expect . expect-value)
 (expr . "(атом? (як-є (alpha beta)))")
 (expected . (value (0)))
 (active . t)
 (name . "atom? пари — NO")
 (semantic-id . "D3:010")
 (governs . "#1704")
 (note . "Сигнатурний предикат — той самий 1 біт."))
