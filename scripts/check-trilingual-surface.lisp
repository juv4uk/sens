; #549 / #76 — Lisp-owned replacement for scripts/check_trilingual_surface.py.
; Governance checker only. Semantic authority remains:
;   lib/surface/semantic-registry.lisp
;
; The checker reads the canonical registry structurally, validates the
; UK/EN/SA status matrix, emits a machine-readable report, and fails closed
; for malformed/duplicate/missing human surfaces. --require-complete keeps
; the historical release gate behavior.

(визначити tri-statuses
  (як-є (stable candidate missing compatibility-only)))

(визначити tri-human-surfaces
  (як-є (uk en sa)))

(визначити tri-fail
  (функція (kind detail)
    (нехай ((shown
            (друкувати
              (список
                (як-є trilingual-surface-error)
                kind
                detail))))
      ; Intentional unbound diagnostic: file-mode CLI returns non-zero.
      (trilingual-surface-check-failed kind detail))))

(визначити tri-member-state
  (функція (value values)
    (за-умовою
      ((атом? values) (structural-kind empty-list) (як-є absent))
      ((атом? values) (structural-kind atom) (як-є malformed))
      ((атом? values) (structural-kind pair)
       (за-умовою
         ((однакові? value (перше values)) (structural-relation same)
          (як-є present))
         ((однакові? value (перше values)) (structural-relation distinct)
          (tri-member-state value (решта values))))))))

(визначити tri-triple-state
  (функція (value)
    (за-умовою
      ((атом? value) (structural-kind empty-list) (як-є no))
      ((атом? value) (structural-kind atom) (як-є no))
      ((атом? value) (structural-kind pair)
       (нехай ((rest1 (решта value)))
         (за-умовою
           ((атом? rest1) (structural-kind pair)
            (нехай ((rest2 (решта rest1)))
              (за-умовою
                ((атом? rest2) (structural-kind pair)
                 (нехай ((rest3 (решта rest2)))
                   (за-умовою
                     ((атом? rest3) (structural-kind empty-list) (як-є yes))
                     ((атом? rest3) (structural-kind atom) (як-є no))
                     ((атом? rest3) (structural-kind pair) (як-є no)))))
                ((атом? rest2) (structural-kind empty-list) (як-є no))
                ((атом? rest2) (structural-kind atom) (як-є no)))))
           ((атом? rest1) (structural-kind empty-list) (як-є no))
           ((атом? rest1) (structural-kind atom) (як-є no))))))))

(визначити tri-special-quote-sym-state
  (функція (field)
    (за-умовою
      ((однакові?
         field
         (список (як-є sym) (список (як-є quote) (як-є stable))))
       (structural-relation same)
       (як-є yes))
      ((однакові?
         field
         (список (як-є sym) (список (як-є quote) (як-є stable))))
       (structural-relation distinct)
       (як-є no)))))

(визначити tri-field-language
  (функція (field)
    (нехай ((спеціальна-змінна (tri-special-quote-sym-state field)))
      (за-умовою
        ((тотожне? спеціальна-змінна (як-є yes)) (identity-relation same) (як-є sym))
        ((тотожне? спеціальна-змінна (як-є yes)) (identity-relation distinct) (перше field))))))

(визначити tri-field-status
  (функція (field)
    (нехай ((спеціальна-змінна (tri-special-quote-sym-state field)))
      (за-умовою
        ((тотожне? спеціальна-змінна (як-є yes)) (identity-relation same) (як-є stable))
        ((тотожне? спеціальна-змінна (як-є yes)) (identity-relation distinct) (third field))))))

