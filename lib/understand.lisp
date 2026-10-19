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

(визначити прибрати-артикль
  (функція (слова)
    (за-умовою
      ((атом? слова) (як-є ()))
      ((тотожне? (перше слова) (як-є a)) (решта слова))
      ((тотожне? (перше слова) (як-є an)) (решта слова))
      (так слова))))

(визначити побудувати-факт-є
  (функція (слова)
    (список (список (перше (прибрати-артикль (решта-решти слова))) (перше слова)))))

(визначити побудувати-факт-відношення
  (функція (слова)
    (список (список (друге слова) (перше слова) (третє слова)))))

(визначити побудувати-універсальне-правило
  (функція (слова)
    (список (список (як-є has) (список (як-є var) (як-є w)) (четверте слова))
          (список (друге слова) (список (як-є var) (як-є w))))))

(визначити розібрати-контрольоване-твердження
  (функція (слова)
    (за-умовою
      ((атом? слова) (як-є ()))
      ((тотожне? (перше слова) (як-є all))
       (розібрати-загальний слова))
      ((тотожне? (друге слова) (як-є is))
       (розібрати-є слова))
      (так
       (розібрати-відношення слова)))))

; `understand-query` is the goal-shaped complement of `understand`.
; Controlled, structural, deterministic: no morphology, no network, no LLM.
(визначити побудувати-запит-є
  (функція (слова)
    (список (перше (прибрати-артикль (решта-решти слова))) (друге слова))))

(визначити побудувати-запит-відношення
  (функція (слова)
    (список (третє слова) (друге слова) (четверте слова))))

(визначити розібрати-контрольований-запит
  (функція (слова)
    (за-умовою
      ((атом? слова) (як-є ()))
      ((тотожне? (перше слова) (як-є is))
       (розібрати-запит-є слова))
      ((тотожне? (перше слова) (як-є does))
       (розібрати-запит-відношення слова))
      (так
       (як-є ())))))

; D9 Ukrainian callable projections. Names/codes: lib/domains/d9.lisp;
; source laws: knowledge/d9-semantic-layer-harvest-v1.json.
; SENS DEFINE aliases existing Lisp closures; NO new native D9 dispatch.
; D9:000001011
(визначити розібрати-є побудувати-факт-є)
; D9:000001100
(визначити розібрати-відношення побудувати-факт-відношення)
; D9:000011111
(визначити розібрати-загальний побудувати-універсальне-правило)
; D9:000110001
(визначити розібрати розібрати-контрольоване-твердження)
; D9:000111001
(визначити розібрати-запит-є побудувати-запит-є)
; D9:000110000
(визначити розібрати-запит-відношення побудувати-запит-відношення)
; D9:000101010
(визначити розібрати-запит розібрати-контрольований-запит)
