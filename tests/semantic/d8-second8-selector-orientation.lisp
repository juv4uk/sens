; D8 наступна вісімка 01101000..01101111. 16 positive + 16 one-bit negative.
; Повне асиметричне дерево: кожний CAR/CDR шлях відрізняється точною ціллю.
((lambda (дерево)
  (list
    ; D8:01101000 CDADAAAR: exact, потім однобітний мутант.
    (eq? (р-п-р-п-п-п дерево) (quote лист-000101))
    (not? (eq? (car (car (cdr (car (car (car дерево)))))) (quote лист-000101)))
    ; D8:01101001 CDADAADR: exact, потім однобітний мутант.
    (eq? (р-п-р-п-п-р дерево) (quote лист-100101))
    (not? (eq? (car (car (cdr (car (car (cdr дерево)))))) (quote лист-100101)))
    ; D8:01101010 CDADADAR: exact, потім однобітний мутант.
    (eq? (р-п-р-п-р-п дерево) (quote лист-010101))
    (not? (eq? (car (car (cdr (car (cdr (car дерево)))))) (quote лист-010101)))
    ; D8:01101011 CDADADDR: exact, потім однобітний мутант.
    (eq? (р-п-р-п-р-р дерево) (quote лист-110101))
    (not? (eq? (car (car (cdr (car (cdr (cdr дерево)))))) (quote лист-110101)))
    ; D8:01101100 CDADDAAR: exact, потім однобітний мутант.
    (eq? (р-п-р-р-п-п дерево) (quote лист-001101))
    (not? (eq? (car (car (cdr (cdr (car (car дерево)))))) (quote лист-001101)))
    ; D8:01101101 CDADDADR: exact, потім однобітний мутант.
    (eq? (р-п-р-р-п-р дерево) (quote лист-101101))
    (not? (eq? (car (car (cdr (cdr (car (cdr дерево)))))) (quote лист-101101)))
    ; D8:01101110 CDADDDAR: exact, потім однобітний мутант.
    (eq? (р-п-р-р-р-п дерево) (quote лист-011101))
    (not? (eq? (car (car (cdr (cdr (cdr (car дерево)))))) (quote лист-011101)))
    ; D8:01101111 CDADDDDR: exact, потім однобітний мутант.
    (eq? (р-п-р-р-р-р дерево) (quote лист-111101))
    (not? (eq? (car (car (cdr (cdr (cdr (cdr дерево)))))) (quote лист-111101)))    ; D8:01110000 CDDAAAAR
    (eq? (р-р-п-п-п-п дерево) (quote лист-000011))
    (not? (eq? (car (cdr (car (car (car (car дерево)))))) (quote лист-000011)))
    ; D8:01110001 CDDAAADR
    (eq? (р-р-п-п-п-р дерево) (quote лист-100011))
    (not? (eq? (car (cdr (car (car (car (cdr дерево)))))) (quote лист-100011)))
    ; D8:01110010 CDDAADAR
    (eq? (р-р-п-п-р-п дерево) (quote лист-010011))
    (not? (eq? (car (cdr (car (car (cdr (car дерево)))))) (quote лист-010011)))
    ; D8:01110011 CDDAADDR
    (eq? (р-р-п-п-р-р дерево) (quote лист-110011))
    (not? (eq? (car (cdr (car (car (cdr (cdr дерево)))))) (quote лист-110011)))
    ; D8:01110100 CDDADAAR
    (eq? (р-р-п-р-п-п дерево) (quote лист-001011))
    (not? (eq? (car (cdr (car (cdr (car (car дерево)))))) (quote лист-001011)))
    ; D8:01110101 CDDADADR
    (eq? (р-р-п-р-п-р дерево) (quote лист-101011))
    (not? (eq? (car (cdr (car (cdr (car (cdr дерево)))))) (quote лист-101011)))
    ; D8:01110110 CDDADDAR
    (eq? (р-р-п-р-р-п дерево) (quote лист-011011))
    (not? (eq? (car (cdr (car (cdr (cdr (car дерево)))))) (quote лист-011011)))
    ; D8:01110111 CDDADDDR
    (eq? (р-р-п-р-р-р дерево) (quote лист-111011))
    (not? (eq? (car (cdr (car (cdr (cdr (cdr дерево)))))) (quote лист-111011)))


  ))
  (cons (cons (cons (cons (cons (cons (quote лист-000000) (quote лист-000001)) (cons (quote лист-000010) (quote лист-000011))) (cons (cons (quote лист-000100) (quote лист-000101)) (cons (quote лист-000110) (quote лист-000111)))) (cons (cons (cons (quote лист-001000) (quote лист-001001)) (cons (quote лист-001010) (quote лист-001011))) (cons (cons (quote лист-001100) (quote лист-001101)) (cons (quote лист-001110) (quote лист-001111))))) (cons (cons (cons (cons (quote лист-010000) (quote лист-010001)) (cons (quote лист-010010) (quote лист-010011))) (cons (cons (quote лист-010100) (quote лист-010101)) (cons (quote лист-010110) (quote лист-010111)))) (cons (cons (cons (quote лист-011000) (quote лист-011001)) (cons (quote лист-011010) (quote лист-011011))) (cons (cons (quote лист-011100) (quote лист-011101)) (cons (quote лист-011110) (quote лист-011111)))))) (cons (cons (cons (cons (cons (quote лист-100000) (quote лист-100001)) (cons (quote лист-100010) (quote лист-100011))) (cons (cons (quote лист-100100) (quote лист-100101)) (cons (quote лист-100110) (quote лист-100111)))) (cons (cons (cons (quote лист-101000) (quote лист-101001)) (cons (quote лист-101010) (quote лист-101011))) (cons (cons (quote лист-101100) (quote лист-101101)) (cons (quote лист-101110) (quote лист-101111))))) (cons (cons (cons (cons (quote лист-110000) (quote лист-110001)) (cons (quote лист-110010) (quote лист-110011))) (cons (cons (quote лист-110100) (quote лист-110101)) (cons (quote лист-110110) (quote лист-110111)))) (cons (cons (cons (quote лист-111000) (quote лист-111001)) (cons (quote лист-111010) (quote лист-111011))) (cons (cons (quote лист-111100) (quote лист-111101)) (cons (quote лист-111110) (quote лист-111111))))))))
