; Пакет знань СЕНС 0.1 — лише дані; читати через `read`, не виконувати через `load`.
; SENS-Wissenspaket 0.1 — nur Daten; mit `read` lesen, nicht mit `load` ausführen.
; SENS knowledge package 0.1 — data only; read with `read`, never `load`.
((format . my-lisp-knowledge)
 (version 0 1)
 (module . astronomy-exchange)
 (clauses . (((planet earth))
             ((has-mass (var x)) (planet (var x))))))
