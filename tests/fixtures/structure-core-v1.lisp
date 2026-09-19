; #230 STRUCTURE-CORE-1 — Lisp-owned freeze witnesses.
; These rows deliberately contain no predicate/control expectations. They freeze
; only structural behavior so later #218/#217 truth migration cannot redefine
; quote/cons/car/cdr by accident.

((expr . "(quote (alpha beta))")
 (expected . "(alpha beta)")
 (structure-core . t)
 (semantic-id . "00000001")
 (note . "quote returns syntax as ordinary data"))

((expr . "(quote (alpha . beta))")
 (expected . "(alpha . beta)")
 (structure-core . t)
 (semantic-id . "00000001")
 (note . "quote preserves dotted structure without assigning truth meaning"))

((expr . "(cons (quote alpha) (quote beta))")
 (expected . "(alpha . beta)")
 (structure-core . t)
 (semantic-id . "00000100")
 (note . "cons constructs a dotted pair from arbitrary values"))

((expr . "(cons (quote alpha) (cons (quote beta) (quote ())))")
 (expected . "(alpha beta)")
 (structure-core . t)
 (semantic-id . "00000100")
 (note . "cons plus structural () constructs a proper list"))

((expr . "(car (cons (quote left) (quote right)))")
 (expected . "left")
 (structure-core . t)
 (semantic-id . "00000101")
 (note . "car(cons x y) returns x independent of any truth convention"))

((expr . "(cdr (cons (quote left) (quote right)))")
 (expected . "right")
 (structure-core . t)
 (semantic-id . "00000110")
 (note . "cdr(cons x y) returns y independent of any truth convention"))

((expr . "(car (cons (quote ()) (quote tail)))")
 (expected . "()")
 (structure-core . t)
 (semantic-id . "00000101")
 (note . "car may return () as data; this result is not a logical NO"))

((expr . "(cdr (cons (quote head) (quote ())))")
 (expected . "()")
 (structure-core . t)
 (semantic-id . "00000110")
 (note . "cdr may return structural empty-list data without invoking truth semantics"))
