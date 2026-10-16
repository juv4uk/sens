; Falsifier: TAKE-right(1, [а, б, в]) != [а]; incorrect left edge is D1:0.
(equal?
  (взяти-справа #d24:000000000000000000000001
    (list (quote а) (quote б) (quote в)))
  (list (quote а)))
