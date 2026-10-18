; D8:00001011 MAPLIST* native SENS witnesses, final empty suffix is observable.
; No direct D8 opcode admission is asserted.
(список
  (equal?
    (залишки+порожнє (quote ()) (lambda (хвіст) хвіст))
    (список (quote ())))
  (equal?
    (залишки+порожнє (список (quote ())) (lambda (хвіст) хвіст))
    (список (список (quote ())) (quote ())))
  (equal?
    (залишки+порожнє (список (quote ()) (список (quote ())))
      (lambda (хвіст) хвіст))
    (список (список (quote ()) (список (quote ())))
          (список (список (quote ())))
          (quote ())))
  (хибне?
    (equal?
      (залишки+порожнє (список (quote ())) (lambda (хвіст) хвіст))
      (відобразити-залишки (список (quote ())) (lambda (хвіст) хвіст)))))

; opt-in повна укр-поверхня: exact identity = lib/domains/d*.lisp; DEFINE-аліас, без нової диспетчеризації.
(визначити список list)
(визначити хибне? not?)
