; #845 — матриця семантичних координат, версія 2; лише читання.
;
; Це тільки зведене представлення: файл не визначає семантичного
; значення, не призначає SID і не копіює дані математичної,
; ядерної чи машинної осі.
;
; Спостерігач виводить координати із зазначених чинних джерел.
; Відсутність свідчень для осі дозволена; її потрібно вказувати
; явно, а не заповнювати здогадом.

(semantic-coordinate-matrix-2
  (identity-source . "knowledge/d1-d11-foundation.json")
  (ukr-projection-source . "lib/domains/d3.lisp;lib/domains/d5.lisp")
  (math-axis-source . "tests/fixtures/semantic-coordinate-law-axis-v1.lisp")
  (kernel-axis-source . "contracts/sid-kernel-witness-735.lisp")
  (machine-axis-source . "lib/machine/capability-axis.lisp")
  (missing-axis-policy . explicit)
  (scope
    (Д5 01010 додати)
    (Д3 101 тотожне?)
    (Д3 111 сполучити)
    (Д3 100 перше)
    (Д3 110 за-умовою)))
