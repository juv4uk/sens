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

(00001001 scientific-constant-knowledge-projection-observation
  (00001000 ()
    (10011101 ((before *knowledge-journal*)
           (clauses
             (scientific-constant->clauses
               si:defining-speed-of-light))
           (count (00101000 clauses))
           (admitted (knowledge-clauses-valid? clauses))
           (journal-relation
             (00100010 before *knowledge-journal*)))
      (00100111 count admitted journal-relation))))

(00001001 scientific-constant-knowledge-projection-witness
  (00001000 ()
    (10011100 ((observation
            (scientific-constant-knowledge-projection-observation)))
      (00000111
        ((00100010
           observation
           (00000001 (7 t (1))))
         (00000001
           (scientific-constant-knowledge-projection-witness
             (status pass))))
        ((00100010 (00100010
           observation
           (00000001 (7 t (1))))
           (00100010 (00000001 d1-no-left) (00000001 d1-no-right)))
         (00100111
           (00000001 scientific-constant-knowledge-projection-witness)
           (00000001 (status fail))
           (00100111 (00000001 actual) observation)
           (00000001
             (expected
               (7 t (1))))))))))

(scientific-constant-knowledge-projection-witness)
