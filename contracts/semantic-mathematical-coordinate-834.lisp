; #834 — координатна вісь математичних законів.
;
; Лише-композиційний вид над наявними семантичними ідентичностями, що належать Lisp.
; Цей файл НЕ карбує SID і не визначає значення часу виконання.
; Канонічне джерело ідентичності: lib/surface/semantic-registry.lisp (sr/2).
; Наявні влади законів/результатів лишаються:
;   #216 бінарний домен exact-Q,
;   #218 структурне спостереження / відношення тотожності,
;   #217 диспетчеризація контролю за явним результатом.
;
(semantic-mathematical-coordinate/1
  (authority-source . "lib/surface/semantic-registry.lisp")
  (axis . mathematical-law)
  (scope . bounded-first-slice)
  (rows
    (((sid . "00001100")
      (status . witnessed)
      (domain . exact-rational)
      (law . addition-result)
      (witness . "tests/fixtures/semantic-coordinate-math-834.lisp"))
     ((sid . "00000011")
      (status . witnessed)
      (domain . atom-identity)
      (law . identity-relation)
      (witness . "tests/fixtures/semantic-coordinate-math-834.lisp"))
     ((sid . "00000100")
      (status . witnessed)
      (domain . structural-pair)
      (law . cons-car-equation)
      (witness . "tests/fixtures/semantic-coordinate-math-834.lisp"))
     ((sid . "00000101")
      (status . witnessed)
      (domain . structural-pair)
      (law . car-cons-equation)
      (witness . "tests/fixtures/semantic-coordinate-math-834.lisp"))
     ((sid . "00000111")
      (status . no-mathematical-law-witness)
      (domain . control-semantics)
      (law . ())
      (witness . "tests/fixtures/semantic-coordinate-math-834.lisp")))))
