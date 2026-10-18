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
  (функція (value)
    (за-умовою
      ((порожній? value)
       так)
      ((атом? value)
       ні)
      (так
       (narrate-proper-list? (решта value))))))

; Structural arity checks return exact D1:YES only at the requested boundary.
; Rejecting cases short-circuit before CDR walks; NULL safely recognizes ().
(визначити narrate-list-exact-two?
  (функція (value)
    (за-умовою
      ((хибне? (narrate-proper-list? value))
       ні)
      ((порожній? value)
       ні)
      ((атом? value)
       ні)
      ((порожній? (решта value))
       ні)
      ((порожній? (решта (решта value)))
       так)
      (так
       ні))))

(визначити narrate-list-exact-three?
  (функція (value)
    (за-умовою
      ((хибне? (narrate-proper-list? value))
       ні)
      ((порожній? value)
       ні)
      ((атом? value)
       ні)
      ((порожній? (решта value))
       ні)
      ((порожній? (решта (решта value)))
       ні)
      ((порожній? (решта (решта (решта value))))
       так)
      (так
       ні))))

(визначити narrate-fact
  (функція (fact)
    (за-умовою
      ((narrate-list-exact-two? fact)
       (список (друге fact) (як-є is) (як-є a) (перше fact)))
      ((narrate-list-exact-three? fact)
       (список (друге fact) (перше fact) (третє fact)))
      (так fact))))

(визначити provenance-goal (функція (prov) (друге prov)))
(визначити provenance-source (функція (prov) (друге (третє prov))))
(визначити provenance-rule (функція (prov) (друге (четверте prov))))
(визначити provenance-derived-from (функція (prov) (друге (п'ятий prov))))

(визначити narrate-derivation
  (функція (derivations)
    (за-умовою
      ((атом? derivations) (як-є ()))
      ((атом? (решта derivations)) (narrate-provenance (перше derivations)))
      (так
       (приєднати (narrate-provenance (перше derivations))
         (сполучити (як-є and) (narrate-derivation (решта derivations))))))))

(визначити narrate-provenance
  (функція (prov)
    (за-умовою
      ((тотожне? (походження-джерело prov) (як-є fact)) (narrate-fact (походження-правило prov)))
      (так
       (приєднати (narrate-fact (походження-правило prov))
         (сполучити (як-є because) (narrate-derivation (походження-похідний-з prov))))))))

; `narrate-answer` grounds the conclusion with the caller's actual query while
; retaining the proof's real premises.
(визначити narrate-answer
  (функція (goal proof)
    (нехай ((derivations (походження-похідний-з (походження proof))))
      (за-умовою
        ((атом? derivations) (narrate-fact goal))
        (так
         (приєднати (narrate-fact goal)
           (сполучити (як-є because) (narrate-derivation derivations))))))))

; ----------------------------------------------------------------------
; Structured reasoning-outcome presentation (B2)
; ----------------------------------------------------------------------
; Exact reader: unconditional COND guards are the one-bit D1:YES (1).
; Semantic meaning stays in lib/result-status.lisp. These functions only turn a
; canonical outcome into a controlled word/data list for presentation. They
; deliberately keep the status word visible so `unknown`, `disputed`,
; `blocked`, and `invalid` can never collapse back into one "cannot prove"
; sentence. Reuses result-proper-list? from the migrated result-status surface.

(визначити narrate-proved-outcome
  (функція (outcome)
    (нехай ((statement (друге outcome))
          (results (третє outcome)))
      (за-умовою
        ((атом? results) (список (як-є proved) statement (як-є without-proof-result)))
        (так
         (приєднати
           (список (як-є proved))
           (narrate-answer statement (друге (перше results)))))))))

(визначити narrate-invalid-outcome-shape
  (функція (outcome)
    (список (як-є invalid) (як-є outcome-shape) outcome)))

; Outcome arity is structural: the exact D3/D4 helpers above own the shape check.

(визначити narrate-outcome
  (функція (outcome)
    (за-умовою
      ((атом? outcome) (пояснити-неприпустиму-структуру-результату outcome))
      ((хибне? (результат-є-правильним-списком? outcome))
       (пояснити-неприпустиму-структуру-результату outcome))
      ((хибне? (атом? (перше outcome)))
       (список (як-є invalid) (як-є outcome-tag) (перше outcome)))
      ((хибне? (символ? (перше outcome)))
       (список (як-є invalid) (як-є outcome-tag) (перше outcome)))
      ((тотожне? (перше outcome) (як-є proved))
       (за-умовою
         ((narrate-list-exact-three? outcome) (пояснити-результат-із-доказом outcome))
         (так (пояснити-неприпустиму-структуру-результату outcome))))
      ((тотожне? (перше outcome) (як-є unknown))
       (за-умовою
         ((narrate-list-exact-two? outcome)
          (список
            (як-є unknown)
            (як-є because)
            (як-є no-proof-found-for)
            (друге outcome)))
         (так (пояснити-неприпустиму-структуру-результату outcome))))
      ((тотожне? (перше outcome) (як-є partial))
       (за-умовою
         ((narrate-list-exact-three? outcome)
          (список
            (як-є partial)
            (як-є value)
            (друге outcome)
            (як-є bound)
            (третє outcome)))
         (так (пояснити-неприпустиму-структуру-результату outcome))))
      ((тотожне? (перше outcome) (як-є blocked))
       (за-умовою
         ((narrate-list-exact-two? outcome)
          (список
            (як-є blocked)
            (як-є because)
            (друге outcome)))
         (так (пояснити-неприпустиму-структуру-результату outcome))))
      ((тотожне? (перше outcome) (як-є disputed))
       (за-умовою
         ((narrate-list-exact-two? outcome)
          (список
            (як-є disputed)
            (як-є because)
            (як-є both-sides-have-evidence)
            (друге outcome)))
         (так (пояснити-неприпустиму-структуру-результату outcome))))
      ((тотожне? (перше outcome) (як-є invalid))
       (за-умовою
         ((narrate-list-exact-three? outcome)
          (список
            (як-є invalid)
            (як-є because)
            (друге outcome)
            (як-є payload)
            (третє outcome)))
         (так (пояснити-неприпустиму-структуру-результату outcome))))
      (так
       (список (як-є invalid) (як-є outcome-tag) (перше outcome))))))

; D9 Ukrainian callable projections. Names/codes: lib/domains/d9.lisp;
; source laws: knowledge/d9-semantic-layer-harvest-v1.json.
; SENS DEFINE aliases existing Lisp closures; NO new native D9 dispatch.
; D9:000011000
(визначити пояснити-факт narrate-fact)
; D9:000111000
(визначити пояснити-виведення narrate-derivation)
; D9:000011011
(визначити пояснити-походження narrate-provenance)
; D9:000000001
(визначити пояснити-відповідь narrate-answer)
; D9:000100110
(визначити пояснити-підсумок narrate-outcome)

; D10 full-ukr peers: exact identity = lib/domains/d10.lisp; DEFINE alias, no new dispatch.
; D10:0010101110
(визначити пояснити-неприпустиму-структуру-результату narrate-invalid-outcome-shape)
; D10:0010010110
(визначити результат-є-правильним-списком? result-proper-list?)
; D10:0010101101
(визначити пояснити-результат-із-доказом narrate-proved-outcome)

; opt-in повна укр-поверхня: exact identity = lib/domains/d*.lisp; DEFINE-аліас, без нової диспетчеризації.
(визначити походження-похідний-з provenance-derived-from)
(визначити походження-правило provenance-rule)
(визначити походження-джерело provenance-source)
