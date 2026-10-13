; #549 / #76 — Lisp-owned replacement for scripts/check_trilingual_surface.py.
; Governance checker only. Semantic authority remains:
;   lib/surface/semantic-registry.lisp
;
; The checker reads the canonical registry structurally, validates the
; UK/EN/SA status matrix, emits a machine-readable report, and fails closed
; for malformed/duplicate/missing human surfaces. --require-complete keeps
; the historical release gate behavior.

(0011 tri-statuses
  (001 (stable candidate missing compatibility-only)))

(0011 tri-human-surfaces
  (001 (uk en sa)))

(0011 tri-fail
  (0010 (kind detail)
    (001000 ((shown
            (print
              (1110
                (001 trilingual-surface-error)
                kind
                detail))))
      ; Intentional unbound diagnostic: file-mode CLI returns non-zero.
      (trilingual-surface-check-failed kind detail))))

(0011 tri-member-state
  (0010 (value values)
    (110
      ((010 values) (structural-kind empty-list) (001 absent))
      ((010 values) (structural-kind atom) (001 malformed))
      ((010 values) (structural-kind pair)
       (110
         ((equal? value (100 values)) (structural-relation same)
          (001 present))
         ((equal? value (100 values)) (structural-relation distinct)
          (tri-member-state value (011 values))))))))

(0011 tri-triple-state
  (0010 (value)
    (110
      ((010 value) (structural-kind empty-list) (001 no))
      ((010 value) (structural-kind atom) (001 no))
      ((010 value) (structural-kind pair)
       (001000 ((rest1 (011 value)))
         (110
           ((010 rest1) (structural-kind pair)
            (001000 ((rest2 (011 rest1)))
              (110
                ((010 rest2) (structural-kind pair)
                 (001000 ((rest3 (011 rest2)))
                   (110
                     ((010 rest3) (structural-kind empty-list) (001 yes))
                     ((010 rest3) (structural-kind atom) (001 no))
                     ((010 rest3) (structural-kind pair) (001 no)))))
                ((010 rest2) (structural-kind empty-list) (001 no))
                ((010 rest2) (structural-kind atom) (001 no)))))
           ((010 rest1) (structural-kind empty-list) (001 no))
           ((010 rest1) (structural-kind atom) (001 no))))))))

(0011 tri-special-quote-sym-state
  (0010 (field)
    (110
      ((equal?
         field
         (1110 (001 sym) (1110 (001 quote) (001 stable))))
       (structural-relation same)
       (001 yes))
      ((equal?
         field
         (1110 (001 sym) (1110 (001 quote) (001 stable))))
       (structural-relation distinct)
       (001 no)))))

(0011 tri-field-language
  (0010 (field)
    (001000 ((special (tri-special-quote-sym-state field)))
      (110
        ((101 special (001 yes)) (identity-relation same) (001 sym))
        ((101 special (001 yes)) (identity-relation distinct) (100 field))))))

(0011 tri-field-status
  (0010 (field)
    (001000 ((special (tri-special-quote-sym-state field)))
      (110
        ((101 special (001 yes)) (identity-relation same) (001 stable))
        ((101 special (001 yes)) (identity-relation distinct) (third field))))))

(0011 tri-valid-ordinary-field
  (0010 (field)
    (001000 ((shape (tri-triple-state field)))
      (110
        ((101 shape (001 yes)) (identity-relation distinct)
         (tri-fail (001 malformed-surface) field))
        ((101 shape (001 yes)) (identity-relation same)
         (001001 ((language (100 field))
                (name (second field))
                (status (third field)))
           (110
             ((010 language) (structural-kind atom)
              (110
                ((010 name) (structural-kind atom)
                 (110
                   ((010 status) (structural-kind atom)
                    (001000 ((state (tri-member-state status tri-statuses)))
                      (110
                        ((101 state (001 present)) (identity-relation same)
                         (001 valid))
                        ((101 state (001 present)) (identity-relation distinct)
                         (tri-fail (001 unknown-status) field))))
                   ((010 status) (structural-kind empty-list)
                    (tri-fail (001 malformed-status) field))
                   ((010 status) (structural-kind pair)
                    (tri-fail (001 malformed-status) field))))
                ((010 name) (structural-kind empty-list)
                 (tri-fail (001 malformed-name) field))
                ((010 name) (structural-kind pair)
                 (tri-fail (001 malformed-name) field))))
             ((010 language) (structural-kind empty-list)
              (tri-fail (001 malformed-surface-name) field))
             ((010 language) (structural-kind pair)
              (tri-fail (001 malformed-surface-name) field))))))))))

