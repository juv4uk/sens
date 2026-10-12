; #1145 executable witness for the yantraOS bridge contract.
;
; The witness proves the intended composition without network access:
; SENS constructs a typed action envelope, yantraOS is represented as
; the execution owner, and the returned execution observation remains data.
; No raw shell command is admitted to the envelope.

(0011 yo-proper-list?
  (0010 (value)
    (110
      ((010 value)
       (1)
       (110
         ((11110111 value (001 ()))
          (1)
          (001 yes))
         ((001 always)
          (001 always)
          (001 invalid))))
      ((001 always)
       (001 always)
       (yo-proper-list? (011 value))))))

(0011 yo-field
  (0010 (name record)
    (001000 ((found (11100 name record)))
      (110
        ((11110111 found (001 ()))
         (1)
         (001 ()))
        ((001 always)
         (001 always)
         (011 found))))))

(0011 yo-has-field?
  (0010 (name record)
    (001000 ((found (11100 name record)))
      (110
        ((11110111 found (001 ()))
         (1)
         (001 no))
        ((001 always)
         (001 always)
         (001 yes))))))

(0011 yo-no-raw-shell?
  (0010 (envelope)
    (001000 ((action (yo-field (001 action) envelope))
          (parameters (yo-field (001 parameters) envelope)))
      (110
        ((11110111
           (yo-field (001 capability) action)
           (001 shell))
         (1)
         (001 no))
        ((yo-has-field? (001 command) parameters)
         (001 yes)
         (001 no))
        ((001 always)
         (001 always)
         (001 yes))))))

(0011 yo-action-envelope
  (0010 (goal capability operation target parameters verification provenance approval)
    (1110
      (111 (001 protocol) (001 (yantraos-bridge 1)))
      (111 (001 intent)
            (1110
              (111 (001 goal) goal)
              (111 (001 requires) (001 ()))
              (111 (001 stop-on) (001 (verified)))
              (111 (001 produces) (001 (execution-observation)))))
      (111 (001 action)
            (1110
              (111 (001 capability) capability)
              (111 (001 operation) operation)
              (111 (001 target) target)))
      (111 (001 parameters) parameters)
      (111 (001 verification) verification)
      (111 (001 provenance) provenance)
      (111 (001 approval) approval))))

(0011 yo-action-envelope?
  (0010 (value)
    (110
      ((yo-proper-list? value)
       (001 yes)
       (110
         ((yo-has-field? (001 protocol) value)
          (001 yes)
          (110
            ((yo-has-field? (001 intent) value)
             (001 yes)
             (110
               ((yo-has-field? (001 action) value)
                (001 yes)
                (110
                  ((yo-has-field? (001 parameters) value)
                   (001 yes)
                   (110
                     ((yo-has-field? (001 verification) value)
                      (001 yes)
                      (110
                        ((yo-has-field? (001 provenance) value)
                         (001 yes)
                         (110
                           ((yo-has-field? (001 approval) value)
                            (001 yes)
                            (yo-no-raw-shell? value))
                           ((001 always)
                            (001 always)
                            (001 no))))
                        ((001 always)
                         (001 always)
                         (001 no))))
                     ((001 always)
                      (001 always)
                      (001 no))))
                  ((001 always)
                   (001 always)
                   (001 no))))
               ((001 always)
                (001 always)
                (001 no))))
            ((001 always)
             (001 always)
             (001 no))))
         ((001 always)
          (001 always)
          (001 no))))
      ((001 always)
       (001 always)
       (001 no)))))

(0011 yo-execution-observation
  (0010 (result route evidence audit-ref provenance)
    (1110
      (111 (001 protocol) (001 (yantraos-bridge 1)))
      (111 (001 result) result)
      (111 (001 route) route)
      (111 (001 evidence) evidence)
      (111 (001 audit-ref) audit-ref)
      (111 (001 provenance) provenance))))

(0011 yo-execution-observation?
  (0010 (value)
    (110
      ((yo-proper-list? value)
       (001 yes)
       (110
         ((yo-has-field? (001 protocol) value)
          (001 yes)
          (110
            ((yo-has-field? (001 result) value)
             (001 yes)
             (110
               ((yo-has-field? (001 route) value)
                (001 yes)
                (110
                  ((yo-has-field? (001 evidence) value)
                   (001 yes)
                   (110
                     ((yo-has-field? (001 audit-ref) value)
                      (001 yes)
                      (yo-has-field? (001 provenance) value))
                     ((001 always)
                      (001 always)
                      (001 no))))
                  ((001 always)
                   (001 always)
                   (001 no))))
               ((001 always)
                (001 always)
                (001 no))))
            ((001 always)
             (001 always)
             (001 no))))
         ((001 always)
          (001 always)
          (001 no))))
      ((001 always)
       (001 always)
       (001 no)))))
