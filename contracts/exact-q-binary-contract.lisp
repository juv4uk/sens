; #1826 — допуск точних раціональних чисел ℚ до предикатів порівняння.
;
; Перевірка точності відповідає на одне питання: чи може числовий
; предикат повернути точну відповідь мови без наближення?
; Якщо операцію допущено, результат — однобітна відповідь СЕНС:
;   0 = НІ
;   1 = ТАК
;
; Біт предиката не є числом. Раціональні 0/1 і 1/1 залишаються числами,
; їх не можна підміняти тотожністю предиката.
; За межами допущеного домену ℚ має виникнути іменована помилка
; домену чи типу. Структурне () не є третьою відповіддю предиката.

(exact-q-predicate-contract/2
  ((domain-owner . exact-q-comparison-predicate)
   (admissibility . all-required-values-exact-rational)
   (result-form . predicate-one-bit)
   (yes . one)
   (no . zero)
   (outside-domain . named-domain-error)
   (approximation-policy . forbidden)
   (number-as-predicate-result . forbidden)
   (generic-truth-coercion . forbidden)
   (host-bool-authority . forbidden))

  ((identity . 00011010)
   (relation . strictly-increasing)
   (operand-domain . exact-rational-sequence))

  ((identity . 00011011)
   (relation . strictly-decreasing)
   (operand-domain . exact-rational-sequence))

  ((identity . 00011100)
   (relation . numeric-equality)
   (operand-domain . exact-rational-sequence))

  ((identity . 00011101)
   (relation . nondecreasing)
   (operand-domain . exact-rational-sequence))

  ((identity . 00011110)
   (relation . nonincreasing)
   (operand-domain . exact-rational-sequence)))