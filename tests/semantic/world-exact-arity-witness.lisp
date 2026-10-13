; SENS-owned witness for the actual Lisp predicate world?.
; All primitive operators retain exact identities: D3 EQ/QUOTE and D1 bits.
; world? is a local Lisp binding, not an admitted D10 callable identity; do not
; invent a D10 call head merely to force this fixture into the pure .bits reader.
;
; Each form is a self-verdict: EQ compares world?'s actual D1 result to the
; expected D1 bit. The host runner checks only that every form returns D1 YES.

(101 (world? (001 (world () () ()))) 1)
(101 (world? (001 (world))) 0)
(101 (world? (001 (world parent))) 0)
(101 (world? (001 (world parent journal))) 0)
(101 (world? (001 (world parent journal metadata extra))) 0)
(101 (world? (001 (not-world parent journal metadata))) 0)
(101 (world? (001 ())) 0)
