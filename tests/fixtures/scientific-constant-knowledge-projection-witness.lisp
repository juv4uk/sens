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

(def scientific-constant-knowledge-projection-observation
  (lambda ()
    (let* ((before *knowledge-journal*)
           (clauses
             (scientific-constant->clauses
               si:defining-speed-of-light))
           (count (length clauses))
           (admitted (knowledge-clauses-valid? clauses))
           (journal-relation
             (equal? before *knowledge-journal*)))
      (list count admitted journal-relation))))

(def scientific-constant-knowledge-projection-witness
  (lambda ()
    (let ((observation
            (scientific-constant-knowledge-projection-observation)))
      (cond
        ((equal?
           observation
           (quote (7 t (1))))
         (1)
         (quote
           (scientific-constant-knowledge-projection-witness
             (status pass))))
        ((equal?
           observation
           (quote (7 t (1))))
         (0)
         (list
           (quote scientific-constant-knowledge-projection-witness)
           (quote (status fail))
           (list (quote actual) observation)
           (quote
             (expected
               (7 t (1))))))))))

(scientific-constant-knowledge-projection-witness)
