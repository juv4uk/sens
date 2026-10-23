; #996 — передавання семантичної тотожності з ратифікованої драбини SENS.
; Джерело влади — лише доменні таблиці D1–D10, не плоский SID8.
; Українська проєкція «укр» відповідає парі (домен, точне бітове слово).
; Цей контракт не дублює жодного семантичного рядка.
; Історичний lib/surface/semantic-registry.lisp не є джерелом тотожності.
; Виконуваний читач поточних таблиць: lib/surface/semantic-registry-api.lisp.
; D7 є текстом; присутність у таблиці не надає права виклику.

(semantic-registry-handoff-contract-1
  (authority-owner sens)
  (authority-kind ratified-domain-ladder)
  (authority
    "lib/domains/d1.lisp"
    "lib/domains/d2.lisp"
    "lib/domains/d3.lisp"
    "lib/domains/d4.lisp"
    "lib/domains/d5.lisp"
    "lib/domains/d6.lisp"
    "lib/domains/d7.lisp"
    "lib/domains/d8.lisp"
    "lib/domains/d9.lisp"
    "lib/domains/d10.lisp")
  (reader "lib/surface/semantic-registry-api.lisp")
  (identity-domain (domain exact-bit-word))
  (human-projection укр)
  (revision-pin git-commit-containing-authority)
  (content-digest sha256-utf8-source)
  (witness semantic-registry-handoff-witness)
  (consumers
    (cml lower-or-observe-only)
    (wsm-my-lisp lower-or-observe-only))
  (forbidden
    historical-sid8-as-domain-code
    flat-byte-identity
    width-padding-or-truncation
    decimal-sid-shadow-table
    string-sid-shadow-table
    downstream-semantic-reinterpretation))
