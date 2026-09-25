; #469 — executable post-core peer materialization witness.
;
; The CLI loads core + time/process/fs before this file, but it does NOT load
; lib/surface/uk.lisp. Therefore the UK peer below exists only if the post-core
; library materialized it through the registry-driven mechanism.
;
; This witness also loads the generated registry projection as DATA evidence:
; the numeric semantic ID remains authority, candidates remain unadmitted, and
; the runtime peer projection for the exercised post-core range must neither
; invent nor omit an admitted spelling.

(load "lib/generated/meta-semantic-registry.lisp")


; Authority-hardening follow-up: the runtime table in core is a bootstrap cache,
; not a second surface authority. Derive the expected cache directly from the
; real semantic registry plus the numeric-ID materialization declarations in
; post-core libraries. This makes omissions, invented peers and stale candidate
; promotion fail closed without giving Rust or a second hand-written table any
; authority.

(def postcore-authority-form
  (car (read-all (read-file "lib/surface/semantic-registry.lisp"))))

(def postcore-authority-rows postcore-authority-form)

(def postcore-member-status
  (lambda (needle items)
    (cond
      ((atom? items) (structural-kind empty-list)
       (quote absent))
      ((atom? items) (structural-kind pair)
       (cond
         ((eq? needle (car items)) (identity-relation same)
          (quote present))
         ((eq? needle (car items)) (identity-relation distinct)
          (postcore-member-status needle (cdr items))))))))

(def postcore-find-authority-row
  (lambda (semantic-id rows)
    (cond
      ((atom? rows) (structural-kind empty-list)
       (quote ()))
      ((atom? rows) (structural-kind pair)
       (let ((row (car rows)))
         (cond
           ((= semantic-id (car row)) 1
            row)
           ((= semantic-id (car row)) 0
            (postcore-find-authority-row semantic-id (cdr rows)))))))))

(def postcore-surfaces-with-status-onto
  (lambda (status surfaces acc)
    (cond
      ((atom? surfaces) (structural-kind empty-list)
       (reverse acc))
      ((atom? surfaces) (structural-kind pair)
       (let* ((surface (car surfaces))
              (word (second surface))
              (surface-status (third surface)))
         (cond
           ((eq? surface-status status) (identity-relation same)
            (cond
              ((eq? word (quote —)) (identity-relation same)
               (postcore-surfaces-with-status-onto
                 status
                 (cdr surfaces)
                 acc))
              ((eq? word (quote —)) (identity-relation distinct)
               (cond
                 ((eq? (postcore-member-status word acc) (quote present))
                  (identity-relation same)
                  (postcore-surfaces-with-status-onto
                    status
                    (cdr surfaces)
                    acc))
                 ((eq? (postcore-member-status word acc) (quote absent))
                  (identity-relation same)
                  (postcore-surfaces-with-status-onto
                    status
                    (cdr surfaces)
                    (cons word acc)))))))
           ((eq? surface-status status) (identity-relation distinct)
            (postcore-surfaces-with-status-onto status (cdr surfaces) acc))))))))

(def postcore-surfaces-with-status
  (lambda (status registry-row)
    (cond
      ((atom? registry-row) (structural-kind empty-list)
       (quote ()))
      ((atom? registry-row) (structural-kind pair)
       (postcore-surfaces-with-status-onto status (cdr registry-row) (quote ()))))))

(def postcore-materialization-declarations-onto
  (lambda (forms acc)
    (cond
      ((atom? forms) (structural-kind empty-list)
       (reverse acc))
      ((atom? forms) (structural-kind pair)
       (let ((form (car forms)))
         (cond
           ((atom? form) (structural-kind pair)
            (cond
              ((eq? (car form) (quote my-postcore-materialize-stable-peers))
               (identity-relation same)
               (postcore-materialization-declarations-onto
                 (cdr forms)
                 (cons (list (second form) (third form)) acc)))
              ((eq? (car form) (quote my-postcore-materialize-stable-peers))
               (identity-relation distinct)
               (postcore-materialization-declarations-onto
                 (cdr forms)
                 acc))))
           ((atom? form) (structural-kind atom)
            (postcore-materialization-declarations-onto (cdr forms) acc))
           ((atom? form) (structural-kind empty-list)
            (postcore-materialization-declarations-onto (cdr forms) acc))))))))

