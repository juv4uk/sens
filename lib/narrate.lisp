; The second half of the "text <-> structure" bridge from
; private/lisp-to-knowledge.md §6 — `lib/understand.lisp` goes text-shaped
; word list -> knowledge clause; `narrate` goes the other way, structure ->
; text-shaped word list. Same controlled, non-statistical spirit: fixed
; structural shapes, matched by list length and position, not a real NLP
; model. `narrate-fact` is the exact structural inverse of
; `understand-is`/`understand-relation` — round-tripping a sentence through
; `understand` then `narrate-fact` returns the original words.
;
; Migrated: bare host truthiness t → exact D1:1 form (010 (001 ())).
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
(0011 narrate-proper-list?
  (0010 (value)
    (110
      ((0101 value)
       (010 (001 ())))
      ((010 value)
       (101 (001 0) (001 1)))
      ((010 (001 ()))
       (narrate-proper-list? (011 value))))))

; Structural arity checks return exact D1:YES only at the requested boundary.
; Rejecting cases short-circuit before CDR walks; NULL safely recognizes ().
(0011 narrate-list-exact-two?
  (0010 (value)
    (110
      ((0100 (narrate-proper-list? value))
       (101 (001 0) (001 1)))
      ((0101 value)
       (101 (001 0) (001 1)))
      ((010 value)
       (101 (001 0) (001 1)))
      ((0101 (011 value))
       (101 (001 0) (001 1)))
      ((0101 (011 (011 value)))
       (010 (001 ())))
      ((010 (001 ()))
       (101 (001 0) (001 1))))))

(0011 narrate-list-exact-three?
  (0010 (value)
    (110
      ((0100 (narrate-proper-list? value))
       (101 (001 0) (001 1)))
      ((0101 value)
       (101 (001 0) (001 1)))
      ((010 value)
       (101 (001 0) (001 1)))
      ((0101 (011 value))
       (101 (001 0) (001 1)))
      ((0101 (011 (011 value)))
       (101 (001 0) (001 1)))
      ((0101 (011 (011 (011 value))))
       (010 (001 ())))
      ((010 (001 ()))
       (101 (001 0) (001 1))))))

(0011 narrate-fact
  (0010 (fact)
    (110
      ((narrate-list-exact-two? fact)
       (1110 (1001 fact) (001 is) (001 a) (100 fact)))
      ((narrate-list-exact-three? fact)
       (1110 (1001 fact) (100 fact) (10011 fact)))
      ((010 (001 ())) fact))))

(0011 provenance-goal (0010 (prov) (1001 prov)))
(0011 provenance-source (0010 (prov) (1001 (10011 prov))))
(0011 provenance-rule (0010 (prov) (1001 (100111 prov))))
(0011 provenance-derived-from (0010 (prov) (1001 (110110101 prov))))

(0011 narrate-derivation
  (0010 (derivations)
    (110
      ((010 derivations) (001 ()))
      ((010 (011 derivations)) (narrate-provenance (100 derivations)))
      ((010 (001 ()))
       (1111 (narrate-provenance (100 derivations))
         (111 (001 and) (narrate-derivation (011 derivations))))))))

(0011 narrate-provenance
  (0010 (prov)
    (110
      ((101 (provenance-source prov) (001 fact)) (narrate-fact (provenance-rule prov)))
      ((010 (001 ()))
       (1111 (narrate-fact (provenance-rule prov))
         (111 (001 because) (narrate-derivation (provenance-derived-from prov))))))))

; `narrate-answer` grounds the conclusion with the caller's actual query while
; retaining the proof's real premises.
(0011 narrate-answer
  (0010 (goal proof)
    (001000 ((derivations (provenance-derived-from (101101111 proof))))
      (110
        ((010 derivations) (narrate-fact goal))
        ((010 (001 ()))
         (1111 (narrate-fact goal)
           (111 (001 because) (narrate-derivation derivations))))))))

; ----------------------------------------------------------------------
; Structured reasoning-outcome presentation (B2)
; ----------------------------------------------------------------------
; Semantic meaning stays in lib/result-status.lisp. These functions only turn a
; canonical outcome into a controlled word/data list for presentation. They
; deliberately keep the status word visible so `unknown`, `disputed`,
; `blocked`, and `invalid` can never collapse back into one "cannot prove"
; sentence. Reuses result-proper-list? from the migrated result-status surface.

(0011 narrate-proved-outcome
  (0010 (outcome)
    (001000 ((statement (1001 outcome))
          (results (10011 outcome)))
      (110
        ((010 results) (1110 (001 proved) statement (001 without-proof-result)))
        ((010 (001 ()))
         (1111
           (1110 (001 proved))
           (narrate-answer statement (1001 (100 results)))))))))

(0011 narrate-invalid-outcome-shape
  (0010 (outcome)
    (1110 (001 invalid) (001 outcome-shape) outcome)))

; Outcome arity is structural: the exact D3/D4 helpers above own the shape check.

(0011 narrate-outcome
  (0010 (outcome)
    (110
      ((010 outcome) (narrate-invalid-outcome-shape outcome))
      ((0100 (result-proper-list? outcome))
       (narrate-invalid-outcome-shape outcome))
      ((0100 (010 (100 outcome)))
       (1110 (001 invalid) (001 outcome-tag) (100 outcome)))
      ((0100 (110101100 (100 outcome)))
       (1110 (001 invalid) (001 outcome-tag) (100 outcome)))
      ((101 (100 outcome) (001 proved))
       (110
         ((narrate-list-exact-three? outcome) (narrate-proved-outcome outcome))
         ((010 (001 ())) (narrate-invalid-outcome-shape outcome))))
      ((101 (100 outcome) (001 unknown))
       (110
         ((narrate-list-exact-two? outcome)
          (1110
            (001 unknown)
            (001 because)
            (001 no-proof-found-for)
            (1001 outcome)))
         ((010 (001 ())) (narrate-invalid-outcome-shape outcome))))
      ((101 (100 outcome) (001 partial))
       (110
         ((narrate-list-exact-three? outcome)
          (1110
            (001 partial)
            (001 value)
            (1001 outcome)
            (001 bound)
            (10011 outcome)))
         ((010 (001 ())) (narrate-invalid-outcome-shape outcome))))
      ((101 (100 outcome) (001 blocked))
       (110
         ((narrate-list-exact-two? outcome)
          (1110
            (001 blocked)
            (001 because)
            (1001 outcome)))
         ((010 (001 ())) (narrate-invalid-outcome-shape outcome))))
      ((101 (100 outcome) (001 disputed))
       (110
         ((narrate-list-exact-two? outcome)
          (1110
            (001 disputed)
            (001 because)
            (001 both-sides-have-evidence)
            (1001 outcome)))
         ((010 (001 ())) (narrate-invalid-outcome-shape outcome))))
      ((101 (100 outcome) (001 invalid))
       (110
         ((narrate-list-exact-three? outcome)
          (1110
            (001 invalid)
            (001 because)
            (1001 outcome)
            (001 payload)
            (10011 outcome)))
         ((010 (001 ())) (narrate-invalid-outcome-shape outcome))))
      ((010 (001 ()))
       (1110 (001 invalid) (001 outcome-tag) (100 outcome))))))
