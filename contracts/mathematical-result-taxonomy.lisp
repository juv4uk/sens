; Класифікація математичних результатів: закони належать самій мові СЕНС.
;
; Завдання #225 не створює іншої математики. Воно зберігає загальноприйняті
; математичні класифікації та відокремлює їх від ролі й подання результату.
;
; Не можна змішувати два незалежні запитання:
;
;   1. Яким математичним об'єктом є дане значення?
;      Приклад: число π є дійсним, ірраціональним і трансцендентним.
;
;   2. Як результат представляє математичний об'єкт або співвідноситься з ним?
;      Приклад: 314159/100000 саме є точним раціональним числом, але також
;      може слугувати раціональним наближенням до числа π.
;
; Основний закон: математичний об'єкт не тотожний своєму наближенню.
;
; Недвійкова математика залишається математикою. Жоден запис цього
; контракту не встановлює багатозначного логічного стану й не дозволяє
; загального перетворення довільного значення на логічний тип.

(mathematical-result-taxonomy/1
  ((identity . laws)
   (domain-owner . mathematical-result)
   (classification-source . standard-mathematics)
   (object-approximation-identity . distinct)
   (generic-truth-coercion . forbidden)
   (many-valued-collapse . forbidden)
   (lower-logic-redefinition . forbidden))

  ; Раціональний результат уже є точним математичним об'єктом.
  ; Можливість наближати цим числом інший об'єкт означає окремий
  ; зв'язок ролі результату, а не зміну його тотожності.
  ((identity . rational-example)
   (value . 1/2)
   (number-system . rational)
   (subset-of . real)
   (result-role . exact-object))

  ; Число π не є наближенням: це точна математична стала.
  ; Виконавець може обрати символічне, точне дійсне або інше
  ; подання, не змінюючи математичної тотожності.
  ((identity . pi-example)
   (object . pi)
   (number-system . real)
   (rationality . irrational)
   (algebraic-status . transcendental)
   (result-role . exact-object)
   (representation-policy . representation-may-vary-without-changing-object))

  ; Квадратний корінь із двох є точним алгебраїчним ірраціональним
  ; числом, навіть коли виконавець представляє його символічно,
  ; а не скінченним числовим записом.
  ((identity . sqrt2-example)
   (object . (sqrt 2))
   (number-system . real)
   (rationality . irrational)
   (algebraic-status . algebraic)
   (result-role . exact-object)
   (representation-policy . representation-may-vary-without-changing-object))

  ; Наближення пов'язує два математичні об'єкти: точне число-наближення
  ; та його ціль. Слід явно зазначити ступінь обґрунтованості наближення.
  ((identity . approximation-role)
   (result-role . approximation)
   (required-metadata . (target approximant precision-or-error-guarantee))
   (approximant-remains-own-mathematical-object . t)
   (truth-status . not-applicable))

  ; Інтервал, що охоплює результат, є математичними даними.
  ; Його гарантія свідчить лише про належність цілі до вказаних меж,
  ; а не про нечіткий ступінь істинності.
  ((identity . interval-enclosure-role)
   (result-role . interval-enclosure)
   (required-metadata . (target lower-bound upper-bound enclosure-guarantee))
   (truth-status . not-applicable))

  ; Символічна форма — спосіб подання. Символічний вираз може позначати
  ; точний математичний об'єкт (π, корінь із двох, необчислений
  ; алгебраїчний вираз), не стаючи епістемічним чи багатозначним станом.
  ((identity . symbolic-expression-role)
   (result-role . symbolic-expression)
   (may-denote-exact-mathematical-object . t)
   (many-valued-status . forbidden)))
