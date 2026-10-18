; D10 PAIP research compositions: MKLIST, MAPPEND, one-level FLATTEN.
; Domain coordinates in lib/domains/d10.lisp; no D10 direct-call admission.
; Positive and falsifying D1 comparisons: expect (1 1 1 1 1 1 1 0 0 1).
(список
  (equal? (утворити-список (quote яблуко))
          (список (quote яблуко)))
  (equal? (утворити-список (список (quote яблуко) (quote груша)))
          (список (quote яблуко) (quote груша)))
  (порожній? (утворити-список (quote ())))
  (equal?
    (відобразити-й-додати
      (lambda (елемент) (список елемент (quote хвіст)))
      (список (quote яблуко) (quote груша)))
    (список (quote яблуко) (quote хвіст) (quote груша) (quote хвіст)))
  (порожній?
    (відобразити-й-додати
      (lambda (елемент) (список елемент)) (quote ())))
  (equal?
    (сплющити
      (список (список (quote яблуко) (quote груша))
            (quote слива) (список (quote вишня))))
    (список (quote яблуко) (quote груша) (quote слива) (quote вишня)))
  (equal?
    (сплющити
      (список (список (quote яблуко) (список (quote груша))) (quote слива)))
    (список (quote яблуко) (список (quote груша)) (quote слива)))
  (equal?
    (сплющити
      (список (список (quote яблуко) (список (quote груша))) (quote слива)))
    (список (quote яблуко) (quote груша) (quote слива)))
  (equal?
    (відобразити-й-додати
      (lambda (елемент) (список елемент (quote хвіст)))
      (список (quote яблуко) (quote груша)))
    (список (quote груша) (quote хвіст) (quote яблуко) (quote хвіст)))
  (порожній?
    (відобразити-й-додати
      (lambda (елемент) (quote ())) (список (quote яблуко))))
)

; opt-in повна укр-поверхня: exact identity = lib/domains/d*.lisp; DEFINE-аліас, без нової диспетчеризації.
(визначити список list)
(визначити порожній? null?)
