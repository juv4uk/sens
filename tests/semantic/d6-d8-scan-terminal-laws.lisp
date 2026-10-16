; Вісім точкових нативних SENS свідків D6:101111 SCAN / D8:10111011 SCAN-right.
; Контракт #3370/#3674: terminal, noncommutative orientation, empty unchanged.
; Кожний НЕкоментований рядок — окрема програма, очікувана відповідь D1:1.
(equal? (накопичувати (lambda (стан елемент) (cons елемент стан)) (quote ()) (list (quote яблуко) (quote груша))) (list (quote ()) (list (quote яблуко)) (list (quote груша) (quote яблуко))))
(not? (equal? (накопичувати (lambda (стан елемент) (cons елемент стан)) (quote ()) (list (quote яблуко) (quote груша))) (list (quote ()) (list (quote яблуко)))))
(equal? (накопичувати (lambda (стан елемент) (cons елемент стан)) (quote ()) (list (quote яблуко))) (list (quote ()) (list (quote яблуко))))
(equal? (накопичувати-справа (lambda (лівий правий) (cons лівий правий)) (quote ()) (list (quote яблуко) (quote груша))) (list (quote ()) (list (quote груша)) (list (quote яблуко) (quote груша))))
(equal? (car (reverse (накопичувати-справа (lambda (лівий правий) (cons лівий правий)) (quote ()) (list (quote яблуко) (quote груша))))) (згорнути-справа (lambda (лівий правий) (cons лівий правий)) (quote ()) (list (quote яблуко) (quote груша))))
(not? (equal? (накопичувати-справа (lambda (лівий правий) (cons лівий правий)) (quote ()) (list (quote яблуко) (quote груша))) (list (quote ()) (list (quote яблуко)) (list (quote груша) (quote яблуко)))))
(null? (накопичувати (lambda (стан елемент) (cons елемент стан)) (quote ()) (quote ())))
(null? (накопичувати-справа (lambda (лівий правий) (cons лівий правий)) (quote ()) (quote ())))