(визначити tri-valid-ordinary-field
  (функція (field)
    (нехай ((shape (tri-triple-state field)))
      (за-умовою
        ((тотожне? shape (як-є yes)) (identity-relation distinct)
         (tri-fail (як-є malformed-surface) field))
        ((тотожне? shape (як-є yes)) (identity-relation same)
         (нехай-послідовно ((language (перше field))
                (name (second field))
                (status (third field)))
           (за-умовою
             ((атом? language) (structural-kind atom)
              (за-умовою
                ((атом? name) (structural-kind atom)
                 (за-умовою
                   ((атом? status) (structural-kind atom)
                    (нехай ((state (tri-member-state status tri-statuses)))
                      (за-умовою
                        ((тотожне? state (як-є present)) (identity-relation same)
                         (як-є valid))
                        ((тотожне? state (як-є present)) (identity-relation distinct)
                         (tri-fail (як-є unknown-status) field))))
                   ((атом? status) (structural-kind empty-list)
                    (tri-fail (як-є malformed-status) field))
                   ((атом? status) (structural-kind pair)
                    (tri-fail (як-є malformed-status) field))))
                ((атом? name) (structural-kind empty-list)
                 (tri-fail (як-є malformed-name) field))
                ((атом? name) (structural-kind pair)
                 (tri-fail (як-є malformed-name) field))))
             ((атом? language) (structural-kind empty-list)
              (tri-fail (як-є malformed-surface-name) field))
             ((атом? language) (structural-kind pair)
              (tri-fail (як-є malformed-surface-name) field))))))))))

(визначити tri-require-human-surfaces
  (функція (seen)
    (нехай ((uk-state (tri-member-state (як-є uk) seen)))
      (за-умовою
        ((тотожне? uk-state (як-є present)) (identity-relation distinct)
         (tri-fail (як-є missing-human-surface) (як-є uk)))
        ((тотожне? uk-state (як-є present)) (identity-relation same)
         (нехай ((en-state (tri-member-state (як-є en) seen)))
           (за-умовою
             ((тотожне? en-state (як-є present)) (identity-relation distinct)
              (tri-fail (як-є missing-human-surface) (як-є en)))
             ((тотожне? en-state (як-є present)) (identity-relation same)
              (нехай ((sa-state (tri-member-state (як-є sa) seen)))
                (за-умовою
                  ((тотожне? sa-state (як-є present)) (identity-relation distinct)
                   (tri-fail (як-є missing-human-surface) (як-є sa)))
                  ((тотожне? sa-state (як-є present)) (identity-relation same)
                   (як-є valid))))))))))))

(визначити tri-validate-fields
  (функція (fields seen)
    (за-умовою
      ((атом? fields) (structural-kind empty-list)
       (tri-require-human-surfaces seen))
      ((атом? fields) (structural-kind atom)
       (tri-fail (як-є malformed-field-tail) fields))
      ((атом? fields) (structural-kind pair)
       (нехай-послідовно ((field (перше fields))
              (спеціальна-змінна (tri-special-quote-sym-state field)))
         (за-умовою
           ((тотожне? спеціальна-змінна (як-є yes)) (identity-relation same)
            (нехай ((dup (tri-member-state (як-є sym) seen)))
              (за-умовою
                ((тотожне? dup (як-є present)) (identity-relation same)
                 (tri-fail (як-є duplicate-surface) (як-є sym)))
                ((тотожне? dup (як-є present)) (identity-relation distinct)
                 (tri-validate-fields
                   (решта fields)
                   (сполучити (як-є sym) seen))))))
           ((тотожне? спеціальна-змінна (як-є yes)) (identity-relation distinct)
            (нехай ((valid (tri-valid-ordinary-field field)))
              (нехай-послідовно ((language (tri-field-language field))
                     (dup (tri-member-state language seen)))
                (за-умовою
                  ((тотожне? dup (як-є present)) (identity-relation same)
                   (tri-fail (як-є duplicate-surface) language))
                  ((тотожне? dup (як-є present)) (identity-relation distinct)
                   (tri-validate-fields
                     (решта fields)
                     (сполучити language seen)))))))))))))

(визначити tri-validate-row
  (функція (row)
    (за-умовою
      ((атом? row) (structural-kind empty-list)
       (tri-fail (як-є malformed-entry) row))
      ((атом? row) (structural-kind atom)
       (tri-fail (як-є malformed-entry) row))
      ((атом? row) (structural-kind pair)
       (нехай ((identity (перше row)))
         (за-умовою
           ((атом? identity) (structural-kind atom)
            (нехай ((valid (tri-validate-fields (решта row) (як-є ()))))
              identity))
           ((атом? identity) (structural-kind empty-list)
            (tri-fail (як-є malformed-identity) row))
           ((атом? identity) (structural-kind pair)
            (tri-fail (як-є malformed-identity) row))))))))

