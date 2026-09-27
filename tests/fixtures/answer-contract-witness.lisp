; #228/#244 — Lisp-owned executable witness for the layered answer-contract data.
;
; contracts/answer-contract.lisp is pure data. The host test transports its
; UTF-8 source text into Lisp and defines `answer-contract-document` through
; the Lisp reader. This witness owns every semantic expectation below; Rust
; owns only file-byte transport because core my-lisp intentionally has no
; implicit filesystem capability.

(00001001 answer-contract-schema
  (00001000 () (00000101 answer-contract-document)))

(00001001 answer-contract-entries
  (00001000 () (00000110 answer-contract-document)))

(00001001 answer-contract-field
  (00001000 (entry field)
    (10011100 ((found (00101101 field entry)))
      (00000111
        ((00000010 found) () (00000001 ()))
        ((00000010 found) (1) (00000001 ()))
        (t (00000110 found))))))

(00001001 answer-contract-find
  (00001000 (identity entries)
    (00000111
      ((00000010 entries) () (00000001 ()))
      ((00000010 entries) (1) (00000001 ()))
      ((00100010
         (answer-contract-field (00000101 entries) (00000001 identity))
         identity)
       (00000101 entries))
      (t (answer-contract-find identity (00000110 entries))))))

(00001001 answer-contract-entry
  (00001000 (identity)
    (answer-contract-find identity (answer-contract-entries))))

(00001001 answer-contract-witness-record
  (00001000 (status detail)
    (00100111
      (00000001 answer-contract-witness)
      (00100111 (00000001 status) status)
      (00100111 (00000001 detail) detail))))

(00001001 answer-contract-witness-expect
  (00001000 (identity field expected)
    (10011100 ((entry (answer-contract-entry identity)))
      (00000111
        ((00000010 entry) () (00100111 (00000001 missing-entry) identity field expected))
        ((00000010 entry) (1) (00100111 (00000001 missing-entry) identity field expected))
        ((00100010 (answer-contract-field entry field) expected)
         (00000001 ()))
        (t
         (00100111
           (00000001 mismatch)
           identity
           field
           expected
           (answer-contract-field entry field)))))))

; #244 negative law: Canon 0 is not an alias for any stronger domain-owned
; state. A pass is represented by () because this helper itself only reports
; a failure when an accidental semantic collapse is detected.
(00001001 answer-contract-witness-expect-distinct
  (00001000 (left right)
    (00000111
      ((00100010 left right)
       (00100111 (00000001 unexpected-collapse) left right))
      (t (00000001 ())))))

(00001001 answer-contract-witness-expect-missing
  (00001000 (identity)
    (00000111
      ((00000010 (answer-contract-entry identity)) () (00000001 ()))
      ((00000010 (answer-contract-entry identity)) (1) (00000001 ()))
      (t (00100111 (00000001 unexpected-entry) identity)))))

(00001001 answer-contract-witness-first-failure
  (00001000 (checks)
    (00000111
      ((00000010 checks) () (00000001 ()))
      ((00000010 checks) (1) (00000001 ()))
      ((00000010 (00000101 checks)) () (answer-contract-witness-first-failure (00000110 checks)))
      ((00000010 (00000101 checks)) (1) (answer-contract-witness-first-failure (00000110 checks)))
      (t (00000101 checks)))))

