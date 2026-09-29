; tests/fixtures/semantic/eq-1bit-v1.lisp — #1709, закон #1705.
; EQ відповідає рівно одним бітом на admitted-діапазоні та іменованою помилкою
; поза ним. Пара не є допустимим аргументом EQ, тому вона не має типу
; (ні true, ні false) — вона поза доменом предиката.
;
;   same admitted atom  -> 1
;   distinct atoms      -> 0
;   any pair argument   -> named error (Type), not a bit
;
; EQ answers with exactly one bit on the admitted domain and a named error
; outside it. A pair is not an admitted EQ argument, so it has no predicate
; type at all — it is outside the domain, not a false answer.

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
