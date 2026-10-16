; D9:011000000..011000111 — 8 ратифікованих селекторів, 16 позитивів і 16 однобітних мутантів.
; Листки повного 7-рівневого SENS cons-дерева попарно різні, для fail-closed.
((lambda (дерево)
  (list
    ; D9:011000000 CDAAAAAAR — одна позитивна та одна негативна орієнтація.
    (eq? (р-п-п-п-п-п-п дерево) (quote лист-0000001))
    (not? (eq? (car (car (car (car (car (car (car дерево))))))) (quote лист-0000001)))
    ; D9:011000001 CDAAAAADR — одна позитивна та одна негативна орієнтація.
    (eq? (р-п-п-п-п-п-р дерево) (quote лист-1000001))
    (not? (eq? (car (car (car (car (car (car (cdr дерево))))))) (quote лист-1000001)))
    ; D9:011000010 CDAAAADAR — одна позитивна та одна негативна орієнтація.
    (eq? (р-п-п-п-п-р-п дерево) (quote лист-0100001))
    (not? (eq? (car (car (car (car (car (cdr (car дерево))))))) (quote лист-0100001)))
    ; D9:011000011 CDAAAADDR — одна позитивна та одна негативна орієнтація.
    (eq? (р-п-п-п-п-р-р дерево) (quote лист-1100001))
    (not? (eq? (car (car (car (car (car (cdr (cdr дерево))))))) (quote лист-1100001)))
    ; D9:011000100 CDAAADAAR — одна позитивна та одна негативна орієнтація.
    (eq? (р-п-п-п-р-п-п дерево) (quote лист-0010001))
    (not? (eq? (car (car (car (car (cdr (car (car дерево))))))) (quote лист-0010001)))
    ; D9:011000101 CDAAADADR — одна позитивна та одна негативна орієнтація.
    (eq? (р-п-п-п-р-п-р дерево) (quote лист-1010001))
    (not? (eq? (car (car (car (car (cdr (car (cdr дерево))))))) (quote лист-1010001)))
    ; D9:011000110 CDAAADDAR — одна позитивна та одна негативна орієнтація.
    (eq? (р-п-п-п-р-р-п дерево) (quote лист-0110001))
    (not? (eq? (car (car (car (car (cdr (cdr (car дерево))))))) (quote лист-0110001)))
    ; D9:011000111 CDAAADDDR — одна позитивна та одна негативна орієнтація.
    (eq? (р-п-п-п-р-р-р дерево) (quote лист-1110001))
    (not? (eq? (car (car (car (car (cdr (cdr (cdr дерево))))))) (quote лист-1110001)))

    ; D9:011001000 CDAADAAAR: позитив та однобітний негатив.
    (eq? (р-п-п-р-п-п-п дерево) (quote лист-0001001))
    (not? (eq? (car (car (car (cdr (car (car (car дерево))))))) (quote лист-0001001)))
    ; D9:011001001 CDAADAADR: позитив та однобітний негатив.
    (eq? (р-п-п-р-п-п-р дерево) (quote лист-1001001))
    (not? (eq? (car (car (car (cdr (car (car (cdr дерево))))))) (quote лист-1001001)))
    ; D9:011001010 CDAADADAR: позитив та однобітний негатив.
    (eq? (р-п-п-р-п-р-п дерево) (quote лист-0101001))
    (not? (eq? (car (car (car (cdr (car (cdr (car дерево))))))) (quote лист-0101001)))
    ; D9:011001011 CDAADADDR: позитив та однобітний негатив.
    (eq? (р-п-п-р-п-р-р дерево) (quote лист-1101001))
    (not? (eq? (car (car (car (cdr (car (cdr (cdr дерево))))))) (quote лист-1101001)))
    ; D9:011001100 CDAADDAAR: позитив та однобітний негатив.
    (eq? (р-п-п-р-р-п-п дерево) (quote лист-0011001))
    (not? (eq? (car (car (car (cdr (cdr (car (car дерево))))))) (quote лист-0011001)))
    ; D9:011001101 CDAADDADR: позитив та однобітний негатив.
    (eq? (р-п-п-р-р-п-р дерево) (quote лист-1011001))
    (not? (eq? (car (car (car (cdr (cdr (car (cdr дерево))))))) (quote лист-1011001)))
    ; D9:011001110 CDAADDDAR: позитив та однобітний негатив.
    (eq? (р-п-п-р-р-р-п дерево) (quote лист-0111001))
    (not? (eq? (car (car (car (cdr (cdr (cdr (car дерево))))))) (quote лист-0111001)))
    ; D9:011001111 CDAADDDDR: позитив та однобітний негатив.
    (eq? (р-п-п-р-р-р-р дерево) (quote лист-1111001))
    (not? (eq? (car (car (car (cdr (cdr (cdr (cdr дерево))))))) (quote лист-1111001)))

  ))
  (cons (cons (cons (cons (cons (cons (cons (quote лист-0000000) (quote лист-0000001)) (cons (quote лист-0000010) (quote лист-0000011))) (cons (cons (quote лист-0000100) (quote лист-0000101)) (cons (quote лист-0000110) (quote лист-0000111)))) (cons (cons (cons (quote лист-0001000) (quote лист-0001001)) (cons (quote лист-0001010) (quote лист-0001011))) (cons (cons (quote лист-0001100) (quote лист-0001101)) (cons (quote лист-0001110) (quote лист-0001111))))) (cons (cons (cons (cons (quote лист-0010000) (quote лист-0010001)) (cons (quote лист-0010010) (quote лист-0010011))) (cons (cons (quote лист-0010100) (quote лист-0010101)) (cons (quote лист-0010110) (quote лист-0010111)))) (cons (cons (cons (quote лист-0011000) (quote лист-0011001)) (cons (quote лист-0011010) (quote лист-0011011))) (cons (cons (quote лист-0011100) (quote лист-0011101)) (cons (quote лист-0011110) (quote лист-0011111)))))) (cons (cons (cons (cons (cons (quote лист-0100000) (quote лист-0100001)) (cons (quote лист-0100010) (quote лист-0100011))) (cons (cons (quote лист-0100100) (quote лист-0100101)) (cons (quote лист-0100110) (quote лист-0100111)))) (cons (cons (cons (quote лист-0101000) (quote лист-0101001)) (cons (quote лист-0101010) (quote лист-0101011))) (cons (cons (quote лист-0101100) (quote лист-0101101)) (cons (quote лист-0101110) (quote лист-0101111))))) (cons (cons (cons (cons (quote лист-0110000) (quote лист-0110001)) (cons (quote лист-0110010) (quote лист-0110011))) (cons (cons (quote лист-0110100) (quote лист-0110101)) (cons (quote лист-0110110) (quote лист-0110111)))) (cons (cons (cons (quote лист-0111000) (quote лист-0111001)) (cons (quote лист-0111010) (quote лист-0111011))) (cons (cons (quote лист-0111100) (quote лист-0111101)) (cons (quote лист-0111110) (quote лист-0111111))))))) (cons (cons (cons (cons (cons (cons (quote лист-1000000) (quote лист-1000001)) (cons (quote лист-1000010) (quote лист-1000011))) (cons (cons (quote лист-1000100) (quote лист-1000101)) (cons (quote лист-1000110) (quote лист-1000111)))) (cons (cons (cons (quote лист-1001000) (quote лист-1001001)) (cons (quote лист-1001010) (quote лист-1001011))) (cons (cons (quote лист-1001100) (quote лист-1001101)) (cons (quote лист-1001110) (quote лист-1001111))))) (cons (cons (cons (cons (quote лист-1010000) (quote лист-1010001)) (cons (quote лист-1010010) (quote лист-1010011))) (cons (cons (quote лист-1010100) (quote лист-1010101)) (cons (quote лист-1010110) (quote лист-1010111)))) (cons (cons (cons (quote лист-1011000) (quote лист-1011001)) (cons (quote лист-1011010) (quote лист-1011011))) (cons (cons (quote лист-1011100) (quote лист-1011101)) (cons (quote лист-1011110) (quote лист-1011111)))))) (cons (cons (cons (cons (cons (quote лист-1100000) (quote лист-1100001)) (cons (quote лист-1100010) (quote лист-1100011))) (cons (cons (quote лист-1100100) (quote лист-1100101)) (cons (quote лист-1100110) (quote лист-1100111)))) (cons (cons (cons (quote лист-1101000) (quote лист-1101001)) (cons (quote лист-1101010) (quote лист-1101011))) (cons (cons (quote лист-1101100) (quote лист-1101101)) (cons (quote лист-1101110) (quote лист-1101111))))) (cons (cons (cons (cons (quote лист-1110000) (quote лист-1110001)) (cons (quote лист-1110010) (quote лист-1110011))) (cons (cons (quote лист-1110100) (quote лист-1110101)) (cons (quote лист-1110110) (quote лист-1110111)))) (cons (cons (cons (quote лист-1111000) (quote лист-1111001)) (cons (quote лист-1111010) (quote лист-1111011))) (cons (cons (quote лист-1111100) (quote лист-1111101)) (cons (quote лист-1111110) (quote лист-1111111)))))))))