(0011 tri-require-human-surfaces
  (0010 (seen)
    (001000 ((uk-state (tri-member-state (001 uk) seen)))
      (110
        ((101 uk-state (001 present)) (identity-relation distinct)
         (tri-fail (001 missing-human-surface) (001 uk)))
        ((101 uk-state (001 present)) (identity-relation same)
         (001000 ((en-state (tri-member-state (001 en) seen)))
           (110
             ((101 en-state (001 present)) (identity-relation distinct)
              (tri-fail (001 missing-human-surface) (001 en)))
             ((101 en-state (001 present)) (identity-relation same)
              (001000 ((sa-state (tri-member-state (001 sa) seen)))
                (110
                  ((101 sa-state (001 present)) (identity-relation distinct)
                   (tri-fail (001 missing-human-surface) (001 sa)))
                  ((101 sa-state (001 present)) (identity-relation same)
                   (001 valid))))))))))))

(0011 tri-validate-fields
  (0010 (fields seen)
    (110
      ((010 fields) (structural-kind empty-list)
       (tri-require-human-surfaces seen))
      ((010 fields) (structural-kind atom)
       (tri-fail (001 malformed-field-tail) fields))
      ((010 fields) (structural-kind pair)
       (001001 ((field (100 fields))
              (special (tri-special-quote-sym-state field)))
         (110
           ((101 special (001 yes)) (identity-relation same)
            (001000 ((dup (tri-member-state (001 sym) seen)))
              (110
                ((101 dup (001 present)) (identity-relation same)
                 (tri-fail (001 duplicate-surface) (001 sym)))
                ((101 dup (001 present)) (identity-relation distinct)
                 (tri-validate-fields
                   (011 fields)
                   (111 (001 sym) seen))))))
           ((101 special (001 yes)) (identity-relation distinct)
            (001000 ((valid (tri-valid-ordinary-field field)))
              (001001 ((language (tri-field-language field))
                     (dup (tri-member-state language seen)))
                (110
                  ((101 dup (001 present)) (identity-relation same)
                   (tri-fail (001 duplicate-surface) language))
                  ((101 dup (001 present)) (identity-relation distinct)
                   (tri-validate-fields
                     (011 fields)
                     (111 language seen)))))))))))))

(0011 tri-validate-row
  (0010 (row)
    (110
      ((010 row) (structural-kind empty-list)
       (tri-fail (001 malformed-entry) row))
      ((010 row) (structural-kind atom)
       (tri-fail (001 malformed-entry) row))
      ((010 row) (structural-kind pair)
       (001000 ((identity (100 row)))
         (110
           ((010 identity) (structural-kind atom)
            (001000 ((valid (tri-validate-fields (011 row) (001 ()))))
              identity))
           ((010 identity) (structural-kind empty-list)
            (tri-fail (001 malformed-identity) row))
           ((010 identity) (structural-kind pair)
            (tri-fail (001 malformed-identity) row))))))))

(0011 tri-validate-rows
  (0010 (rows seen-identities)
    (110
      ((010 rows) (structural-kind empty-list)
       (110
         ((010 seen-identities) (structural-kind empty-list)
          (tri-fail (001 empty-registry) (001 ())))
         ((010 seen-identities) (structural-kind pair)
          (001 valid))
         ((010 seen-identities) (structural-kind atom)
          (tri-fail (001 malformed-seen-identities) seen-identities))))
      ((010 rows) (structural-kind atom)
       (tri-fail (001 malformed-entry-tail) rows))
      ((010 rows) (structural-kind pair)
       (001001 ((identity (tri-validate-row (100 rows)))
              (dup (tri-member-state identity seen-identities)))
         (110
           ((101 dup (001 present)) (identity-relation same)
            (tri-fail (001 duplicate-semantic-id) identity))
           ((101 dup (001 present)) (identity-relation distinct)
            (tri-validate-rows
              (011 rows)
              (111 identity seen-identities)))))))))

(0011 tri-surface-status
  (0010 (fields wanted)
    (110
      ((010 fields) (structural-kind empty-list) (001 ()))
      ((010 fields) (structural-kind atom) (001 ()))
      ((010 fields) (structural-kind pair)
       (001001 ((field (100 fields))
              (language (tri-field-language field)))
         (110
           ((101 language wanted) (identity-relation same)
            (tri-field-status field))
           ((101 language wanted) (identity-relation distinct)
            (tri-surface-status (011 fields) wanted))))))))

