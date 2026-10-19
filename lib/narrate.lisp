; The second half of the "text <-> structure" bridge from
; private/lisp-to-knowledge.md §6 — `lib/understand.lisp` goes text-shaped
; word list -> knowledge clause; `narrate` goes the other way, structure ->
; text-shaped word list. Same controlled, non-statistical spirit: fixed
; structural shapes, matched by list length and position, not a real NLP
; model. `narrate-fact` is the exact structural inverse of
; `understand-is`/`understand-relation` — round-tripping a sentence through
; `understand` then `narrate-fact` returns the original words.
;
; Exact-domain source uses the one-bit D1 words 0/1 directly; no compatibility projection.
; Reuses result-proper-list? from lib/result-status.lisp and existing
; project selectors. Width is identity; every bit of the domain address valued.
;
; `narrate-provenance` explains *why*, walking a `provenance` record
; (lib/reason.lisp) into a word list joined by `because`/`and`. It narrates
; each node's `rule` field, not its `goal` field.

; Structural list-shape tests replace D6 LENGTH + D8 EQUAL and naked 2/3.
; All branches return exact D1; list data never acquires numeric truthiness.
; NULL is the admitted exact D4 empty-list predicate and returns D1.
; It avoids trying to call atom-only EQ on structural ().
(визначити narrate-proper-list?
  (функція (значення)
    (за-умовою
      ((порожній? значення)
       так)
      ((атом? значення)
       ні)
      (так
       (narrate-proper-list? (решта значення))))))

; Structural arity checks return exact D1:YES only at the requested boundary.
; Rejecting cases short-circuit before CDR walks; NULL safely recognizes ().
(визначити narrate-list-exact-two?
  (функція (значення)
    (за-умовою
      ((хибне? (narrate-proper-list? значення))
       ні)
      ((порожній? значення)
       ні)
      ((атом? значення)
       ні)
      ((порожній? (решта значення))
       ні)
      ((порожній? (решта (решта значення)))
       так)
      (так
       ні))))

(визначити narrate-list-exact-three?
  (функція (значення)
    (за-умовою
      ((хибне? (narrate-proper-list? значення))
       ні)
      ((порожній? значення)
       ні)
      ((атом? значення)
       ні)
      ((порожній? (решта значення))
       ні)
      ((порожній? (решта (решта значення)))
       ні)
      ((порожній? (решта (решта (решта значення))))
       так)
      (так
       ні))))

(визначити пояснити-факт
  (функція (факт)
    (за-умовою
      ((narrate-list-exact-two? факт)
       (список (друге факт) (як-є is) (як-є a) (перше факт)))
      ((narrate-list-exact-three? факт)
       (список (друге факт) (перше факт) (третє факт)))
      (так факт))))

