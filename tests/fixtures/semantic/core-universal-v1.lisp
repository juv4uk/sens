; tests/fixtures/semantic/core-universal-v1.lisp — #1709.
; Спільний корпус: ці очікування мають бути однаковими під кожним профілем
; (native evaluator, Core1, Core2, Core3, Core4). Якщо ядро дає іншу
; відповідь, ніж нативний рантайм, це розбіжність, а не особливість профілю.
; Rust не має права «підлаштовувати» очікування під профіль: воно переносить
; фактичний результат, а вердикт виносить Lisp.
;
; Shared corpus: these expectations must be identical under every profile
; (native evaluator, Core1, Core2, Core3, Core4). If a core answers
; differently from the native runtime, that is a divergence, not a profile
; feature. Rust may not adapt expectations per profile: it transports the
; actual result, Lisp delivers the verdict.

((expect . expect-value)
 (expr . "(00100010 1 1)")
 (expected . (value (1)))
 (active . t)
 (name . "universal: equal? 1 1 -> 1 біт")
 (semantic-id . 00100010)
 (governs . "#1699")
 (note . "Однакова відповідь у кожному профілі."))

((expect . expect-value)
 (expr . "(00100010 1 2)")
 (expected . (value (0)))
 (active . t)
 (name . "universal: equal? 1 2 -> 1 біт")
 (semantic-id . 00100010)
 (governs . "#1699")
 (note . "Відсутність збігу теж має бути 0, а не ()."))

((expect . expect-value)
 (expr . "(10110101 5)")
 (expected . (value (1)))
 (active . t)
 (name . "universal: ATOM не-пара -> 1")
 (semantic-id . 10110101)
 (governs . "#1704")
 (note . "Спільна істина для всіх профілів."))

((expect . expect-value)
 (expr . "(10110101 (00000001 (alpha beta)))")
 (expected . (value (0)))
 (active . t)
 (name . "universal: ATOM пара -> 0")
 (semantic-id . 10110101)
 (governs . "#1704")
 (note . "Спільна істина для всіх профілів."))

((expect . expect-value)
 (expr . "(10110110 (00000001 alpha) (00000001 alpha))")
 (expected . (value (1)))
 (active . t)
 (name . "universal: EQ той самий атом -> 1")
 (semantic-id . 10110110)
 (governs . "#1705")
 (note . "Спільна істина для всіх профілів."))

((expect . expect-value)
 (expr . "(10110110 (00000001 alpha) (00000001 beta))")
 (expected . (value (0)))
 (active . t)
 (name . "universal: EQ різні атоми -> 0")
 (semantic-id . 10110110)
 (governs . "#1705")
 (note . "Спільна істина для всіх профілів."))

 ((expect . expect-rejected)
  (expr . "(10110110 1")
  (expected . (rejected "(10110110 1"))
  (active . t)
  (name . "universal: незакрита форма відхиляється, а не ремонтується")
  (semantic-id . "reader")
  (governs . "#1709")
  (note . "Корпус є Lisp-джерелом: пошкоджене джерело відхиляється читачем, а не мовчки виправляється."))
