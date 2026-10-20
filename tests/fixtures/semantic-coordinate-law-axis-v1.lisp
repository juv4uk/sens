; Обмежений свідок осі законів семантичних координат #834.
; Це доказові дані, а не друга таблиця семантичної ратифікації.
; Тотожності та закони належать чинному канону СЕНС.
; Власні Lisp-функції й параметри — українською, таблиця свідчень незмінна.
; Людські числа залишено десятковими, без виведення домену з байтів.

(визначити вісь-законів-семантичних-координат-1
  (як-є
    ((12
       (axis mathematical)
       (domain exact-rational-arithmetic)
       (witness exact-rational-sum)
       (evidence tests/fixtures/mathematical-result-v1.lisp))
     (4
       (axis equational-structure)
       (domain pair-construction)
       (witness car-cons-left-inverse)
       (evidence lib/canon.lisp))
     (5
       (axis equational-structure)
       (domain pair-elimination)
       (witness car-cons-left-inverse)
       (evidence lib/canon.lisp))
     (7
       (axis semantic-control)
       (domain non-mathematical-in-this-slice)
       (witness no-mathematical-law-claimed)
       (evidence contracts/control-dispatch-contract.lisp)))))

(визначити рядок-закону-семантичної-координати
  (функція (ідентичність рядки)
    (за-умовою
      ((атом? рядки) (як-є ()))
      ((тотожне? ідентичність (перше (перше рядки))) (перше рядки))
      (так (рядок-закону-семантичної-координати ідентичність (решта рядки))))))

(визначити закон-семантичної-координати-за-ідентичністю
  (функція (ідентичність)
    (рядок-закону-семантичної-координати ідентичність вісь-законів-семантичних-координат-1)))

; Історичні сумісні імена не створюють нових ідентичностей.
(визначити semantic-coordinate-law-axis-v1 вісь-законів-семантичних-координат-1)
(визначити semantic-coordinate-law-row рядок-закону-семантичної-координати)
(визначити semantic-coordinate-law-for-sid закон-семантичної-координати-за-ідентичністю)
