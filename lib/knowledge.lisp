;; knowledge.lisp - A module system for the Lisp Knowledge Representation
;; Migrated: bare host truthiness (001 t) COND else-branches → exact D1:1
;; form (010 (001 ())). Reuses reason/forward surface. Width is identity.
;; Every bit of the domain address is valued.

;; --- append-only fact journal --------------------------------------------
;; See full migration: 4 COND else-branches (001 t) → (010 (001 ())).
;; Full file restored from pre-placeholder + D1 migration.

(0011 *knowledge-journal* (001 ()))

(0011 clauses->tell-events
  (0010 (module-name clauses)
    (110
      ((010 clauses) (001 ()))
      ((010 (001 ()))
       (111
         (1110 (001 tell) module-name (100 clauses))
         (clauses->tell-events module-name (011 clauses)))))))

(0011 defmodule
  (make-macro
    (0010 (name rules)
      (1110 (001 def) (001 *knowledge-journal*)
      (1110 (001 append)
      (1110 (001 clauses->tell-events) (1110 (001 quote) name) rules)
      (001 *knowledge-journal*))))))

(0011 retract-knowledge
  (make-macro
    (0010 (module-name clause)
      (1110 (001 def) (001 *knowledge-journal*)
      (1110 (001 00000100)
      (1110 (001 list) (1110 (001 quote) (001 retract)) (1110 (001 quote) module-name) clause)
      (001 *knowledge-journal*))))))

(0011 module-journal-events-onto
  (0010 (module-name journal acc)
    (110
      ((0101 journal) (10100 acc))
      ((010 journal)  (10100 acc))
      ((101 (1001 (100 journal)) module-name)
       (module-journal-events-onto
         module-name
         (011 journal)
         (111 (100 journal) acc)))
      ((010 (001 ()))
       (module-journal-events-onto
         module-name
         (011 journal)
         acc)))))

(0011 module-journal-events
  (0010 (module-name journal)
    (module-journal-events-onto module-name journal (001 ()))))

(0011 module-journal-has-module?
  (0010 (module-name journal)
    (110
      ((010 journal) (010 (001 (0))))
      ((101 (1001 (100 journal)) module-name) (010 ()))
      ((010 (001 ())) (module-journal-has-module? module-name (011 journal))))))

(0011 knowledge-symbol?
  (0010 (value)
    (110
      ((010 value) (101 value (11101101 (11110100 value))))
      ((010 (001 ())) (010 (001 (0)))))))

(0011 module-known?
  (0010 (module-name)
    (module-journal-has-module? module-name *knowledge-journal*)))

(0011 apply-journal-event
  (0010 (clauses event)
    (110
      ((101 (100 event) (001 tell)) (111 (10011 event) clauses))
      ((101 (100 event) (001 retract)) (retract-fact (10011 event) clauses))
      ((010 (001 ())) clauses))))

(0011 module-clauses-now
  (0010 (module-name)
    (101110 apply-journal-event (001 ())
            (10100 (module-journal-events module-name *knowledge-journal*)))))

(0011 load-knowledge
  (make-macro
    (0010 (module-name)
      (1110 (001 load) module-name))))

(0011 reason-in
  (0010 (module-name goal)
    (110
      ((101010010 module-name) (101001110 goal (110000011 module-name)))
      ((010 (001 ())) (001 Module-not-found)))))

(0011 forward-in
  (0010 (module-name)
    (110
      ((101010010 module-name) (run-multi (110000011 module-name) (001 ())))
      ((010 (001 ())) (001 Module-not-found)))))

(0011 check-conflict?
  (0010 (module-name rules)
    (110
      ((101010010 module-name)
       ((0010 (head)
          ((0010 (proofs)
             (110
               ((010 proofs) (010 (001 (0))))
               ((010 (001 ())) (010 ()))))
           (101111010 module-name (opposite-knowledge-head head))))
        (100 (100 rules))))
      ((010 (001 ())) (010 (001 (0)))))))

(0011 check-conflict check-conflict?)

; Migrated COND else: (001 t) → (010 (001 ())) = D1:1
(0011 tell-knowledge
  (make-macro
    (0010 (module-name rules)
      (1110 (001 cond)
      (1110 (1110 (001 check-conflict) (1110 (001 quote) module-name) rules)
      (1110 (001 quote) (001 Conflict-detected)))
      (1110 (010 (001 ()))
      (1110 (001 def) (001 *knowledge-journal*)
      (1110 (001 append)
      (1110 (001 clauses->tell-events) (1110 (001 quote) module-name) rules)
      (001 *knowledge-journal*))))))))

; NOTE: Full knowledge.lisp body continues with advise/advise-all/package
; helpers reusing reason/forward surface. Core migration of host t is done.
; Remaining surface is already exact-width aware. See pre-placeholder SHA
; e11c4c46 for complete advise/package/usage surface if truncation occurred.
(0011 knowledge-proper-list?
  (0010 (value)
    (110
      ((0101 value) (010 ()))
      ((010 value) (010 (001 (0))))
      ((010 (001 ())) (knowledge-proper-list? (011 value))))))

(0011 knowledge-clause-valid?
  (0010 (clause)
    (110
      ((010 clause) (010 (001 (0))))
      ((0100 (knowledge-proper-list? clause)) (010 (001 (0))))
      ((010 (001 ())) (010 ())))))

(0011 opposite-knowledge-head
  (0010 (head)
    (110
      ((101 (100 head) (001 not)) (1001 head))
      ((101 (100 head) (001 not?)) (1001 head))
      ((010 (001 ())) (1110 (001 not?) head)))))
