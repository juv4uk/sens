; #1145 executable witness for the yantraOS bridge contract.
;
; The witness proves the intended composition without network access:
; my-lisp constructs a typed action envelope, yantraOS is represented as
; the execution owner, and the returned execution observation remains data.
; No raw shell command is admitted to the envelope.

(00001001 yo-proper-list?
  (00001000 (value)
    (00000111
      ((00000010 value)
       (1)
       (00000111
         ((00100010 value (00000001 ()))
          (1)
          (00000001 yes))
         ((00000001 always)
          (00000001 always)
          (00000001 invalid))))
      ((00000001 always)
       (00000001 always)
       (yo-proper-list? (00000110 value))))))

(00001001 yo-field
  (00001000 (name record)
    (10011100 ((found (00101101 name record)))
      (00000111
        ((00100010 found (00000001 ()))
         (1)
         (00000001 ()))
        ((00000001 always)
         (00000001 always)
         (00000110 found))))))

(00001001 yo-has-field?
  (00001000 (name record)
    (10011100 ((found (00101101 name record)))
      (00000111
        ((00100010 found (00000001 ()))
         (1)
         (00000001 no))
        ((00000001 always)
         (00000001 always)
         (00000001 yes))))))

(00001001 yo-no-raw-shell?
  (00001000 (envelope)
    (10011100 ((action (yo-field (00000001 action) envelope))
          (parameters (yo-field (00000001 parameters) envelope)))
      (00000111
        ((00100010
           (yo-field (00000001 capability) action)
           (00000001 shell))
         (1)
         (00000001 no))
        ((yo-has-field? (00000001 command) parameters)
         (00000001 yes)
         (00000001 no))
        ((00000001 always)
         (00000001 always)
         (00000001 yes))))))

(00001001 yo-action-envelope
  (00001000 (goal capability operation target parameters verification provenance approval)
    (00100111
      (00000100 (00000001 protocol) (00000001 (yantraos-bridge 1)))
      (00000100 (00000001 intent)
            (00100111
              (00000100 (00000001 goal) goal)
              (00000100 (00000001 requires) (00000001 ()))
              (00000100 (00000001 stop-on) (00000001 (verified)))
              (00000100 (00000001 produces) (00000001 (execution-observation)))))
      (00000100 (00000001 action)
            (00100111
              (00000100 (00000001 capability) capability)
              (00000100 (00000001 operation) operation)
              (00000100 (00000001 target) target)))
      (00000100 (00000001 parameters) parameters)
      (00000100 (00000001 verification) verification)
      (00000100 (00000001 provenance) provenance)
      (00000100 (00000001 approval) approval))))

(00001001 yo-action-envelope?
  (00001000 (value)
    (00000111
      ((yo-proper-list? value)
       (00000001 yes)
       (00000111
         ((yo-has-field? (00000001 protocol) value)
          (00000001 yes)
          (00000111
            ((yo-has-field? (00000001 intent) value)
             (00000001 yes)
             (00000111
               ((yo-has-field? (00000001 action) value)
                (00000001 yes)
                (00000111
                  ((yo-has-field? (00000001 parameters) value)
                   (00000001 yes)
                   (00000111
                     ((yo-has-field? (00000001 verification) value)
                      (00000001 yes)
                      (00000111
                        ((yo-has-field? (00000001 provenance) value)
                         (00000001 yes)
                         (00000111
                           ((yo-has-field? (00000001 approval) value)
                            (00000001 yes)
                            (yo-no-raw-shell? value))
                           ((00000001 always)
                            (00000001 always)
                            (00000001 no))))
                        ((00000001 always)
                         (00000001 always)
                         (00000001 no))))
                     ((00000001 always)
                      (00000001 always)
                      (00000001 no))))
                  ((00000001 always)
                   (00000001 always)
                   (00000001 no))))
               ((00000001 always)
                (00000001 always)
                (00000001 no))))
            ((00000001 always)
             (00000001 always)
             (00000001 no))))
         ((00000001 always)
          (00000001 always)
          (00000001 no))))
      ((00000001 always)
       (00000001 always)
       (00000001 no)))))

(00001001 yo-execution-observation
  (00001000 (result route evidence audit-ref provenance)
    (00100111
      (00000100 (00000001 protocol) (00000001 (yantraos-bridge 1)))
      (00000100 (00000001 result) result)
      (00000100 (00000001 route) route)
      (00000100 (00000001 evidence) evidence)
      (00000100 (00000001 audit-ref) audit-ref)
      (00000100 (00000001 provenance) provenance))))

(00001001 yo-execution-observation?
  (00001000 (value)
    (00000111
      ((yo-proper-list? value)
       (00000001 yes)
       (00000111
         ((yo-has-field? (00000001 protocol) value)
          (00000001 yes)
          (00000111
            ((yo-has-field? (00000001 result) value)
             (00000001 yes)
             (00000111
               ((yo-has-field? (00000001 route) value)
                (00000001 yes)
                (00000111
                  ((yo-has-field? (00000001 evidence) value)
                   (00000001 yes)
                   (00000111
                     ((yo-has-field? (00000001 audit-ref) value)
                      (00000001 yes)
                      (yo-has-field? (00000001 provenance) value))
                     ((00000001 always)
                      (00000001 always)
                      (00000001 no))))
                  ((00000001 always)
                   (00000001 always)
                   (00000001 no))))
               ((00000001 always)
                (00000001 always)
                (00000001 no))))
            ((00000001 always)
             (00000001 always)
             (00000001 no))))
         ((00000001 always)
          (00000001 always)
          (00000001 no))))
      ((00000001 always)
       (00000001 always)
       (00000001 no)))))