(визначити tri-validate-rows
  (функція (rows seen-identities)
    (за-умовою
      ((атом? rows) (structural-kind empty-list)
       (за-умовою
         ((атом? seen-identities) (structural-kind empty-list)
          (tri-fail (як-є empty-registry) (як-є ())))
         ((атом? seen-identities) (structural-kind pair)
          (як-є valid))
         ((атом? seen-identities) (structural-kind atom)
          (tri-fail (як-є malformed-seen-identities) seen-identities))))
      ((атом? rows) (structural-kind atom)
       (tri-fail (як-є malformed-entry-tail) rows))
      ((атом? rows) (structural-kind pair)
       (нехай-послідовно ((identity (tri-validate-row (перше rows)))
              (dup (tri-member-state identity seen-identities)))
         (за-умовою
           ((тотожне? dup (як-є present)) (identity-relation same)
            (tri-fail (як-є duplicate-semantic-id) identity))
           ((тотожне? dup (як-є present)) (identity-relation distinct)
            (tri-validate-rows
              (решта rows)
              (сполучити identity seen-identities)))))))))

(визначити tri-surface-status
  (функція (fields wanted)
    (за-умовою
      ((атом? fields) (structural-kind empty-list) (як-є ()))
      ((атом? fields) (structural-kind atom) (як-є ()))
      ((атом? fields) (structural-kind pair)
       (нехай-послідовно ((field (перше fields))
              (language (tri-field-language field)))
         (за-умовою
           ((тотожне? language wanted) (identity-relation same)
            (tri-field-status field))
           ((тотожне? language wanted) (identity-relation distinct)
            (tri-surface-status (решта fields) wanted))))))))

(визначити tri-all-status-state
  (функція (fields languages wanted)
    (за-умовою
      ((атом? languages) (structural-kind empty-list) (як-є all))
      ((атом? languages) (structural-kind atom) (як-є not-all))
      ((атом? languages) (structural-kind pair)
       (нехай ((current
               (tri-surface-status fields (перше languages))))
         (за-умовою
           ((тотожне? current wanted) (identity-relation same)
            (tri-all-status-state
              fields
              (решта languages)
              wanted))
           ((тотожне? current wanted) (identity-relation distinct)
            (як-є not-all))))))))

(визначити tri-public-kind
  (функція (row)
    (нехай ((state
            (tri-all-status-state
              (решта row)
              tri-human-surfaces
              (як-є compatibility-only))))
      (за-умовою
        ((тотожне? state (як-є all)) (identity-relation same)
         (як-є compatibility-only))
        ((тотожне? state (як-є all)) (identity-relation distinct)
         (як-є public))))))

(визначити tri-stable-kind
  (функція (row)
    (нехай ((state
            (tri-all-status-state
              (решта row)
              tri-human-surfaces
              (як-є stable))))
      (за-умовою
        ((тотожне? state (як-є all)) (identity-relation same)
         (як-є all-stable))
        ((тотожне? state (як-є all)) (identity-relation distinct)
         (як-є not-all-stable))))))

(визначити tri-surface-presence
  (функція (fields wanted)
    (нехай ((value (tri-surface-status fields wanted)))
      (за-умовою
        ((атом? value) (structural-kind empty-list) (як-є absent))
        ((атом? value) (structural-kind atom) (як-є present))
        ((атом? value) (structural-kind pair) (як-є present))))))

(визначити tri-count-status
  (функція (rows language wanted acc)
    (за-умовою
      ((атом? rows) (structural-kind empty-list) acc)
      ((атом? rows) (structural-kind atom) acc)
      ((атом? rows) (structural-kind pair)
       (нехай ((status
               (tri-surface-status (решта (перше rows)) language)))
         (за-умовою
           ((тотожне? status wanted) (identity-relation same)
            (tri-count-status (решта rows) language wanted (додати acc 1)))
           ((тотожне? status wanted) (identity-relation distinct)
            (tri-count-status (решта rows) language wanted acc))))))))

