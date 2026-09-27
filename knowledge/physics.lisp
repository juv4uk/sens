;; knowledge/physics.lisp
(defmodule physics (00000001 (
  ;; Rule: Anything with mass is attracted by gravity
  ((attracted-by-gravity (var x)) (has-mass (var x)))
  
  ;; Rule: If something is a planet, it has mass
  ((has-mass (var x)) (planet (var x)))

  ;; Facts
  ((has-mass apple))
)))
