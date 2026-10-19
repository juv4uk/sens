; PAIP FIND-IF-ANYWHERE: exact D1 verdicts from the pinned source law.
; D10:0011010011 remains a research candidate; this source-level helper does not admit a D10 opcode.
; PAIP applies the predicate to atoms including (); the empty-list case therefore tests ATOM semantics.
; Expected D1 vector: nested hit, miss, NIL atom, false predicate, hit on the right subtree -> (1 0 1 0 1).
(список
  (є-листок-дерева-що-задовольняє-предикат?
    (функція (елемент) (equal? елемент (як-є слива)))
    (список (список (як-є яблуко) (список (як-є слива))) (як-є груша)))
  (є-листок-дерева-що-задовольняє-предикат?
    (функція (елемент) (equal? елемент (як-є слива)))
    (список (список (як-є яблуко)) (як-є груша)))
  (є-листок-дерева-що-задовольняє-предикат?
    (функція (елемент) (атом? елемент))
    (як-є ()))
  (є-листок-дерева-що-задовольняє-предикат?
    (функція (елемент) ні)
    (як-є (яблуко груша)))
  (є-листок-дерева-що-задовольняє-предикат?
    (функція (елемент) (equal? елемент (як-є слива)))
    (список (як-є яблуко) (список (як-є груша) (як-є слива)))))

; opt-in повна укр-поверхня: exact identity = lib/domains/d*.lisp; DEFINE-аліас, без нової диспетчеризації.
(визначити список list)
