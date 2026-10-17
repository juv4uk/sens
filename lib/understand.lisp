; A controlled-natural-language bridge from a fixed sentence shape to a
; knowledge clause `(head . body)`, in `lib/knowledge.lisp`'s / `lib/reason.lisp`'s
; format — the "text -> structure" half of the Advice Taker vision from
; private/lisp-to-knowledge.md §6, deliberately without a real NLP model.
;
; Migrated: two-field COND only; unconditional branches use exact D1:1.
; Pairs with migrated lib/narrate.lisp (structure -> text). Reuses project
; selectors 100/011/1001/10011/100111. Width is identity; every bit valued.
;
; `understand` takes a *word list*, not a raw string — my-lisp has no string
; primitives. Controlled natural language: three fixed sentence shapes,
; matched structurally, not parsed statistically.
;
; Shapes recognized:
;   (X is a Y)   / (X is an Y) / (X is Y)  -> fact:  ((Y X))
;   (X V Y)                                -> fact:  ((V X Y))
;   (all X have Y)                         -> rule:  ((has (var w) Y) (X (var w)))
;
; Query shapes (via `understand-query`):
;   (is X a Y)   / (is X an Y) / (is X Y)  -> goal:  (Y X)
;   (does X V Y)                           -> goal:  (V X Y)

(0011 strip-article
  (0010 (words)
    (110
      ((010 words) (001 ()))
      ((101 (100 words) (001 a)) (011 words))
      ((101 (100 words) (001 an)) (011 words))
      (#d1:1 words))))

(0011 understand-is
  (0010 (words)
    (1110 (1110 (100 (strip-article (0111 words))) (100 words)))))

(0011 understand-relation
  (0010 (words)
    (1110 (1110 (1001 words) (100 words) (10011 words)))))

(0011 understand-universal
  (0010 (words)
    (1110 (1110 (001 has) (1110 (001 var) (001 w)) (100111 words))
          (1110 (1001 words) (1110 (001 var) (001 w))))))

(0011 understand
  (0010 (words)
    (110
      ((010 words) (001 ()))
      ((101 (100 words) (001 all))
       (understand-universal words))
      ((101 (1001 words) (001 is))
       (understand-is words))
      (#d1:1
       (understand-relation words)))))

; `understand-query` is the goal-shaped complement of `understand`.
; Controlled, structural, deterministic: no morphology, no network, no LLM.
(0011 understand-query-is
  (0010 (words)
    (1110 (100 (strip-article (0111 words))) (1001 words))))

(0011 understand-query-relation
  (0010 (words)
    (1110 (10011 words) (1001 words) (100111 words))))

(0011 understand-query
  (0010 (words)
    (110
      ((010 words) (001 ()))
      ((101 (100 words) (001 is))
       (understand-query-is words))
      ((101 (100 words) (001 does))
       (understand-query-relation words))
      (#d1:1
       (001 ())))))

; D9 Ukrainian callable projections. Names/codes: lib/domains/d9.lisp;
; source laws: knowledge/d9-semantic-layer-harvest-v1.json.
; SENS DEFINE aliases existing Lisp closures; NO new native D9 dispatch.
; D9:000001011
(0011 розібрати-є understand-is)
; D9:000001100
(0011 розібрати-відношення understand-relation)
; D9:000011111
(0011 розібрати-загальний understand-universal)
; D9:000110001
(0011 розібрати understand)
; D9:000111001
(0011 розібрати-запит-є understand-query-is)
; D9:000110000
(0011 розібрати-запит-відношення understand-query-relation)
; D9:000101010
(0011 розібрати-запит understand-query)