(def postcore-materialization-declarations
  (lambda (path)
    (postcore-materialization-declarations-onto
      (read-all (read-file path))
      (quote ()))))

(def postcore-declarations
  (append
    (postcore-materialization-declarations "lib/time.lisp")
    (append
      (postcore-materialization-declarations "lib/process.lisp")
      (append
        (postcore-materialization-declarations "lib/tcp.lisp")
        (postcore-materialization-declarations "lib/fs.lisp")))))

(def postcore-declarations-match-authority
  (lambda (declarations)
    (cond
      ((atom? declarations) (structural-kind empty-list)
       (quote registry-consistent))
      ((atom? declarations) (structural-kind pair)
       (let* ((declaration (car declarations))
              (semantic-id (car declaration))
              (source (second declaration))
              (row
                (postcore-find-authority-row
                  semantic-id
                  postcore-authority-rows))
              (stable-peers
                (postcore-surfaces-with-status (quote stable) row)))
         (cond
           ((atom? row) (structural-kind empty-list)
            (quote registry-drift))
           ((atom? row) (structural-kind pair)
            (cond
              ((eq? (postcore-member-status source stable-peers) (quote present))
               (identity-relation same)
               (postcore-declarations-match-authority (cdr declarations)))
              ((eq? (postcore-member-status source stable-peers) (quote absent))
               (identity-relation same)
               (quote registry-drift))))))))))

(def postcore-expected-peer-groups-onto
  (lambda (declarations acc)
    (cond
      ((atom? declarations) (structural-kind empty-list)
       (reverse acc))
      ((atom? declarations) (structural-kind pair)
       (let* ((declaration (car declarations))
              (semantic-id (car declaration))
              (row
                (postcore-find-authority-row
                  semantic-id
                  postcore-authority-rows))
              (stable-peers
                (postcore-surfaces-with-status (quote stable) row)))
         (cond
           ((> (length stable-peers) 1) 1
            (postcore-expected-peer-groups-onto
              (cdr declarations)
              (cons (cons semantic-id stable-peers) acc)))
           ((> (length stable-peers) 1) 0
            (postcore-expected-peer-groups-onto
              (cdr declarations)
              acc))))))))

(def postcore-expected-peer-groups
  (postcore-expected-peer-groups-onto postcore-declarations (quote ())))

(def postcore-find-group
  (lambda (semantic-id groups)
    (cond
      ((atom? groups) (structural-kind empty-list)
       (quote ()))
      ((atom? groups) (structural-kind pair)
       (let ((group (car groups)))
         (cond
           ((= semantic-id (car group)) 1
            group)
           ((= semantic-id (car group)) 0
            (postcore-find-group semantic-id (cdr groups)))))))))

(def postcore-peer-members-match
  (lambda (expected actual)
    (cond
      ((atom? expected) (structural-kind empty-list)
       (quote registry-consistent))
      ((atom? expected) (structural-kind pair)
       (cond
         ((eq? (postcore-member-status (car expected) actual) (quote present))
          (identity-relation same)
          (postcore-peer-members-match (cdr expected) actual))
         ((eq? (postcore-member-status (car expected) actual) (quote absent))
          (identity-relation same)
          (quote registry-drift)))))))

(def postcore-peer-sets-match
  (lambda (expected actual)
    (cond
      ((= (length expected) (length actual)) 0
       (quote registry-drift))
      ((= (length expected) (length actual)) 1
       (postcore-peer-members-match expected actual)))))

(def postcore-projection-groups-match
  (lambda (expected actual)
    (cond
      ((atom? expected) (structural-kind empty-list)
       (quote registry-consistent))
      ((atom? expected) (structural-kind pair)
       (let* ((expected-group (car expected))
              (semantic-id (car expected-group))
              (actual-group (postcore-find-group semantic-id actual)))
         (cond
           ((atom? actual-group) (structural-kind empty-list)
            (quote registry-drift))
           ((atom? actual-group) (structural-kind pair)
            (cond
              ((eq?
                 (postcore-peer-sets-match
                   (cdr expected-group)
                   (cdr actual-group))
                 (quote registry-consistent))
               (identity-relation same)
               (postcore-projection-groups-match (cdr expected) actual))
              ((eq?
                 (postcore-peer-sets-match
                   (cdr expected-group)
                   (cdr actual-group))
                 (quote registry-drift))
               (identity-relation same)
               (quote registry-drift))))))))))

