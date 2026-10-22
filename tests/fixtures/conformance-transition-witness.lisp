; Перехідні свідчення #231/#220: чинні відповідники історичних випробувань.
;
; Файл tests/fixtures/conformance.lisp залишається історичним доказом.
; Записи нижче не встановлюють нових семантичних законів: поле
; `supersedes-expr` указує на старий вираз, а поля `expr` та `expected`
; визначають його чинну виконувану заміну й очікуваний результат.
; У чинних умовах обидві гілки мають рівно два поля; істинність дають лише обчислені Д1-предикати.
; Старі трипольові конструкції лишаються тільки як текст походження.
;
; Rust має право лише переносити ці відповідності, але не вигадувати
; вилучену форму чи її наступника. Після архівування старого корпусу
; двочастинних умовних конструкцій цей перехідний файл можна вилучити.

((supersedes-expr . "(cond (0 (quote truthy)) (t (quote falsy)))")
 (expr . "(за-умовою ((атом? (як-є (()))) (як-є wrong)) ((атом? (як-є ())) (як-є zero-data)))")
 (expected . "zero-data")
 (meta-eval . t)
 (reason . universal-zero-truthiness-retired)
 (owner . "217/220/231"))

((supersedes-expr . "(cond (0 (quote zero-is-truthy)) (t (quote wrong)))")
 (expr . "(за-умовою ((атом? (як-є (()))) (як-є wrong)) ((атом? (як-є ())) (як-є explicit-fallback)))")
 (expected . "explicit-fallback")
 (meta-eval . t)
 (reason . universal-zero-truthiness-retired)
 (owner . "217/220/231"))

((supersedes-expr . "(= 3 3.0)")
 (expr . "(= 3 3.0)")
 (expected . "1")
 (compiler-corpus . t)
 (reason . exact-q-result-algebra-supersedes-truth-sentinel)
 (owner . "216/220/631"))

((supersedes-expr . "(cond (() (quote first)) (() (quote second)) (t (quote third)))")
 (expr . "(за-умовою ((тотожне? (як-є одне) (як-є інше)) (як-є перше)) ((тотожне? (як-є друге) (як-є третє)) (як-є друге)))")
 (expected . "()")
 (meta-eval . t)
 (owner . "4196/4166"))

((supersedes-expr . "(cond ((quote radio) antenna (quote wrong)))")
 (expr . "(за-умовою ((тотожне? (як-є radio) (як-є radio)) (як-є antenna)))")
 (expected . "antenna")
 (meta-eval . t)
 (owner . "4196/4166"))