(визначити tri-count-public
  (функція (rows acc)
    (за-умовою
      ((атом? rows) (structural-kind empty-list) acc)
      ((атом? rows) (structural-kind atom) acc)
      ((атом? rows) (structural-kind pair)
       (нехай ((kind (tri-public-kind (перше rows))))
         (за-умовою
           ((тотожне? kind (як-є public)) (identity-relation same)
            (tri-count-public (решта rows) (додати acc 1)))
           ((тотожне? kind (як-є public)) (identity-relation distinct)
            (tri-count-public (решта rows) acc))))))))

(визначити tri-count-symbolic
  (функція (rows acc)
    (за-умовою
      ((атом? rows) (structural-kind empty-list) acc)
      ((атом? rows) (structural-kind atom) acc)
      ((атом? rows) (structural-kind pair)
       (нехай ((state
               (tri-surface-presence
                 (решта (перше rows))
                 (як-є sym))))
         (за-умовою
           ((тотожне? state (як-є present)) (identity-relation same)
            (tri-count-symbolic (решта rows) (додати acc 1)))
           ((тотожне? state (як-є present)) (identity-relation distinct)
            (tri-count-symbolic (решта rows) acc))))))))

(визначити tri-count-common-stable
  (функція (rows acc)
    (за-умовою
      ((атом? rows) (structural-kind empty-list) acc)
      ((атом? rows) (structural-kind atom) acc)
      ((атом? rows) (structural-kind pair)
       (нехай ((public (tri-public-kind (перше rows))))
         (за-умовою
           ((тотожне? public (як-є public)) (identity-relation distinct)
            (tri-count-common-stable (решта rows) acc))
           ((тотожне? public (як-є public)) (identity-relation same)
            (нехай ((stable (tri-stable-kind (перше rows))))
              (за-умовою
                ((тотожне? stable (як-є all-stable)) (identity-relation same)
                 (tri-count-common-stable (решта rows) (додати acc 1)))
                ((тотожне? stable (як-є all-stable)) (identity-relation distinct)
                 (tri-count-common-stable (решта rows) acc)))))))))))

(визначити tri-release-state
  (функція (rows)
    (за-умовою
      ((атом? rows) (structural-kind empty-list) (як-є confirmed))
      ((атом? rows) (structural-kind atom) (як-є open))
      ((атом? rows) (structural-kind pair)
       (нехай ((public (tri-public-kind (перше rows))))
         (за-умовою
           ((тотожне? public (як-є public)) (identity-relation distinct)
            (tri-release-state (решта rows)))
           ((тотожне? public (як-є public)) (identity-relation same)
            (нехай ((stable (tri-stable-kind (перше rows))))
              (за-умовою
                ((тотожне? stable (як-є all-stable)) (identity-relation same)
                 (tri-release-state (решта rows)))
                ((тотожне? stable (як-є all-stable)) (identity-relation distinct)
                 (як-є open)))))))))))

(визначити tri-mode
  (функція (argv)
    (за-умовою
      ((атом? argv) (structural-kind empty-list) (як-є report))
      ((атом? argv) (structural-kind atom)
       (tri-fail (як-є malformed-argv) argv))
      ((атом? argv) (structural-kind pair)
       (нехай ((rest (решта argv)))
         (за-умовою
           ((атом? rest) (structural-kind empty-list)
            (за-умовою
              ((однакові? (перше argv) "--require-complete")
               (structural-relation same)
               (як-є require-complete))
              ((однакові? (перше argv) "--require-complete")
               (structural-relation distinct)
               (tri-fail (як-є unknown-argument) (перше argv)))))
           ((атом? rest) (structural-kind atom)
            (tri-fail (як-є malformed-argv) argv))
           ((атом? rest) (structural-kind pair)
            (tri-fail (як-є too-many-arguments) argv))))))))