(def postcore-projection-matches-authority
  (lambda (expected actual)
    (cond
      ((= (length expected) (length actual)) 0
       (quote registry-drift))
      ((= (length expected) (length actual)) 1
       (postcore-projection-groups-match expected actual)))))

(def postcore-surfaces-unbound
  (lambda (surfaces)
    (cond
      ((atom? surfaces) (structural-kind empty-list)
       (quote surfaces-unbound))
      ((atom? surfaces) (structural-kind pair)
       (cond
         ((eq?
            (my-postcore-binding-status (car surfaces) (env))
            (quote absent))
          (identity-relation same)
          (postcore-surfaces-unbound (cdr surfaces)))
         ((eq?
            (my-postcore-binding-status (car surfaces) (env))
            (quote present))
          (identity-relation same)
          (quote surfaces-bound)))))))

(def postcore-candidate-surfaces-unbound
  (lambda (declarations)
    (cond
      ((atom? declarations) (structural-kind empty-list)
       (quote candidates-unbound))
      ((atom? declarations) (structural-kind pair)
       (let* ((semantic-id (car (car declarations)))
              (row
                (postcore-find-authority-row
                  semantic-id
                  postcore-authority-rows))
              (candidates
                (postcore-surfaces-with-status (quote candidate) row)))
         (cond
           ((eq?
              (postcore-surfaces-unbound candidates)
              (quote surfaces-unbound))
            (identity-relation same)
            (postcore-candidate-surfaces-unbound (cdr declarations)))
           ((eq?
              (postcore-surfaces-unbound candidates)
              (quote surfaces-bound))
            (identity-relation same)
            (quote candidates-bound))))))))

(def postcore-registry-surface-count
  (lambda (semantic-id-text entries)
    (cond
      ((atom? entries) (structural-kind empty-list)
       0)
      ((atom? entries) (structural-kind pair)
       (let ((entry (car entries)))
         (cond
           ((eq? (second entry) semantic-id-text) (identity-relation same)
            (+ 1
               (postcore-registry-surface-count
                 semantic-id-text
                 (cdr entries))))
           ((eq? (second entry) semantic-id-text) (identity-relation distinct)
            (postcore-registry-surface-count
              semantic-id-text
              (cdr entries)))))))))

(def postcore-peers-match-id
  (lambda (peers semantic-id-text)
    (cond
      ((atom? peers) (structural-kind empty-list)
       (quote registry-consistent))
      ((atom? peers) (structural-kind pair)
       (cond
         ((eq? (my-semantic-id-for-surface (car peers)) semantic-id-text)
          (identity-relation same)
          (postcore-peers-match-id (cdr peers) semantic-id-text))
         ((eq? (my-semantic-id-for-surface (car peers)) semantic-id-text)
          (identity-relation distinct)
          (quote registry-drift)))))))

(def postcore-groups-match-generated-registry
  (lambda (groups)
    (cond
      ((atom? groups) (structural-kind empty-list)
       (quote registry-consistent))
      ((atom? groups) (structural-kind pair)
       (let* ((group (car groups))
              (semantic-id (car group))
              (peers (cdr group))
              (semantic-id-text (number->string semantic-id))
              (projected-count
                (postcore-registry-surface-count
                  semantic-id-text
                  my-semantic-surface-registry)))
         (cond
           ((= projected-count (length peers)) 1
            (cond
              ((eq? (postcore-peers-match-id peers semantic-id-text)
                   (quote registry-consistent))
               (identity-relation same)
               (postcore-groups-match-generated-registry (cdr groups)))
              ((eq? (postcore-peers-match-id peers semantic-id-text)
                   (quote registry-drift))
               (identity-relation same)
               (quote registry-drift))))
           ((= projected-count (length peers)) 0
            (quote registry-drift))))))))

(def postcore-witness-failure
  (lambda (case actual expected)
    (list
      (quote postcore-peer-materialization-witness)
      (quote (status fail))
      (list (quote case) case)
      (list (quote actual) actual)
      (list (quote expected) expected))))

