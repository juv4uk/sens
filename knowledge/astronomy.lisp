;; knowledge/astronomy.lisp
(defmodule astronomy (001 (
  ;; Facts
  ((planet earth))
  ((planet mars))
  ((star sun))

  ;; Rules
  ((orbits (var p) (var s)) (planet (var p)) (star (var s)))
)))
