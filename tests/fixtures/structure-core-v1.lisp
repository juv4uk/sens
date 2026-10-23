; #230 — структурні свідки першого ядра, визначені мовою СЕНС.
; Закріплюють лише поведінку як-є, сполучити, перше й решта,
; щоб подальша міграція істинності не могла непомітно змінити їхні закони.
; Виконавчі вирази й очікування незмінні; semantic-id — точна (D3, біти)
; за чинною колонкою «укр» lib/domains/d3.lisp, не старий плоский SID8.

((expr . "(як-є (alpha beta))")
 (expected . "(alpha beta)")
 (structure-core . t)
 (semantic-id . "D3:001")
 (note . "як-є повертає синтаксис як звичайні дані"))

((expr . "(як-є (alpha . beta))")
 (expected . "(alpha . beta)")
 (structure-core . t)
 (semantic-id . "D3:001")
 (note . "як-є зберігає крапкову структуру без значення істинності"))

((expr . "(сполучити (як-є alpha) (як-є beta))")
 (expected . "(alpha . beta)")
 (structure-core . t)
 (semantic-id . "D3:111")
 (note . "сполучити будує крапкову пару з довільних значень"))

((expr . "(сполучити (як-є alpha) (сполучити (як-є beta) (як-є ())))")
 (expected . "(alpha beta)")
 (structure-core . t)
 (semantic-id . "D3:111")
 (note . "сполучити з () будує правильний список"))

((expr . "(перше (сполучити (як-є left) (як-є right)))")
 (expected . "left")
 (structure-core . t)
 (semantic-id . "D3:100")
 (note . "перше(сполучити x y) повертає x незалежно від істинності"))

((expr . "(решта (сполучити (як-є left) (як-є right)))")
 (expected . "right")
 (structure-core . t)
 (semantic-id . "D3:011")
 (note . "решта(сполучити x y) повертає y незалежно від істинності"))

((expr . "(перше (сполучити (як-є ()) (як-є tail)))")
 (expected . "()")
 (structure-core . t)
 (semantic-id . "D3:100")
 (note . "перше може повернути () як дані; це не логічне НІ"))

((expr . "(решта (сполучити (як-є head) (як-є ())))")
 (expected . "()")
 (structure-core . t)
 (semantic-id . "D3:011")
 (note . "решта може повернути порожній список без семантики істинності"))
