; D9 W9 ratified text functions: UTF-8 characters are scalar data, not D7 digits.
; Exact D1 vector (1 0 1 0 1 0 1 0): independent positive/wrong-answer laws.
; Only SENS executes the semantics; shell CI transports this source as input.
(список
  (рядок-порожній? "")
  (рядок-порожній? "ї")
  (equal? (рядок-перший "кіт") "к")
  (equal? (рядок-перший "кіт") "і")
  (equal? (рядок-решта "кіт") "іт")
  (equal? (рядок-решта "кіт") "кі")
  (рядок-префікс? "лі" "ліс")
  (рядок-префікс? "слі" "ліс"))

; opt-in повна укр-поверхня: exact identity = lib/domains/d*.lisp; DEFINE-аліас, без нової диспетчеризації.
(визначити список list)
