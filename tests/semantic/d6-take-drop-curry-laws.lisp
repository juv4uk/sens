; D6:110000 TAKE, D6:110001 DROP — pure lower-domain composition (D3+SUB1+ZEROP/NULL).
; CURRY already on main (batch 5). ADD1 as збільшити-на-один already on main.
; Self-contained TAKE/DROP DEFINEs prove the law in-session; also in
; research/d6-take-drop-curry-batch-2026-10-17.lisp for core4 apply script.
(0011 взяти
  (0010 (n xs)
    (110
      ((нуль? n) (001 ()))
      ((0101 xs) (001 ()))
      ((0100 (0101 xs))
       (111 (100 xs) (взяти (зменшити-на-один n) (011 xs)))))))
(0011 відкинути
  (0010 (n xs)
    (110
      ((нуль? n) xs)
      ((0101 xs) xs)
      ((0100 (0101 xs))
       (відкинути (зменшити-на-один n) (011 xs))))))
(list
  (equal? (взяти #d24:000000000000000000000010
                 (list (quote а) (quote б) (quote в)))
          (list (quote а) (quote б)))
  (equal? (взяти #d24:000000000000000000000000
                 (list (quote а)))
          (quote ()))
  (equal? (відкинути #d24:000000000000000000000001
                     (list (quote а) (quote б) (quote в)))
          (list (quote б) (quote в)))
  (equal? (відкинути #d24:000000000000000000000000
                     (list (quote а)))
          (list (quote а)))
  (equal? ((частково-застосувати cons (quote x)) (quote ()))
          (cons (quote x) (quote ())))
  (equal? (збільшити-на-один #d24:000000000000000000000001)
          #d24:000000000000000000000010))