(визначити tri-registry-form
  (перше
    (читати-всі
      (читати-файл "lib/surface/semantic-registry.lisp"))))

(визначити tri-rows
  (за-умовою
    ((атом? tri-registry-form) (structural-kind empty-list)
     (tri-fail (як-є malformed-registry-root) tri-registry-form))
    ((атом? tri-registry-form) (structural-kind atom)
     (tri-fail (як-є malformed-registry-root) tri-registry-form))
    ((атом? tri-registry-form) (structural-kind pair)
     (за-умовою
       ((тотожне? (перше tri-registry-form) (як-є sr/1))
        (identity-relation same)
        (решта tri-registry-form))
       ((тотожне? (перше tri-registry-form) (як-є sr/1))
        (identity-relation distinct)
        (tri-fail
          (як-є malformed-registry-root)
          (перше tri-registry-form)))))))

(визначити tri-validation
  (tri-validate-rows tri-rows (як-є ())))

(визначити tri-public-count
  (tri-count-public tri-rows 0))

(визначити tri-symbolic-count
  (tri-count-symbolic tri-rows 0))

(визначити tri-common-stable-count
  (tri-count-common-stable tri-rows 0))

(визначити tri-release
  (tri-release-state tri-rows))

(визначити tri-report
  (список
    (як-є trilingual-surface-report)
    (список (як-є entries) (довжина tri-rows))
    (список (як-є public-semantic-identities) tri-public-count)
    (список (як-є shared-symbolic-identities) tri-symbolic-count)
    (список
      (як-є uk)
      (список (як-є stable)
            (tri-count-status tri-rows (як-є uk) (як-є stable) 0))
      (список (як-є candidate)
            (tri-count-status tri-rows (як-є uk) (як-є candidate) 0))
      (список (як-є missing)
            (tri-count-status tri-rows (як-є uk) (як-є missing) 0))
      (список (як-є compatibility-only)
            (tri-count-status
              tri-rows
              (як-є uk)
              (як-є compatibility-only)
              0)))
    (список
      (як-є en)
      (список (як-є stable)
            (tri-count-status tri-rows (як-є en) (як-є stable) 0))
      (список (як-є candidate)
            (tri-count-status tri-rows (як-є en) (як-є candidate) 0))
      (список (як-є missing)
            (tri-count-status tri-rows (як-є en) (як-є missing) 0))
      (список (як-є compatibility-only)
            (tri-count-status
              tri-rows
              (як-є en)
              (як-є compatibility-only)
              0)))
    (список
      (як-є sa)
      (список (як-є stable)
            (tri-count-status tri-rows (як-є sa) (як-є stable) 0))
      (список (як-є candidate)
            (tri-count-status tri-rows (як-є sa) (як-є candidate) 0))
      (список (як-є missing)
            (tri-count-status tri-rows (як-є sa) (як-є missing) 0))
      (список (як-є compatibility-only)
            (tri-count-status
              tri-rows
              (як-є sa)
              (як-є compatibility-only)
              0)))
    (список
      (як-є trilingual-stable-identities)
      tri-common-stable-count
      tri-public-count)
    (список (як-є release-parity) tri-release)))

(визначити tri-shown
  (друкувати tri-report))

(визначити tri-selected-mode
  (tri-mode *argv*))

(за-умовою
  ((тотожне? tri-selected-mode (як-є require-complete))
   (identity-relation same)
   (за-умовою
     ((тотожне? tri-release (як-є confirmed))
      (identity-relation same)
      tri-report)
     ((тотожне? tri-release (як-є confirmed))
      (identity-relation distinct)
      (tri-fail (як-є release-parity-open) tri-report))))
  ((тотожне? tri-selected-mode (як-є require-complete))
   (identity-relation distinct)
   tri-report))

; opt-in повна укр-поверхня: exact identity = lib/domains/d*.lisp; DEFINE-аліас, без нової диспетчеризації.
(визначити читати-всі read-all)
(визначити спеціальна-змінна special)
