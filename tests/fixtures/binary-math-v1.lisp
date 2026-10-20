; Свідчення #216: двійкові рішення в області точної арифметики Q.
; Очікуваний вид результату, значення та стан домену визначає Lisp СЕНС.
; Rust тільки переносить фактичний вид і текстове подання результату
; до мовної перевірки, не створюючи нового семантичного вердикту.

((expr . "(= 1/3 2/6)")
 (expected-kind . rational)
 (expected-render . "1")
 (decision . yes)
 (active . t))

((expr . "(< 2/3 3/4)")
 (expected-kind . rational)
 (expected-render . "1")
 (decision . yes)
 (active . t))

((expr . "(> 2/3 3/4)")
 (expected-kind . rational)
 (expected-render . "0")
 (decision . no)
 (active . t))

((expr . "(= 3 3)")
 (expected-kind . rational)
 (expected-render . "1")
 (decision . yes)
 (active . t))

((expr . "(< 1 2 3 4)")
 (expected-kind . rational)
 (expected-render . "1")
 (decision . yes)
 (active . t))

; Неточні числа не належать області точних Q-операндів.
; Очікувані форми відмови збережено як історичні тестові дані.
((expr . "(= 3.0 3.0)")
 (expected-kind . empty-list)
 (expected-render . "()")
 (decision . no-answer)
 (active . t))

((expr . "(< 0.5 1.0)")
 (expected-kind . empty-list)
 (expected-render . "()")
 (decision . no-answer)
 (active . t))