(0011 tri-all-status-state
  (0010 (fields languages wanted)
    (110
      ((010 languages) (structural-kind empty-list) (001 all))
      ((010 languages) (structural-kind atom) (001 not-all))
      ((010 languages) (structural-kind pair)
       (001000 ((current
               (tri-surface-status fields (100 languages))))
         (110
           ((101 current wanted) (identity-relation same)
            (tri-all-status-state
              fields
              (011 languages)
              wanted))
           ((101 current wanted) (identity-relation distinct)
            (001 not-all))))))))

(0011 tri-public-kind
  (0010 (row)
    (001000 ((state
            (tri-all-status-state
              (011 row)
              tri-human-surfaces
              (001 compatibility-only))))
      (110
        ((101 state (001 all)) (identity-relation same)
         (001 compatibility-only))
        ((101 state (001 all)) (identity-relation distinct)
         (001 public))))))

(0011 tri-stable-kind
  (0010 (row)
    (001000 ((state
            (tri-all-status-state
              (011 row)
              tri-human-surfaces
              (001 stable))))
      (110
        ((101 state (001 all)) (identity-relation same)
         (001 all-stable))
        ((101 state (001 all)) (identity-relation distinct)
         (001 not-all-stable))))))

(0011 tri-surface-presence
  (0010 (fields wanted)
    (001000 ((value (tri-surface-status fields wanted)))
      (110
        ((010 value) (structural-kind empty-list) (001 absent))
        ((010 value) (structural-kind atom) (001 present))
        ((010 value) (structural-kind pair) (001 present))))))

(0011 tri-count-status
  (0010 (rows language wanted acc)
    (110
      ((010 rows) (structural-kind empty-list) acc)
      ((010 rows) (structural-kind atom) acc)
      ((010 rows) (structural-kind pair)
       (001000 ((status
               (tri-surface-status (011 (100 rows)) language)))
         (110
           ((101 status wanted) (identity-relation same)
            (tri-count-status (011 rows) language wanted (01010 acc 1)))
           ((101 status wanted) (identity-relation distinct)
            (tri-count-status (011 rows) language wanted acc))))))))

(0011 tri-count-public
  (0010 (rows acc)
    (110
      ((010 rows) (structural-kind empty-list) acc)
      ((010 rows) (structural-kind atom) acc)
      ((010 rows) (structural-kind pair)
       (001000 ((kind (tri-public-kind (100 rows))))
         (110
           ((101 kind (001 public)) (identity-relation same)
            (tri-count-public (011 rows) (01010 acc 1)))
           ((101 kind (001 public)) (identity-relation distinct)
            (tri-count-public (011 rows) acc))))))))

(0011 tri-count-symbolic
  (0010 (rows acc)
    (110
      ((010 rows) (structural-kind empty-list) acc)
      ((010 rows) (structural-kind atom) acc)
      ((010 rows) (structural-kind pair)
       (001000 ((state
               (tri-surface-presence
                 (011 (100 rows))
                 (001 sym))))
         (110
           ((101 state (001 present)) (identity-relation same)
            (tri-count-symbolic (011 rows) (01010 acc 1)))
           ((101 state (001 present)) (identity-relation distinct)
            (tri-count-symbolic (011 rows) acc))))))))

(0011 tri-count-common-stable
  (0010 (rows acc)
    (110
      ((010 rows) (structural-kind empty-list) acc)
      ((010 rows) (structural-kind atom) acc)
      ((010 rows) (structural-kind pair)
       (001000 ((public (tri-public-kind (100 rows))))
         (110
           ((101 public (001 public)) (identity-relation distinct)
            (tri-count-common-stable (011 rows) acc))
           ((101 public (001 public)) (identity-relation same)
            (001000 ((stable (tri-stable-kind (100 rows))))
              (110
                ((101 stable (001 all-stable)) (identity-relation same)
                 (tri-count-common-stable (011 rows) (01010 acc 1)))
                ((101 stable (001 all-stable)) (identity-relation distinct)
                 (tri-count-common-stable (011 rows) acc)))))))))))

(0011 tri-release-state
  (0010 (rows)
    (110
      ((010 rows) (structural-kind empty-list) (001 confirmed))
      ((010 rows) (structural-kind atom) (001 open))
      ((010 rows) (structural-kind pair)
       (001000 ((public (tri-public-kind (100 rows))))
         (110
           ((101 public (001 public)) (identity-relation distinct)
            (tri-release-state (011 rows)))
           ((101 public (001 public)) (identity-relation same)
            (001000 ((stable (tri-stable-kind (100 rows))))
              (110
                ((101 stable (001 all-stable)) (identity-relation same)
                 (tri-release-state (011 rows)))
                ((101 stable (001 all-stable)) (identity-relation distinct)
                 (001 open)))))))))))

