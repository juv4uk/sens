; D6 LET/LET* uk surfaces + D8 ARITHMETIC-SHIFT + COPY-STRUCTURE
; Pure aliases to existing Core4 mechanisms.

; D6:001000 LET / D6:001001 LET*
(0011 нехай let)
(0011 нехай* let*)

; D8:10110101 ARITHMETIC-SHIFT — same as ASH for non-neg k
(0011 арифметично-зсунути арифметичний-зсув)
(0011 arithmetic-shift арифметично-зсунути)

; D8:10101111 COPY-STRUCTURE — for list trees = COPY-LIST
(0011 копіювати-структуру копіювати-список)
(0011 copy-structure копіювати-структуру)
