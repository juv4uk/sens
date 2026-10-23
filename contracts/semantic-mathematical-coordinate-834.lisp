; #834 — координатна вісь математичних законів.
;
; Лише-композиційний вид над наявними семантичними ідентичностями, що належать Lisp.
; Цей файл НЕ карбує SID і не визначає значення часу виконання.
; Канонічна тотожність — ратифікована драбина D1–D11;
; повні українські викличні поверхні — lib/domains/d3.lisp та d5.lisp.
; Наявні влади законів/результатів лишаються:
;   #216 бінарний домен exact-Q,
;   #218 структурне спостереження / відношення тотожності,
;   #217 диспетчеризація контролю за явним результатом.
;
(semantic-mathematical-coordinate-1
  (authority-source . "knowledge/d1-d11-foundation.json")
  (ukr-projection-source . "lib/domains/d3.lisp;lib/domains/d5.lisp")
  (axis . mathematical-law)
  (scope . bounded-first-slice)
  (rows
    (((identity . (D5 "01010"))
      (укр . додати)
      (status . witnessed)
      (domain . exact-rational)
      (law . addition-result)
      (witness . "tests/fixtures/semantic-coordinate-math-834.lisp"))
     ((identity . (D3 "101"))
      (укр . тотожне?)
      (status . witnessed)
      (domain . atom-identity)
      (law . identity-relation)
      (witness . "tests/fixtures/semantic-coordinate-math-834.lisp"))
     ((identity . (D3 "111"))
      (укр . сполучити)
      (status . witnessed)
      (domain . structural-pair)
      (law . cons-car-equation)
      (witness . "tests/fixtures/semantic-coordinate-math-834.lisp"))
     ((identity . (D3 "100"))
      (укр . перше)
      (status . witnessed)
      (domain . structural-pair)
      (law . car-cons-equation)
      (witness . "tests/fixtures/semantic-coordinate-math-834.lisp"))
     ((identity . (D3 "110"))
      (укр . за-умовою)
      (status . no-mathematical-law-witness)
      (domain . control-semantics)
      (law . ())
      (witness . "tests/fixtures/semantic-coordinate-math-834.lisp")))))
