; #845 — матриця семантичних координат, версія 2; лише читання.
;
; Це тільки зведене представлення: файл не визначає семантичного
; значення, не призначає SID і не копіює дані математичної,
; ядерної чи машинної осі.
;
; Спостерігач виводить координати із зазначених чинних джерел.
; Відсутність свідчень для осі дозволена; її потрібно вказувати
; явно, а не заповнювати здогадом.

(semantic-coordinate-matrix/2
  (identity-source . "lib/surface/semantic-registry.lisp")
  (math-axis-source . "tests/fixtures/semantic-coordinate-law-axis-v1.lisp")
  (kernel-axis-source . "contracts/sid-kernel-witness-735.lisp")
  (machine-axis-source . "lib/machine/capability-axis.lisp")
  (missing-axis-policy . explicit)
  (scope
    00001100 ; +
    00000011 ; eq
    00000100 ; cons
    00000101 ; car
    00000111)) ; cond