(def postcore-check-rows
  (lambda (rows)
    (cond
      ((atom? rows) (structural-kind empty-list)
       (quote (postcore-peer-materialization-witness (status pass))))
      ((atom? rows) (structural-kind atom)
       (postcore-witness-failure
         (quote malformed-row-tail)
         rows
         (quote ())))
      ((atom? rows) (structural-kind pair)
       (let ((row (car rows)))
         (cond
           ((equal? (second row) (third row)) (structural-relation same)
            (postcore-check-rows (cdr rows)))
           ((equal? (second row) (third row)) (structural-relation distinct)
            (postcore-witness-failure
              (car row)
              (second row)
              (third row)))))))))

(def postcore-phase-one
  (postcore-check-rows
    (list
      ; Every numeric materialization declaration in the post-core libraries
      ; must name a stable source binding from the single semantic authority.
      (list
        (quote declaration-source-authority)
        (postcore-declarations-match-authority postcore-declarations)
        (quote registry-consistent))

      ; The bootstrap cache must be exactly the set of declared post-core IDs
      ; that currently have more than one unique stable spelling. IDs with only
      ; their source spelling need no cache row yet; promoting a candidate to
      ; stable therefore makes this witness RED until the cache is refreshed.
      (list
        (quote authority-derived-complete-projection)
        (postcore-projection-matches-authority
          postcore-expected-peer-groups
          my-postcore-stable-peer-projection)
        (quote registry-consistent))

      ; Declaring a post-core identity must never admit candidate spellings.
      (list
        (quote candidates-remain-unbound)
        (postcore-candidate-surfaces-unbound postcore-declarations)
        (quote candidates-unbound))

      ; The hand-executed runtime projection must exactly match the generated
      ; admitted registry projection for every currently exercised time ID.
      (list
        (quote generated-registry-parity)
        (postcore-groups-match-generated-registry
          my-postcore-stable-peer-projection)
        (quote registry-consistent))

      ; Both stable spellings route to the same opaque numeric identity.
      (list
        (quote semantic-id-en)
        (my-semantic-id-for-surface (quote utc-from-unix))
        "1080")
      (list
        (quote semantic-id-uk)
        (my-semantic-id-for-surface (quote всч-із-юнікс))
        "1080")

      ; The full UKR spelling is still candidate. It must be absent from both
      ; the admitted registry projection and the live environment.
      (list
        (quote candidate-not-admitted)
        (atom?
          (my-semantic-id-for-surface
            (quote всесвітній-координований-час-із-часу-юнікс)))
        (quote (structural-kind empty-list)))
      (list
        (quote candidate-not-bound)
        (my-postcore-binding-status
          (quote всесвітній-координований-час-із-часу-юнікс)
          (env))
        (quote absent))

      ; Stable EN/UK peers begin as exactly the same closure and execute with
      ; the same deterministic result.
      (list
        (quote initial-peer-identity)
        (eq? utc-from-unix всч-із-юнікс)
        (quote (identity-relation same)))
      (list
        (quote invocation-parity)
        (equal? (utc-from-unix 0 0) (всч-із-юнікс 0 0))
        (quote (structural-relation same)))

      ; Ordinary lexical shadowing is independent: rebinding one spelling does
      ; not mutate or retarget the other spelling.
      (list
        (quote lexical-shadowing-independent)
        (let ((всч-із-юнікс
                (lambda (seconds nanosecond) (quote shadowed))))
          (eq? utc-from-unix всч-із-юнікс))
        (quote (identity-relation distinct))))))

; Stronger idempotence law: install an explicit existing peer binding, invoke
; materialization again at top level, and prove the macro does NOT overwrite it.
; This mutation is local to this one-shot witness process.
(def postcore-existing-peer
  (lambda (seconds nanosecond) (quote preserved-peer)))

(def всч-із-юнікс postcore-existing-peer)
(my-postcore-materialize-stable-peers 1080 utc-from-unix)

(def postcore-phase-two
  (postcore-check-rows
    (list
      (list
        (quote phase-one)
        postcore-phase-one
        (quote (postcore-peer-materialization-witness (status pass))))
      (list
        (quote rematerialization-preserves-existing-binding)
        (eq? всч-із-юнікс postcore-existing-peer)
        (quote (identity-relation same)))
      (list
        (quote rematerialization-does-not-retarget-source)
        (eq? всч-із-юнікс utc-from-unix)
        (quote (identity-relation distinct)))
      (list
        (quote preserved-binding-invocation)
        (всч-із-юнікс 0 0)
        (quote preserved-peer)))))

postcore-phase-two
