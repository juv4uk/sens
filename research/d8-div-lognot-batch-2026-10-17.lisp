; D8 DIV + LOGNOT — pure non-neg D24+
; Residency lib/domains/d8.lisp. LOGNOT inverts significant bits only (no fixed width).

; D8:11001100 DIV — pair (quotient . remainder)
(0011 частка+остача
  (0010 (a b)
    (сполучити (quotient a b)
               (сполучити (mod a b) (як-є ())))))
(0011 div частка+остача)

; D8:10110010 LOGNOT — invert bits of the used magnitude (finite support)
(0011 побітове-не
  (0010 (n)
    (110
      ((нуль? n) #d24:000000000000000000000000)
      ((0100 (нуль? n))
       (додати
         (110
           ((equal? (mod n #d24:000000000000000000000010)
                    #d24:000000000000000000000000)
            #d24:000000000000000000000001)
           ((0100
              (equal? (mod n #d24:000000000000000000000010)
                      #d24:000000000000000000000000))
            #d24:000000000000000000000000))
         (помножити
           #d24:000000000000000000000010
           (побітове-не
             (quotient n #d24:000000000000000000000010))))))))
(0011 lognot побітове-не)
