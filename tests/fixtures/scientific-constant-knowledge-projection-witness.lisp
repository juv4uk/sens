; #305 — preserve useful scientific-constant -> knowledge projection laws
; before retiring stale Rust semantic sentinels.
;
; Semantic meaning remains in Lisp libraries. This witness proves only:
;   * the speed-of-light record projects to exactly seven clauses;
;   * the projected batch is admitted by the existing knowledge validator;
;   * projection is pure: the global knowledge journal is unchanged.
;
; Ukrainian projection only.

(load "lib/core.lisp")
(load "lib/unify.lisp")
(load "lib/reason.lisp")
(load "lib/forward.lisp")
(load "lib/knowledge.lisp")
(load "lib/result-status.lisp")
(load "lib/quantity.lisp")
(load "lib/si.lisp")

(визначити scientific-constant-knowledge-projection-observation
  (функція ()
    (нехай ((before *knowledge-journal*)
           (clauses
             (scientific-constant->clauses
               si:defining-speed-of-light))
           (count (довжина clauses))
           (admitted (knowledge-clauses-valid? clauses))
           (journal-relation
             (однакові? before *knowledge-journal*)))
      (список count admitted journal-relation))))

(визначити scientific-constant-knowledge-projection-witness
  (функція ()
    (нехай ((observation
            (scientific-constant-knowledge-projection-observation)))
      (за-умовою
        ((однакові?
           observation
           (як-є (7 так (1))))
         (як-є
           (scientific-constant-knowledge-projection-witness
             (status pass))))
        (так
         (список
           (як-є scientific-constant-knowledge-projection-witness)
           (як-є (status fail))
           (список (як-є actual) observation)
           (як-є
             (expected
               (7 так (1))))))))))

(scientific-constant-knowledge-projection-witness)
