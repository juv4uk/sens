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

(визначити strip-article
  (функція (words)
    (за-умовою
      ((атом? words) (як-є ()))
      ((тотожне? (перше words) (як-є a)) (решта words))
      ((тотожне? (перше words) (як-є an)) (решта words))
      (так words))))

(визначити understand-is
  (функція (words)
    (список (список (перше (strip-article (решта-решти words))) (перше words)))))

(визначити understand-relation
  (функція (words)
    (список (список (друге words) (перше words) (третє words)))))

(визначити understand-universal
  (функція (words)
    (список (список (як-є has) (список (як-є var) (як-є w)) (четверте words))
          (список (друге words) (список (як-є var) (як-є w))))))

(визначити understand
  (функція (words)
    (за-умовою
      ((атом? words) (як-є ()))
      ((тотожне? (перше words) (як-є all))
       (розібрати-загальний words))
      ((тотожне? (друге words) (як-є is))
       (розібрати-є words))
      (так
       (розібрати-відношення words)))))

; `understand-query` is the goal-shaped complement of `understand`.
; Controlled, structural, deterministic: no morphology, no network, no LLM.
(визначити understand-query-is
  (функція (words)
    (список (перше (strip-article (решта-решти words))) (друге words))))

(визначити understand-query-relation
  (функція (words)
    (список (третє words) (друге words) (четверте words))))

(визначити understand-query
  (функція (words)
    (за-умовою
      ((атом? words) (як-є ()))
      ((тотожне? (перше words) (як-є is))
       (розібрати-запит-є words))
      ((тотожне? (перше words) (як-є does))
       (розібрати-запит-відношення words))
      (так
       (як-є ())))))

; D9 Ukrainian callable projections. Names/codes: lib/domains/d9.lisp;
; source laws: knowledge/d9-semantic-layer-harvest-v1.json.
; SENS DEFINE aliases existing Lisp closures; NO new native D9 dispatch.
; D9:000001011
(визначити розібрати-є understand-is)
; D9:000001100
(визначити розібрати-відношення understand-relation)
; D9:000011111
(визначити розібрати-загальний understand-universal)
; D9:000110001
(визначити розібрати understand)
; D9:000111001
(визначити розібрати-запит-є understand-query-is)
; D9:000110000
(визначити розібрати-запит-відношення understand-query-relation)
; D9:000101010
(визначити розібрати-запит understand-query)
