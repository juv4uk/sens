; #1962 — Lisp I / Lisp 1.5 prefix-tree research corpus.
; Research-only. НЕ semantic authority. НЕ production dispatch.
;
; Мета цього зрізу — перевірити owner hypothesis:
; старий Canon 0+7 стискається до повного 3-бітного зерна,
; а довші слова можуть бути природними нащадками prefix-графа.
;
; Жоден запис нижче не призначає production-код новій функції.

(sens-prefix-domain-research/1
  (issue 1962)
  (role research-only)
  (production-change none)

  (fixed-premises
    (uttara1
      (0 no)
      (1 yes))
    (racana2
      (00 separator)
      (10 open-parenthesis)
      (01 close-parenthesis)
      (11 dot)))

  ; Повне 3-бітне зерно: () + історичні сім constitutive operations.
  ; Це дослідницька компресія старих padded 8-bit rows 00000000..00000111.
  (bija3
    (000 empty-ground ())
    (001 historical-quote QUOTE)
    (010 historical-atom ATOM)
    (011 historical-eq EQ)
    (100 historical-cons CONS)
    (101 historical-car CAR)
    (110 historical-cdr CDR)
    (111 historical-cond COND))

  (prefix-law-candidate
    (minimum-width 3)
    (parent "remove the final bit")
    (children "append 0 or append 1")
    (semantic-meaning-of-parent-edge unresolved)
    (allowed-interpretations
      derivation
      family
      allocation-ancestry
      structural-composition))

  ; Сильний позитивний witness: CAR/CDR composite selectors.
  ;
  ; Визначення:
  ;   0 => A => CAR
  ;   1 => D => CDR
  ;
  ; Корінь 101 already means CAR, корінь 110 already means CDR.
  ; Кожен доданий bit додає ще один внутрішній selector.
  ;
  ; Тому prefix tree mechanically generates the historical C[AD]+R family.
  (selector-subtree
    (bit 0 A CAR)
    (bit 1 D CDR)

    (width3
      (101 CAR)
      (110 CDR))

    (width4
      (1010 CAAR)
      (1011 CADR)
      (1100 CDAR)
      (1101 CDDR))

    (width5
      (10100 CAAAR)
      (10101 CAADR)
      (10110 CADAR)
      (10111 CADDR)
      (11000 CDAAR)
      (11001 CDADR)
      (11010 CDDAR)
      (11011 CDDDR)))

  (historical-evidence
    (lisp-i
      (source "LISP I Programmer's Manual, MIT, March 1960")
      (fact "five elementary functions/predicates are the basis for composition, conditional expressions and recursion")
      (fact "APPLY is the interpreter synthesis of apply/eval"))
    (lisp-1.5
      (source "LISP 1.5 Programmer's Manual, MIT, 1962")
      (fact "five elementary functions are CAR CDR CONS ATOM EQ")
      (fact "universal evalquote is defined through apply/eval")
      (fact "manual uses composite selectors including CAAR CADR CDAR and CDDR inside evaluator/helper definitions")))

  (strong-observation
    "The selector family is not a hand-authored table: bit extension itself is the composition path.")

  (open-families
    ; Не заповнювати на смак. Для кожного потрібен окремий witness.
    (000 empty-ground)
    (001 quote-family)
    (010 atom-family)
    (011 equality-family)
    (100 construction-family)
    (111 conditional-family))

  (falsification
    (selector-name-collision reject)
    (child-with-wrong-prefix reject)
    (width-with-wrong-selector-cardinality reject)
    (manual-allocation-presented-as-derivation reject)
    (prefix-parent-equals-semantic-parent without-evidence reject))

  (next
    "Порівняти інші 3-bit families з Lisp I / Lisp 1.5 і шукати такі ж природні binary expansions; незручні сімейства не форсувати."))