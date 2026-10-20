; #432 обмежений пошук структурної основи
; Лише дослідницькі дані. НЕ семантична влада. НЕ доказ глобальної незвідності.
; База: main@23cfdc141ef1e7ab4275d27c536a99d1018f3292
;
; Мета:
;   Сфальсифікувати одну конкретну сім'ю CAR/CDR-редукцій, не чіпаючи Canon/runtime.
;   Цей перший обмежений пошук навмисно використовує лише енергійні операції
;   значень ATOM/EQ/CONS. Керівні форми — окремий наступний експеримент, а не
;   тихе посилення граматики після того, як числа вже спостережено.
;
; Важлива відмінність:
;   механізм пошуку може оглядати згенеровані терми як дослідницькі дані;
;   самі згенеровані кандидати об'єктної мови не можуть містити CAR/CDR,
;   peer-поверхні, round-trip семантичних ID, деструктуризацію пар хоста
;   чи завантаження бекенда.

(canon-sculpt-bounded-search
  (schema-version 2)
  (issue 432)
  (base-main "23cfdc141ef1e7ab4275d27c536a99d1018f3292")
  (role research-only)
  (classification insufficient-evidence)

  (object-language-basis
    (variable x)
    (constants
      () a b c h z
      (structural-kind pair)
      (structural-kind atom)
      (structural-kind empty-list)
      (identity-relation same)
      (identity-relation distinct))
    (constructors atom eq cons)
    (evaluation eager)
    (forbidden
      car cdr
      cond-or-other-selector
      peer-surface-car peer-surface-cdr
      semantic-registry-roundtrip
      host-pair-destructuring
      representation-tag-oracle
      backend-load-as-semantic-primitive))

  (search-method
    (kind extensional-behavior-closure)
    (rounds 2)
    (deduplication "candidate terms with identical observations on all probes collapse to one behavior vector")
    (error-model "eq applied to a pair yields named Type failure; failures propagate through eager arguments")
    (round-0-behaviors 12)
    (round-1-new-behaviors 145)
    (round-1-total-behaviors 157)
    (round-2-new-behaviors 24192)
    (round-2-total-behaviors 24349)
    (round-2-varying-behaviors 6913))

  (car-separation
    (inputs
      ((a . z) (b . z) (c . z)))
    (target-observation (a b c))
    (property "same tail, three distinct heads")
    (result target-not-found-through-round-2)
    (interpretation
      "Within this finite eager ATOM/EQ/CONS grammar/depth, no candidate reproduced CAR on the separating family."))

  (cdr-separation
    (inputs
      ((h . a) (h . b) (h . c)))
    (target-observation (a b c))
    (property "same head, three distinct tails")
    (result target-not-found-through-round-2)
    (interpretation
      "Within this finite eager ATOM/EQ/CONS grammar/depth, no candidate reproduced CDR on the separating family."))

  (why-these-probes-separate
    (car
      "ATOM sees pair/pair/pair; EQ cannot inspect pair interiors; CONS can only wrap values already available. The varying head is therefore the hidden coordinate a candidate would need to recover.")
    (cdr
      "The dual family holds the head fixed and varies only the tail, so the missing observation is the second coordinate."))

  (non-claims
    global-irreducibility-not-proven
    cond-extended-basis-not-yet-searched
    all-possible-lower-bases-not-enumerated
    unbounded-program-space-not-searched
    implementation-mechanism-not-semantic-proof)

  (next-falsification
    (replay "execute this exact eager basis in a verification-only runner and compare the observed closure counts")
    (control-extension "add a precisely specified non-eager selector as a separate experiment; never reuse these counts for the enlarged grammar")
    (candidate-basis-test "if a proposed weaker pair eliminator appears, add it explicitly and rerun rather than silently strengthening the basis")
    (positive-stop "if any candidate reaches the target observation, inspect it for hidden projection/circularity before calling it a derivation")))