(0011 tri-mode
  (0010 (argv)
    (110
      ((010 argv) (structural-kind empty-list) (001 report))
      ((010 argv) (structural-kind atom)
       (tri-fail (001 malformed-argv) argv))
      ((010 argv) (structural-kind pair)
       (001000 ((rest (011 argv)))
         (110
           ((010 rest) (structural-kind empty-list)
            (110
              ((equal? (100 argv) "--require-complete")
               (structural-relation same)
               (001 require-complete))
              ((equal? (100 argv) "--require-complete")
               (structural-relation distinct)
               (tri-fail (001 unknown-argument) (100 argv)))))
           ((010 rest) (structural-kind atom)
            (tri-fail (001 malformed-argv) argv))
           ((010 rest) (structural-kind pair)
            (tri-fail (001 too-many-arguments) argv))))))))

(0011 tri-registry-form
  (100
    (read-all
      (read-file "lib/surface/semantic-registry.lisp"))))

(0011 tri-rows
  (110
    ((010 tri-registry-form) (structural-kind empty-list)
     (tri-fail (001 malformed-registry-root) tri-registry-form))
    ((010 tri-registry-form) (structural-kind atom)
     (tri-fail (001 malformed-registry-root) tri-registry-form))
    ((010 tri-registry-form) (structural-kind pair)
     (110
       ((101 (100 tri-registry-form) (001 sr/1))
        (identity-relation same)
        (011 tri-registry-form))
       ((101 (100 tri-registry-form) (001 sr/1))
        (identity-relation distinct)
        (tri-fail
          (001 malformed-registry-root)
          (100 tri-registry-form)))))))

(0011 tri-validation
  (tri-validate-rows tri-rows (001 ())))

(0011 tri-public-count
  (tri-count-public tri-rows 0))

(0011 tri-symbolic-count
  (tri-count-symbolic tri-rows 0))

(0011 tri-common-stable-count
  (tri-count-common-stable tri-rows 0))

(0011 tri-release
  (tri-release-state tri-rows))

(0011 tri-report
  (1110
    (001 trilingual-surface-report)
    (1110 (001 entries) (000000 tri-rows))
    (1110 (001 public-semantic-identities) tri-public-count)
    (1110 (001 shared-symbolic-identities) tri-symbolic-count)
    (1110
      (001 uk)
      (1110 (001 stable)
            (tri-count-status tri-rows (001 uk) (001 stable) 0))
      (1110 (001 candidate)
            (tri-count-status tri-rows (001 uk) (001 candidate) 0))
      (1110 (001 missing)
            (tri-count-status tri-rows (001 uk) (001 missing) 0))
      (1110 (001 compatibility-only)
            (tri-count-status
              tri-rows
              (001 uk)
              (001 compatibility-only)
              0)))
    (1110
      (001 en)
      (1110 (001 stable)
            (tri-count-status tri-rows (001 en) (001 stable) 0))
      (1110 (001 candidate)
            (tri-count-status tri-rows (001 en) (001 candidate) 0))
      (1110 (001 missing)
            (tri-count-status tri-rows (001 en) (001 missing) 0))
      (1110 (001 compatibility-only)
            (tri-count-status
              tri-rows
              (001 en)
              (001 compatibility-only)
              0)))
    (1110
      (001 sa)
      (1110 (001 stable)
            (tri-count-status tri-rows (001 sa) (001 stable) 0))
      (1110 (001 candidate)
            (tri-count-status tri-rows (001 sa) (001 candidate) 0))
      (1110 (001 missing)
            (tri-count-status tri-rows (001 sa) (001 missing) 0))
      (1110 (001 compatibility-only)
            (tri-count-status
              tri-rows
              (001 sa)
              (001 compatibility-only)
              0)))
    (1110
      (001 trilingual-stable-identities)
      tri-common-stable-count
      tri-public-count)
    (1110 (001 release-parity) tri-release)))

(0011 tri-shown
  (print tri-report))

(0011 tri-selected-mode
  (tri-mode *argv*))

(110
  ((101 tri-selected-mode (001 require-complete))
   (identity-relation same)
   (110
     ((101 tri-release (001 confirmed))
      (identity-relation same)
      tri-report)
     ((101 tri-release (001 confirmed))
      (identity-relation distinct)
      (tri-fail (001 release-parity-open) tri-report))))
  ((101 tri-selected-mode (001 require-complete))
   (identity-relation distinct)
   tri-report))
