; Native SENS: D8:11110001 ANY(NOT p) та D8:11110011 ALL(NOT p).
; Шість D1-свідків: позитив, негатив та порожня структура.
(list
  (є-що-не-задовольняє? (lambda (x) (eq? x (quote яблуко)))
                          (list (quote яблуко) (quote груша)))
  (not? (є-що-не-задовольняє? (lambda (x) (eq? x (quote яблуко)))
                                  (list (quote яблуко))))
  (not? (є-що-не-задовольняє? (lambda (x) (eq? x (quote яблуко)))
                                  (list)))
  (усі-не-задовольняють? (lambda (x) (eq? x (quote яблуко)))
                           (list (quote груша) (quote груша)))
  (not? (усі-не-задовольняють? (lambda (x) (eq? x (quote яблуко)))
                                  (list (quote груша) (quote яблуко))))
  (усі-не-задовольняють? (lambda (x) (eq? x (quote яблуко)))
                           (list)))
