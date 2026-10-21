; #419 — Дослідницький аудит побудови Канону перед версією 1.0.
; Це лише карта доказів, а не визначення семантики мови.
; Класифікація попередня: кожне твердження допускає спростування.

(canon-sculpt-audit
  (schema-version 1)
  (freeze-status pre-1.0-unfrozen)
  (classification-vocabulary
    (ground-value
     syntax-rule-candidate
     irreducible-candidate
     derivable-candidate
     value-domain
     insufficient-evidence))

  (candidate
    (identity CANON_EMPTY_LIST)
    (surface ())
    (category ground-value)
    (observable-laws
      (ground-object)
      (proper-list-terminator)
      (unspecialized-no-answer-where-explicitly-contracted))
    (lower-concepts ())
    (classification ground-value)
    (falsification-question
      "Чи можна замінити кожне чинне використання Канону 0 похідним значенням, не вводячи другої первинної тотожності?"))

  (candidate
    (identity PRIM_QUOTE)
    (category evaluation-control)
    (observable-laws (return-form-without-ordinary-evaluation))
    (classification syntax-rule-candidate)
    (falsification-question
      "Чи можна визначити цитування як звичайну викличну функцію Ліспу, не маючи заздалегідь механізму, який припиняє обчислення аргументу?"))

  (candidate
    (identity PRIM_ATOM)
    (category structural-observation)
    (observable-laws
      ((atom ()) (structural-kind empty-list))
      ((atom pair) (structural-kind pair))
      ((atom non-pair-non-empty) (structural-kind atom)))
    (classification insufficient-evidence)
    (falsification-question
      "Чи можна вивести вид структури без виклику atom, його псевдоніма, позначки представлення зовнішнього виконавця або рівносильного примітивного класифікатора структури?"))

  (candidate
    (identity PRIM_EQ)
    (category identity-observation)
    (observable-laws
      (returns-identity-relation-result-not-generic-truth))
    (classification insufficient-evidence)
    (falsification-question
      "Чи можна вивести відношення тотожності з базовіших понять Ліспу без запозичення рівності вказівників або зовнішнього виконавця та без рекурсивного виклику eq через іншу проєкцію?"))

  (candidate
    (identity PRIM_CONS)
    (category structure-construction)
    (observable-laws (construct-pair))
    (classification irreducible-candidate)
    (falsification-question
      "Чи можна побудувати пару, не маючи вже конструктора пар або потужнішого конструктора складених значень у семантичній основі?"))

  (candidate
    (identity PRIM_CAR)
    (category structure-observation)
    (observable-laws (observe-first-component-of-pair))
    (classification insufficient-evidence)
    (falsification-question
      "Чи можна вивести отримання першої складової пари через cons та базовіші поняття, не додаючи приховано механізму розбирання пари?"))

  (candidate
    (identity PRIM_CDR)
    (category structure-observation)
    (observable-laws (observe-second-component-of-pair))
    (classification insufficient-evidence)
    (falsification-question
      "Чи можна вивести отримання другої складової пари через cons та базовіші поняття, не додаючи приховано механізму розбирання пари?"))

  (candidate
    (identity PRIM_COND)
    (category evaluation-control)
    (observable-laws
      (ordered-clause-selection)
      (evaluate-selected-consequent-only))
    (classification syntax-rule-candidate)
    (falsification-question
      "Чи можна вивести cond макросом із простішої форми керування обчисленням, зберігши спостережуваний порядок обчислення і не проголошуючи приховано простішу форму новим семантичним примітивом?"))

  (audit-law
    (name no-historical-privilege)
    (statement "Назва «примітив» у попередньому контракті — це свідчення для перевірки, а не доказ невивідності."))
  (audit-law
    (name no-host-proof)
    (statement "Реалізація на Rust, позначка часу виконання, тотожність вказівників або обхідний шлях у виконавці самі собою не доводять семантичної невивідності."))
  (audit-law
    (name preserve-before-delete)
    (statement "Жодного кандидата не можна вилучати, доки його спостережувані закони не збережено незалежними свідками, визначеними самим Ліспом, і не доведено їхнє некругове виведення.")))