(визначити походження-ціль (функція (походження) (друге походження)))
(визначити походження-джерело (функція (походження) (друге (третє походження))))
(визначити походження-правило (функція (походження) (друге (четверте походження))))
(визначити походження-похідний-з (функція (походження) (друге (п'ятий походження))))

(визначити пояснити-виведення
  (функція (виведення)
    (за-умовою
      ((атом? виведення) (як-є ()))
      ((атом? (решта виведення)) (пояснити-походження (перше виведення)))
      (так
       (приєднати (пояснити-походження (перше виведення))
         (сполучити (як-є and) (пояснити-виведення (решта виведення))))))))

(визначити пояснити-походження
  (функція (походження)
    (за-умовою
      ((тотожне? (походження-джерело походження) (як-є fact)) (пояснити-факт (походження-правило походження)))
      (так
       (приєднати (пояснити-факт (походження-правило походження))
         (сполучити (як-є because) (пояснити-виведення (походження-похідний-з походження))))))))

; `narrate-answer` grounds the conclusion with the caller's actual query while
; retaining the proof's real premises.
(визначити пояснити-відповідь
  (функція (мета доказ)
    (нехай ((виведення (походження-похідний-з (походження доказ))))
      (за-умовою
        ((атом? виведення) (пояснити-факт мета))
        (так
         (приєднати (пояснити-факт мета)
           (сполучити (як-є because) (пояснити-виведення виведення))))))))

; ----------------------------------------------------------------------
; Structured reasoning-outcome presentation (B2)
; ----------------------------------------------------------------------
; Exact reader: unconditional COND guards are the one-bit D1:YES (1).
; Semantic meaning stays in lib/result-status.lisp. These functions only turn a
; canonical outcome into a controlled word/data list for presentation. They
; deliberately keep the status word visible so `unknown`, `disputed`,
; `blocked`, and `invalid` can never collapse back into one "cannot prove"
; sentence. Reuses result-proper-list? from the migrated result-status surface.

(визначити пояснити-результат-із-доказом
  (функція (підсумок)
    (нехай ((твердження (друге підсумок))
          (результати (третє підсумок)))
      (за-умовою
        ((атом? результати) (список (як-є proved) твердження (як-є without-proof-result)))
        (так
         (приєднати
           (список (як-є proved))
           (пояснити-відповідь твердження (друге (перше результати)))))))))

(визначити пояснити-неприпустиму-структуру-результату
  (функція (підсумок)
    (список (як-є invalid) (як-є outcome-shape) підсумок)))

; Outcome arity is structural: the exact D3/D4 helpers above own the shape check.

(визначити пояснити-підсумок
  (функція (підсумок)
    (за-умовою
      ((атом? підсумок) (пояснити-неприпустиму-структуру-результату підсумок))
      ((хибне? (результат-є-правильним-списком? підсумок))
       (пояснити-неприпустиму-структуру-результату підсумок))
      ((хибне? (атом? (перше підсумок)))
       (список (як-є invalid) (як-є outcome-tag) (перше підсумок)))
      ((хибне? (символ? (перше підсумок)))
       (список (як-є invalid) (як-є outcome-tag) (перше підсумок)))
      ((тотожне? (перше підсумок) (як-є proved))
       (за-умовою
         ((narrate-list-exact-three? підсумок) (пояснити-результат-із-доказом підсумок))
         (так (пояснити-неприпустиму-структуру-результату підсумок))))
      ((тотожне? (перше підсумок) (як-є unknown))
       (за-умовою
         ((narrate-list-exact-two? підсумок)
          (список
            (як-є unknown)
            (як-є because)
            (як-є no-proof-found-for)
            (друге підсумок)))
         (так (пояснити-неприпустиму-структуру-результату підсумок))))
      ((тотожне? (перше підсумок) (як-є partial))
       (за-умовою
         ((narrate-list-exact-three? підсумок)
          (список
            (як-є partial)
            (як-є value)
            (друге підсумок)
            (як-є bound)
            (третє підсумок)))
         (так (пояснити-неприпустиму-структуру-результату підсумок))))
      ((тотожне? (перше підсумок) (як-є blocked))
       (за-умовою
         ((narrate-list-exact-two? підсумок)
          (список
            (як-є blocked)
            (як-є because)
            (друге підсумок)))
         (так (пояснити-неприпустиму-структуру-результату підсумок))))
      ((тотожне? (перше підсумок) (як-є disputed))
       (за-умовою
         ((narrate-list-exact-two? підсумок)
          (список
            (як-є disputed)
            (як-є because)
            (як-є both-sides-have-evidence)
            (друге підсумок)))
         (так (пояснити-неприпустиму-структуру-результату підсумок))))
      ((тотожне? (перше підсумок) (як-є invalid))
       (за-умовою
         ((narrate-list-exact-three? підсумок)
          (список
            (як-є invalid)
            (як-є because)
            (друге підсумок)
            (як-є payload)
            (третє підсумок)))
         (так (пояснити-неприпустиму-структуру-результату підсумок))))
      (так
       (список (як-є invalid) (як-є outcome-tag) (перше підсумок))))))

; D9 Ukrainian callable projections. Names/codes: lib/domains/d9.lisp;
; source laws: knowledge/d9-semantic-layer-harvest-v1.json.
; SENS DEFINE aliases existing Lisp closures; NO new native D9 dispatch.
; D9:000011000
(визначити narrate-fact пояснити-факт)
; D9:000111000
(визначити narrate-derivation пояснити-виведення)
; D9:000011011
(визначити narrate-provenance пояснити-походження)
; D9:000000001
(визначити narrate-answer пояснити-відповідь)
; D9:000100110
(визначити narrate-outcome пояснити-підсумок)

; D10 full-ukr peers: exact identity = lib/domains/d10.lisp; DEFINE alias, no new dispatch.
; D10:0010101110
(визначити narrate-invalid-outcome-shape пояснити-неприпустиму-структуру-результату)
; D10:0010010110
(визначити результат-є-правильним-списком? result-proper-list?)
; D10:0010101101
(визначити narrate-proved-outcome пояснити-результат-із-доказом)

; opt-in повна укр-поверхня: exact identity = lib/domains/d*.lisp; DEFINE-аліас, без нової диспетчеризації.
(визначити provenance-derived-from походження-похідний-з)
(визначити provenance-rule походження-правило)
(визначити provenance-source походження-джерело)
(визначити provenance-goal походження-ціль)
