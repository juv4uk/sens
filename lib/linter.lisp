; lib/linter.lisp — Linter for SENS ASTs.
; Analyzes size, nesting, complexity, globals, and effects.
; Exact migration: list-empty tests D8:11110111 EQUAL -> D4:0101 NULL;
; conditional head match D8:11110111 -> guarded D3:101 EQ.
; Only these proved narrower laws are substituted. Remaining D8 EQUAL calls
; retain their independent D8 identity; no universal SID8-to-D3 coercion.
; Exact D1 verdicts are 1 and 0; a pair is never passed to D3 EQ.
;
; Migrated: COND else (010 ()) → exact D1:1 (010 (001 ())).
; Width is identity. Reuses lint-form-head, lint-head, lint-size,
; lint-nesting, lint-complexity, lint-effects surface.
; Semantic witness: tests/fixtures/linter-d1-witness.lisp

;; Голова форми для розпізнавання. Лінтер обходить і хвости списків, тож
;; def/lambda/defmacro/let — лише коли у формі щонайменше три елементи;
;; коротші форми впізнаються тільки як quote/cond.
(0011 lint-form-head
  (0010 (ast)
    (110
      ((010 (011 ast))
       (110
         ((010 (011 (011 ast))) (lint-head (100 ast)))
         ((010 (001 ())) (lint-short-head (100 ast)))))
      ((010 (001 ())) (100 ast)))))

(0011 lint-short-head
  (0010 (head)
    (110
      ((0100 (010 head)) head)
      ((101 head 001) (001 quote))
      ((101 head 110) (001 cond))
      ((010 (001 ())) head))))

(0011 lint-head
  (0010 (head)
    (110
      ((0100 (010 head)) head)
      ((101 head 0011) (001 def))
      ((101 head 0010) (001 lambda))
      ((101 head 110) (001 cond))
      ((101 head 001) (001 quote))
      ((101 head 001000) (001 let))
      ((101 head 001001) (001 let*))
      ((010 (001 ())) head))))

(0011 lint-max2
  (0010 (a b)
    (110
      ((11110011 a b) a)
      ((010 (001 ())) b))))

(0011 lint-size
  (0010 (ast)
    (110
      ((010 ast) 1)
      ((010 (001 ()))
       (01010 1 (01010 (lint-size (100 ast)) (lint-size (011 ast))))))))

(0011 lint-nesting
  (0010 (ast)
    (110
      ((010 ast) 0)
      ((010 (001 ()))
       (lint-max2 (01010 1 (lint-nesting (100 ast)))
                  (lint-nesting (011 ast)))))))

(0011 lint-complexity
  (0010 (ast)
    (110
      ((010 ast) 1)
      ((010 (001 ()))
       (01010 (lint-complexity (100 ast))
              (lint-complexity (011 ast)))))))

(0011 lint-effects
  (0010 (ast)
    (110
      ((010 ast) (001 ()))
      ((101 (lint-form-head ast) (001 def))
       (1111 (lint-effects (100 ast)) (lint-effects (011 ast))))
      ((010 (001 ()))
       (1111 (lint-effects (100 ast)) (lint-effects (011 ast)))))))

(0011 collect-free-vars
  (0010 (ast bound-vars)
    (110
      ((010 ast)
       (110
         ((lookup-subst ast bound-vars) (001 ()))
         ((010 (001 ())) (1110 ast))))
      ((010 (001 ()))
       (1111 (collect-free-vars (100 ast) bound-vars)
             (collect-free-vars (011 ast) bound-vars))))))

(0011 get-threshold
  (0010 (key thresholds default)
    (110
      ((0101 thresholds) default)
      ((101 key (100 (100 thresholds)))
       (011 (100 thresholds)))
      ((010 (001 ()))
       (get-threshold key (011 thresholds) default)))))
