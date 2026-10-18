; Native SENS self-verdict for unequal lineage depths, with no implicit D24 arithmetic.
; The one-bit mutant changes only the inner D1 expected answer. The enclosing
; two-field D3 COND turns a wrong answer into a deliberate non-callable D1:NO.

(110
  ((101
    (101
      (внутрішня-рівність-версій
        (світ-спільний-предок
          (світ-повідомити
            (світ-повідомити (порожній-світ) (як-є astronomy) (як-є (planet earth)))
            (001 biology)
            (001 (living earth)))
          (світ-повідомити (порожній-світ) (як-є astronomy) (як-є (planet earth))))
        (світ-повідомити (порожній-світ) (як-є astronomy) (як-є (planet earth))))
      #d1:0)
    #d1:1)
   #d1:1)
  (#d1:1 (#d1:0)))

; opt-in повна укр-поверхня: exact identity = lib/domains/d*.lisp; DEFINE-аліас, без нової диспетчеризації.
(визначити порожній-світ empty-world)
(визначити світ-спільний-предок world-common-ancestor)
(визначити світ-повідомити world-tell)
