; Межа повноважень між семантикою СЕНС та машинним виконанням.
; Машинне представлення походить від мовного значення, а не навпаки.
; Відомості про процесор, набори інструкцій, регістри, кодування
; та двійковий інтерфейс виклику описують лише способи виконання.
; Вони не можуть призначати назви, координати чи закони функцій.
;
; Це декларативна політика, якою володіє мовний рівень СЕНС.
; Зовнішні засоби можуть передавати та перевіряти її виконання,
; але не мають права змінювати напрям семантичної влади.

(machine-authority-boundary-1
  (semantic-authority language-contract.lisp+ratified-domain-laws)
  (machine-root lib/machine)
  (public-api-excluded-root lib/machine)
  (machine-public-api-admission explicit-ratification-only)

  (lowering-direction semantic-to-machine)
  (reverse-authority machine-to-semantic forbidden)

  (semantic-id-from-isa forbidden)
  (semantic-id-from-cpu-profile forbidden)
  (peer-surface-from-machine forbidden)

  ; Машинне спостереження підтверджує реалізацію, але не встановлює
  ; очікуваного мовного результату для власного порівняння.
  (machine-semantic-answer-key forbidden)
  (native-only-semantic-witness forbidden)
  (independent-semantic-witness required)
  (representation-specific-meaning forbidden)
  (machine-layer-replaceable required)
  (capability-provenance lib/machine/capability-provenance.lisp)

  (diagnostic machine-authority-boundary-violation)
  (diagnostic machine-semantic-hybrid-violation))
