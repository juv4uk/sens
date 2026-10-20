; Порівняння історичних кодів SID першого ядра з механізмами Ліспу.
;
; Семантичні першоджерела: ранній Лісп Маккарті (1960) та Lisp 1.5 (1962).
; Відмінність написання: англійські назви предикатів завершуються знаком `?`
; за рішенням власника (#1443).
; Історично тотожність визначав код SENS (Sens8), а не назва.
; Нові коди для історичних функцій вимагають рішення власника.
; Цей контракт фіксує історичне походження, а не чинну драбину Д1–Д10.
;
; SID визначав операцію. Обраний профіль ядра встановлював закон
; і домен результату. Перше ядро за потреби застосовує історичні T/NIL.
; Записи результатів четвертого ядра, зокрема identity-relation і
; structural-kind, тут не припускаються і не проєктуються.
;
; Формат рядка:
;   (row SID my-lisp-name historical-name source fit core1-status)
;
; Значення поля fit:
;   direct                 механізм безпосередньо належить першому ядру
;   value-adapter          змінюється лише подання; закон не змінюється
;   closure-adapter        замикання першого ядра надають FUNCTION/FUNARG
;   surface-adapter        відрізняється написання або спосіб виклику
;   profile-support        внутрішній допоміжний механізм, не публічна тотожність
;
; Значення поля core1-status:
;   admitted               застосовується під час чинного початкового завантаження
;   support                внутрішній механізм для допущеної поведінки
;   available-not-admitted наявний історично, але нині не потрібний
;
; Таблиця лише зіставляє тотожності та механізми. Подібність написань
; НЕ встановлює семантичної рівносильності.

(core1-historical-sid-map/1
  (authority
    (semantic-owner . sens)
    (historical-mechanism-repository . juv4uk/mccarthy-eval)
    (historical-mechanism-pin . "1ae9745b66a1439c1929b0d9038c680567118a58")
    (reverse-authority . forbidden)
    (semantic-inspiration . mccarthy-1960)
    (historical-name-may-mint-sid . owner-decision))

  (rows
    (row 00000000 empty-list NIL mccarthy-1960 direct admitted)
    (row 00000001 quote QUOTE mccarthy-1960 direct admitted)
    (row 00000010 atom? ATOM mccarthy-1960 direct admitted)
    (row 00000011 eq? EQ mccarthy-1960 direct admitted)
    (row 00000100 cons CONS mccarthy-1960 direct admitted)
    (row 00000101 car CAR mccarthy-1960 direct admitted)
    (row 00000110 cdr CDR mccarthy-1960 direct admitted)
    (row 00000111 cond COND mccarthy-1960 direct admitted)
    (row 00001000 lambda LAMBDA mccarthy-1960 closure-adapter admitted)
    (row 00001001 define DEFINE lisp-i-1960 surface-adapter admitted)
    (row 00001011 def DEFINE lisp-i-1960 surface-adapter admitted)
    ; 10101010 label: рішення власника 2026-09-26 — LABEL отримав SID
    ; (раніше — механізм без SID). Ядро mccarthy-eval 6031f926 диспетчеризує
    ; LABEL за кодом 10101010; Core1 (lib/core1.lisp) записаний цим кодом.
    (row 10101010 label LABEL mccarthy-1960 direct admitted)
    ; #1443: функції з праці Маккарті (1960, §3d), визначені в lib/core.lisp.
    (row 10101011 null? NULL mccarthy-1960 direct available-not-admitted)
    (row 10101100 subst SUBST mccarthy-1960 direct available-not-admitted)
    (row 10101101 sublis SUBLIS mccarthy-1960 direct available-not-admitted)
    (row 10101110 maplist MAPLIST mccarthy-1960 direct available-not-admitted)
    (row 10101111 apply apply mccarthy-1960 direct available-not-admitted)

    (row 00001100 + PLUS lisp15-1962 direct available-not-admitted)
    (row 00001101 - DIFFERENCE lisp15-1962 surface-adapter available-not-admitted)
    (row 00001110 * TIMES lisp15-1962 direct available-not-admitted)
    (row 00010001 min MIN lisp15-1962 direct available-not-admitted)
    (row 00010010 max MAX lisp15-1962 direct available-not-admitted)
    (row 00010011 mod REMAINDER lisp15-1962 surface-adapter available-not-admitted)
    (row 00010100 quotient QUOTIENT lisp15-1962 direct available-not-admitted)
    (row 00011010 < LESSP lisp15-1962 direct available-not-admitted)
    (row 00011011 > GREATERP lisp15-1962 direct available-not-admitted)

    (row 00100001 not? NOT lisp15-1962 direct admitted)
    (row 00100010 equal? EQUAL lisp15-1962 direct available-not-admitted)
    (row 00100111 list LIST lisp15-1962 direct admitted)
    (row 00101000 length LENGTH lisp15-1962 direct available-not-admitted)
    (row 00101001 append APPEND mccarthy-1960 direct support)
    (row 00101010 reverse REVERSE lisp15-1962 direct available-not-admitted)
    ; member? відповідає також назві `among` у Маккарті (1960), але такої назви немає в закріпленому доказі.
    (row 00101100 member? MEMBER lisp15-1962 direct available-not-admitted)
    (row 00101101 assoc assoc mccarthy-1960 profile-support support)
    (row 00101110 pair PAIR mccarthy-1960 profile-support support)

    (row 01001101 eval eval mccarthy-1960 profile-support support)

    (row 10011010 and AND lisp15-1962 direct available-not-admitted)
    (row 10011011 or OR lisp15-1962 direct available-not-admitted)
    (row 11101101 string->symbol PACK lisp15-1962 direct admitted)
    (row 11110100 write-to-string PRIN1 lisp15-1962 direct admitted)
    (row 11100000 char-code CHAR-CODE lisp15-1962 direct admitted)
    (row 11110110 divide DIVIDE lisp15-1962 direct admitted)

  (historical-support-without-my-lisp-sid
    (mechanism appq mccarthy-1960 evaluator-support)
    (mechanism evcon mccarthy-1960 evaluator-support)
    (mechanism evlis mccarthy-1960 evaluator-support)
    (mechanism FUNCTION lisp15-1962 closure-constructor)
    (mechanism FUNARG lisp15-1962 captured-environment-application)
    (value T mccarthy-1960 historical-control-value))

  (rules
    (sid-selects-identity . yes)
    (profile-selects-law . core1)
    (core1-result-domain . historical-t-nil)
    (core4-result-records-in-core1 . forbidden)
    (historical-name-selects-meaning . no)
    (mechanism-may-be-replaced . yes)
    (cross-profile-projection-must-be-explicit . yes)
    (unmapped-historical-function-becomes-language-feature . no)
    (unmapped-my-lisp-sid-falls-back-to-historical-name . no)))
