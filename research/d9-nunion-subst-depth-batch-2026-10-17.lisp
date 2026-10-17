; D9 NUNION / APPLY-SUBST / WORLD-DEPTH — pure composition
; Residency lib/domains/d9.lisp. No bare numeric call-heads.

; D9:110001100 NUNION — non-destructive = UNION
(0011 nunion об'єднання)

; D9:101101001 APPLY-SUBST — alias to SUBST/замінити
(0011 застосувати-підстановка замінити)
(0011 apply-subst застосувати-підстановка)

; D9:111001011 WORLD-DEPTH — 1 + max(depth car, depth cdr); atom/null = 0
(0011 світ-глибина
  (0010 (т)
    (110
      ((or (0101 т) (атом? т)) #d24:000000000000000000000000)
      ((0100 (or (0101 т) (атом? т)))
       (додати-1
         (110
           ((менше?
              (світ-глибина (100 т))
              (світ-глибина (011 т)))
            (світ-глибина (011 т)))
           ((0100
              (менше?
                (світ-глибина (100 т))
                (світ-глибина (011 т))))
            (світ-глибина (100 т)))))))))
(0011 world-depth світ-глибина)
