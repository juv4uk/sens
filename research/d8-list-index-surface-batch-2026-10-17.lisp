; D8 ELT / POSITION / SUBSEQ / NTH-right — pure composition (lib/domains/d8.lisp)
; No new opcodes. Depends on D5 ZEROP, D6 SUB1/ADD1, D3 CAR/CDR/CONS, TAKE/DROP.

; D8:00000101 ELT
(0011 елемент-за-індексом
  (0010 (lst n)
    (110
      ((нуль? n) (100 lst))
      ((0101 lst) (001 ()))
      ((0100 (0101 lst))
       (елемент-за-індексом (011 lst) (зменшити-на-один n))))))
(0011 elt елемент-за-індексом)

; D8:00000110 POSITION
(0011 позиція-з
  (0010 (item lst i)
    (110
      ((0101 lst) (001 ()))
      ((101 item (100 lst)) i)
      ((0100 (0101 lst))
       (позиція-з item (011 lst) (збільшити-на-один i))))))
(0011 позиція-першого-збігу
  (0010 (item lst)
    (позиція-з item lst #d24:000000000000000000000000)))
(0011 position позиція-першого-збігу)

; D8:00100001 SUBSEQ — end exclusive
(0011 підпослідовність
  (0010 (lst start end)
    (взяти (01011 end start) (відкинути start lst))))
(0011 subseq підпослідовність)

; D8:00010001 NTH-right — elt from the right end
(0011 елемент-справа
  (0010 (lst n)
    (елемент-за-індексом
      lst
      (01011 (зменшити-на-один (довжина lst)) n))))
(0011 nth-right елемент-справа)
