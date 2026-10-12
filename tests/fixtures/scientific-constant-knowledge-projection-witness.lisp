; #305 — preserve useful scientific-constant -> knowledge projection laws
; before retiring stale Rust semantic sentinels.
;
; Semantic meaning remains in Lisp libraries. This witness proves only:
;   * the speed-of-light record projects to exactly seven clauses;
;   * the projected batch is admitted by the existing knowledge validator;
;   * projection is pure: the global knowledge journal is unchanged.
;
; It deliberately does not advise/import the clauses and does not turn this
; evidence file into a second scientific-constant registry.

(load "lib/core.lisp")
(load "lib/unify.lisp")
(load "lib/reason.lisp")
(load "lib/forward.lisp")
(load "lib/knowledge.lisp")
(load "lib/result-status.lisp")
(load "lib/quantity.lisp")
(load "lib/si.lisp")

(0011 scientific-constant-knowledge-projection-observation
  (0010 ()
    (001001 ((before *knowledge-journal*)
           (clauses
             (scientific-constant->clauses
               si:defining-speed-of-light))
           (count (000000 clauses))
           (admitted (knowledge-clauses-valid? clauses))
           (journal-relation
             (11110111 before *knowledge-journal*)))
      (1110 count admitted journal-relation))))

(0011 scientific-constant-knowledge-projection-witness
  (0010 ()
    (001000 ((observation
            (scientific-constant-knowledge-projection-observation)))
      (110
        ((11110111
           observation
           (001 (7 t (1))))
         (1)
         (001
           (scientific-constant-knowledge-projection-witness
             (status pass))))
        ((11110111
           observation
           (001 (7 t (1))))
         (0)
         (1110
           (001 scientific-constant-knowledge-projection-witness)
           (001 (status fail))
           (1110 (001 actual) observation)
           (001
             (expected
               (7 t (1))))))))))

(scientific-constant-knowledge-projection-witness)
