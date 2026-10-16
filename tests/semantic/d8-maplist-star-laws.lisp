; D8:00001011 MAPLIST* native SENS witnesses, final empty suffix is observable.
; No direct D8 opcode admission is asserted.
(list
  (equal?
    (залишки+порожнє (quote ()) (lambda (хвіст) хвіст))
    (list (quote ())))
  (equal?
    (залишки+порожнє (list (quote ())) (lambda (хвіст) хвіст))
    (list (list (quote ())) (quote ())))
  (equal?
    (залишки+порожнє (list (quote ()) (list (quote ())))
      (lambda (хвіст) хвіст))
    (list (list (quote ()) (list (quote ())))
          (list (list (quote ())))
          (quote ())))
  (not?
    (equal?
      (залишки+порожнє (list (quote ())) (lambda (хвіст) хвіст))
      (відобразити-залишки (list (quote ())) (lambda (хвіст) хвіст)))))