(00001001 answer-contract-witness
  (00001000 ()
    (10011100 ((failure
            (answer-contract-witness-first-failure
              (00100111
                (answer-contract-witness-expect
                  (00000001 canon-zero)
                  (00000001 domain-owner)
                  (00000001 no-answer-boundary))
                (answer-contract-witness-expect
                  (00000001 canon-zero)
                  (00000001 answer-role)
                  (00000001 unspecialized-accumulator))
                (answer-contract-witness-expect
                  (00000001 canon-zero)
                  (00000001 indeterminacy)
                  (00000001 unresolved-specialization))
                (answer-contract-witness-expect
                  (00000001 canon-zero)
                  (00000001 specialization-policy)
                  (00000001 justified-only))
                (answer-contract-witness-expect
                  (00000001 canon-zero)
                  (00000001 cause-required)
                  (00000001 no))
                (answer-contract-witness-expect
                  (00000001 canon-zero)
                  (00000001 reentry)
                  (00000001 allowed-at-query-boundaries))
                (answer-contract-witness-expect
                  (00000001 canon-zero)
                  (00000001 result-form)
                  (00000001 empty-list))
                (answer-contract-witness-expect
                  00000100
                  (00000001 domain-owner)
                  (00000001 structure))
                (answer-contract-witness-expect
                  00000100
                  (00000001 result-form)
                  (00000001 pair))
                (answer-contract-witness-expect
                  00000010
                  (00000001 domain-owner)
                  (00000001 structural-observation))
                (answer-contract-witness-expect
                  00000010
                  (00000001 result-form)
                  (00000001 structural-kind))
                (answer-contract-witness-expect
                  00000010
                  (00000001 result-values)
                  (00000001 (()
                          (0)
                          (1))))
                (answer-contract-witness-expect
                  00000010
                  (00000001 no-answer)
                  (00000001 not-applicable))
                (answer-contract-witness-expect
                  00000011
                  (00000001 domain-owner)
                  (00000001 structural-observation))
                (answer-contract-witness-expect
                  00000011
                  (00000001 input-domain)
                  (00000001 (atom? atom)))
                (answer-contract-witness-expect
                  00000011
                  (00000001 result-form)
                  (00000001 identity-relation))
                (answer-contract-witness-expect
                  00000011
                  (00000001 result-values)
                  (00000001 ((1)
                          (0))))
                (answer-contract-witness-expect
                  00000011
                  (00000001 outside-domain)
                  (00000001 type-error))
                (answer-contract-witness-expect
                  00000011
                  (00000001 no-answer)
                  (00000001 not-applicable))
                (answer-contract-witness-expect
                  00011010
                  (00000001 domain-owner)
                  (00000001 exact-q-decision))
                (answer-contract-witness-expect
                  00011010
                  (00000001 binary-values)
                  (00000001 ("0/1" "1/1")))
                (answer-contract-witness-expect
                  00011010
                  (00000001 outside-domain)
                  (00000001 delegate))
                (answer-contract-witness-expect
                  00011010
                  (00000001 unspecialized-result)
                  (00000001 ()))
                (answer-contract-witness-expect
                  00001100
                  (00000001 domain-owner)
                  (00000001 mathematical-result))
                (answer-contract-witness-expect
                  00001100
                  (00000001 unspecialized-result)
                  (00000001 ()))
                (answer-contract-witness-expect
                  10000101
                  (00000001 domain-owner)
                  (00000001 non-mathematical-reasoning))
                (answer-contract-witness-expect
                  10000101
                  (00000001 unspecialized-result)
                  (00000001 ()))
                (answer-contract-witness-expect
                  10000101
                  (00000001 no-answer)
                  (00000001 ()))
                (answer-contract-witness-expect
                  00000111
                  (00000001 domain-owner)
                  (00000001 control-consumer))
                (answer-contract-witness-expect
                  00000111
                  (00000001 unspecialized-result)
                  (00000001 ()))
                (answer-contract-witness-expect
                  00000111
                  (00000001 generic-value-coercion)
                  (00000001 forbidden))

                ; Canon 0 preserves unresolved specialization. These explicit
                ; negative witnesses prevent future code from silently
                ; rebranding () as one stronger answer or observation class.
                (answer-contract-witness-expect-distinct (00000001 ()) 0/1)
                (answer-contract-witness-expect-distinct (00000001 ()) 1/1)
                (answer-contract-witness-expect-distinct
                  (00000001 ()) (00000001 unknown))
                (answer-contract-witness-expect-distinct
                  (00000001 ()) (00000001 conflict))
                (answer-contract-witness-expect-distinct
                  (00000001 ()) (00000001 timeout))
                (answer-contract-witness-expect-distinct
                  (00000001 ()) (00000001 error))

                ; Human spellings stay in semantic-registry.lisp. The contract
                ; is keyed by semantic identity only. Canon 0 is the one special
                ; non-ID entry because the empty list has no lexical Canon ID.
                (answer-contract-witness-expect-missing (00000001 cons))
                (answer-contract-witness-expect-missing (00000001 reason))
                ; A String that looks like an SID is still ordinary String data.
                (answer-contract-witness-expect-missing "00000100")))))
      (00000111
        ((00000011 (answer-contract-schema) (00000001 answer-contract/1))
         (00000111
           ((00000010 failure) () (answer-contract-witness-record
              (00000001 pass)
              (00000001 canon-zero-unspecialized-accumulator)))
           ((00000010 failure) (1) (answer-contract-witness-record
              (00000001 pass)
              (00000001 canon-zero-unspecialized-accumulator)))
           (t
            (answer-contract-witness-record (00000001 fail) failure))))
        (t
         (answer-contract-witness-record
           (00000001 fail)
           (00100111 (00000001 schema) (answer-contract-schema))))))))
