; #229 — current executable Canon laws under layered answer semantics.
; Expected values are Lisp-owned data. No row uses t/() as pass/fail truth.

((expr . "канон-порожній-список")
 (expected . "()")
 (active . t))

((expr . "(канон-закон-порожній-список)")
 (expected . "(canon-law-result empty-list satisfied)")
 (active . t))

((expr . "(канон-закон-атом-пара (quote left) (quote right))")
 (expected . "(canon-law-result atom-cons satisfied)")
 (active . t))

((expr . "(канон-закон-перше-пара (quote left) (quote right))")
 (expected . "(canon-law-result car-cons satisfied)")
 (active . t))

((expr . "(канон-закон-решта-пара (quote left) (quote right))")
 (expected . "(canon-law-result cdr-cons satisfied)")
 (active . t))

((expr . "(канон-закон-рівність-рефлексивний-атом (quote left))")
 (expected . "(canon-law-result eq-reflexive-atom satisfied)")
 (active . t))

((expr . "(канон-закон-решта-крапковий)")
 (expected . "(canon-law-result cdr-dotted satisfied)")
 (active . t))

((expr . "(канон-закон-решта-правильний)")
 (expected . "(canon-law-result cdr-proper satisfied)")
 (active . t))

((expr . "(канон-закон-решта-неправильний)")
 (expected . "(canon-law-result cdr-improper satisfied)")
 (active . t))

((expr . "(канон-закон-цитування-пригнічує-обчислення)")
 (expected . "(canon-law-result quote-suppresses-evaluation satisfied)")
 (active . t))

((expr . "(канон-закон-умова-перший-збіг-короткий-ланцюг)")
 (expected . "(canon-law-result cond-first-match-short-circuit satisfied)")
 (active . t))

((expr . "(канон-закон-символьний-поверхня)")
 (expected . "(canon-law-result symbolic-surface satisfied)")
 (active . t))

((expr . "(канон-відповідає?)")
 (expected . "(canon-conformance satisfied)")
 (active . t))
