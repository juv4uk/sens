; #996 — машинно-читана політика передачі повноважень.
;
; Цей контракт не дублює семантичних рядків. Він зазначає, як нижчі
; споживачі (як-от cml і wsm-my-lisp) мусять закріпити й перевірити канонічний
; реєстр, що належить Lisp, перш ніж понижувати чи спостерігати його.

(semantic-registry-handoff-contract/1
  (authority "lib/surface/semantic-registry.lisp")
  (authority-owner sens)
  (identity-domain bare-sid-8)
  (revision-pin git-commit-containing-authority)
  (content-digest sha256-utf8-source)
  (witness semantic-registry-handoff-witness)
  (consumers
    (cml lower-or-observe-only)
    (wsm-my-lisp lower-or-observe-only))
  (forbidden
    decimal-sid-shadow-table
    string-sid-shadow-table
    downstream-semantic-reinterpretation))
