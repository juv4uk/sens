; Negative PAIP tree-search witness: a predicate must return exact D1 even when the tree root is an atom.
; Structural () is not D1:NO and must not escape the atomic base case.
(дерево-має-збіг?
  (функція (елемент) (як-є ()))
  (як-є яблуко))
