; Core1 SID -> historical Lisp mechanism comparison.
;
; Semantic direction is one-way:
;   my-lisp SID identity + Core1 profile law -> admitted historical mechanism
; Never:
;   historical name / implementation -> new my-lisp semantic identity
;
; SID identifies the operation. The selected Core profile owns the law/result
; domain. Core1 uses the historical T/NIL-oriented law where applicable.
; Core4-only result records such as identity-relation/structural-kind are
; outside this file's profile and are not projected here.
;
; A row is:
;   (row SID my-lisp-name historical-name source fit core1-status)
;
; fit:
;   direct                 historical mechanism is native to the Core1 profile
;   value-adapter          representation/surface adaptation only; Core1 law is unchanged
;   closure-adapter        historical FUNCTION/FUNARG supplies the Core1 closure mechanism
;   surface-adapter        historical surface/calling convention differs
;   profile-support        historical evaluator helper supports Core1 but is not a public identity
;
; core1-status:
;   admitted               used by the current Core1 bootstrap
;   support                internal mechanism used behind admitted Core1 behavior
;   available-not-admitted historically present, but not required by the current bootstrap
;
; This file compares identities/mechanisms. It does NOT declare semantic equivalence
; merely because two names look alike.

(core1-historical-sid-map/1
  (authority
    (semantic-owner . my-lisp)
    (historical-mechanism-repository . juv4uk/mccarthy-eval)
    (historical-mechanism-pin . "1ae9745b66a1439c1929b0d9038c680567118a58")
    (reverse-authority . forbidden)
    (historical-name-may-mint-sid . no))

  (rows
    (row 00000000 empty-list NIL mccarthy-1960 direct admitted)
    (row 00000001 quote QUOTE mccarthy-1960 direct admitted)
    (row 00000010 atom ATOM mccarthy-1960 direct admitted)
    (row 00000011 eq EQ mccarthy-1960 direct admitted)
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

    (row 00001100 + PLUS lisp15-1962 direct available-not-admitted)
    (row 00001101 - DIFFERENCE lisp15-1962 surface-adapter available-not-admitted)
    (row 00001110 * TIMES lisp15-1962 direct available-not-admitted)
    (row 00010001 min MIN lisp15-1962 direct available-not-admitted)
    (row 00010010 max MAX lisp15-1962 direct available-not-admitted)
    (row 00010011 mod REMAINDER lisp15-1962 surface-adapter available-not-admitted)
    (row 00010100 quotient QUOTIENT lisp15-1962 direct available-not-admitted)
    (row 00011010 < LESSP lisp15-1962 direct available-not-admitted)
    (row 00011011 > GREATERP lisp15-1962 direct available-not-admitted)

    (row 00100001 not NOT lisp15-1962 direct admitted)
    (row 00100010 equal? EQUAL lisp15-1962 direct available-not-admitted)
    (row 00100111 list LIST lisp15-1962 direct admitted)
    (row 00101000 length LENGTH lisp15-1962 direct available-not-admitted)
    (row 00101001 append APPEND mccarthy-1960 direct support)
    (row 00101010 reverse REVERSE lisp15-1962 direct available-not-admitted)
    (row 00101100 member? MEMBER lisp15-1962 direct available-not-admitted)
    (row 00101101 assoc assoc mccarthy-1960 profile-support support)
    (row 00101110 pair PAIR mccarthy-1960 profile-support support)

    (row 01001101 eval eval mccarthy-1960 profile-support support)

    (row 10011010 and AND lisp15-1962 direct available-not-admitted)
    (row 10011011 or OR lisp15-1962 direct available-not-admitted))

  (historical-support-without-my-lisp-sid
    (mechanism apply mccarthy-1960 evaluator-support)
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
