; #432 research-only RED probe.
; Candidate route under test: if ordinary CONS data were a Church pair,
; calling it with a left selector could derive CAR without PRIM_CAR.
; Expected current result: named callable/type failure, because CONS creates data.

(def pair-value (cons (quote fresh-left) (quote fresh-right)))
(pair-value (lambda (left right) left))
