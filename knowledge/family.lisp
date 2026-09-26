;; knowledge/family.lisp — replaces physics.lisp/astronomy.lisp as the toy-sized
;; demo domains (PLAN.md item 12): both were single-hop only (one rule, no
;; recursion), never exercising the recursive-logic capability lib/reason.lisp
;; itself documents in its own header comment ("standardizing apart ...
;; allows for recursive logic!") — this domain uses `ancestor` specifically
;; to exercise that, not just add more toy facts.
(defmodule family (00000001 (
  ;; Facts — a small family tree, three generations
  ((parent tom bob))
  ((parent tom liz))
  ((parent bob ann))
  ((parent bob pat))
  ((parent pat jim))

  ;; Rules
  ;; grandparent: one intermediate hop, the same shape as astronomy.lisp's
  ;; old (orbits) rule — kept as a baseline, not the point of this file.
  ((grandparent (var x) (var y)) (parent (var x) (var z)) (parent (var z) (var y)))
  ;; ancestor: recursive — the base case (direct parent) and the recursive
  ;; case (parent of an ancestor) together derive tom's whole descendant
  ;; line (bob, liz, ann, pat, jim) without a fixed hop count, unlike
  ;; grandparent above. This is the actual point of the domain.
  ((ancestor (var x) (var y)) (parent (var x) (var y)))
  ((ancestor (var x) (var y)) (parent (var x) (var z)) (ancestor (var z) (var y)))
)))
