; Свідчення #1826: порівняння в області точних чисел Q.
; Поле `expected` містить тільки людське подання бітової відповіді:
; "1" означає ТАК, "0" — НІ. Семантичний домен результату
; належить однобітному предикату, а не домену числових величин.
; Правило Q визначає допустимість аргументів, не алгебру істинності.
; Вихід за область допустимості має окрему іменовану помилку
; домену або типу, а не підміняється структурним порожнім списком.

((expr . "(= 1/3 2/6)")
 (expected . "1")
 (expected-domain . "predicate-bit")
 (case . rational-equality-yes))

((expr . "(< 2/3 3/4)")
 (expected . "1")
 (expected-domain . "predicate-bit")
 (case . rational-less-yes))

((expr . "(> 2/3 3/4)")
 (expected . "0")
 (expected-domain . "predicate-bit")
 (case . rational-greater-no))

((expr . "(<= 1/3 1/3 2/3)")
 (expected . "1")
 (expected-domain . "predicate-bit")
 (case . rational-nondecreasing-yes))

((expr . "(>= 3/4 2/3 2/3)")
 (expected . "1")
 (expected-domain . "predicate-bit")
 (case . rational-nonincreasing-yes))

; Закон #295: строгі ланцюгові порівняння зберігають семантику Q
; після вилучення історичних перевірок істинності з Rust.
; Результат установлює мова, а не новий зовнішній оракул.
((expr . "(< 1 2 3)")
 (expected . "1")
 (expected-domain . "predicate-bit")
 (case . strict-chain-yes))

((expr . "(< 1 3 2)")
 (expected . "0")
 (expected-domain . "predicate-bit")
 (case . strict-chain-no))

((expr . "(< 5)")
 (expected . "1")
 (expected-domain . "predicate-bit")
 (case . strict-single-argument-vacuous-yes))


; Канонізація числових дробів належить числовому домену окремо
; від однобітних відповідей предикатів. Ці рядки доводять лише
; рівноцінність записів 0/1 і 1/1 відповідно числам 0 і 1.
((expr . "(= 0 0/1)")
 (expected . "1")
 (expected-domain . "predicate-bit")
 (case . zero-and-zero-over-one-are-the-same-exact-q-value))

((expr . "(= 1 1/1)")
 (expected . "1")
 (expected-domain . "predicate-bit")
 (case . one-and-one-over-one-are-the-same-exact-q-value))

((expr . "(list 0 0/1 1 1/1)")
 (expected . "(0 0 1 1)")
 (case . denominator-one-source-spellings-write-canonically))

; Історичний закон #216: рівність точного цілого дає відповідь ТАК
; у домені Q, представлену одним бітом СЕНС, а не логічним типом хоста.
((expr . "(= 3 3)")
 (expected . "1")
 (expected-domain . "predicate-bit")
 (case . integer-equality-yes))

; Порівняння всіх сусідніх пар залишається ланцюговим законом області Q.
((expr . "(< 1 2 3 4)")
 (expected . "1")
 (expected-domain . "predicate-bit")
 (case . integer-less-chain-four-yes))
