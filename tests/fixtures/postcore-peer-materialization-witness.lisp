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

(00001001 postcore-authority-form
  (00000101 (01001011 (10100110 "lib/surface/semantic-registry.lisp"))))

(00001001 postcore-authority-rows postcore-authority-form)

(00001001 postcore-member-status
  (00001000 (needle items)
    (00000111
      ((00000010 items) ()
       (00000001 absent))
      ((00000010 items) (0)
       (00000111
         ((00000011 needle (00000101 items)) (1)
          (00000001 present))
         ((00000011 needle (00000101 items)) (0)
          (postcore-member-status needle (00000110 items))))))))

(00001001 postcore-find-authority-row
  (00001000 (semantic-id rows)
    (00000111
      ((00000010 rows) ()
       (00000001 ()))
      ((00000010 rows) (0)
       (10011100 ((row (00000101 rows)))
         (00000111
           ((00011100 semantic-id (00000101 row)) 1
            row)
           ((00011100 semantic-id (00000101 row)) 0
            (postcore-find-authority-row semantic-id (00000110 rows)))))))))

(00001001 postcore-surfaces-with-status-onto
  (00001000 (status surfaces acc)
    (00000111
      ((00000010 surfaces) ()
       (00101010 acc))
      ((00000010 surfaces) (0)
       (10011101 ((surface (00000101 surfaces))
              (word (00101111 surface))
              (surface-status (00110000 surface)))
         (00000111
           ((00000011 surface-status status) (1)
            (00000111
              ((00000011 word (00000001 —)) (1)
               (postcore-surfaces-with-status-onto
                 status
                 (00000110 surfaces)
                 acc))
              ((00000011 word (00000001 —)) (0)
               (00000111
                 ((00000011 (postcore-member-status word acc) (00000001 present))
                  (1)
                  (postcore-surfaces-with-status-onto
                    status
                    (00000110 surfaces)
                    acc))
                 ((00000011 (postcore-member-status word acc) (00000001 absent))
                  (1)
                  (postcore-surfaces-with-status-onto
                    status
                    (00000110 surfaces)
                    (00000100 word acc)))))))
           ((00000011 surface-status status) (0)
            (postcore-surfaces-with-status-onto status (00000110 surfaces) acc))))))))

(00001001 postcore-surfaces-with-status
  (00001000 (status registry-row)
    (00000111
      ((00000010 registry-row) ()
       (00000001 ()))
      ((00000010 registry-row) (0)
       (postcore-surfaces-with-status-onto status (00000110 registry-row) (00000001 ()))))))

(00001001 postcore-materialization-declarations-onto
  (00001000 (forms acc)
    (00000111
      ((00000010 forms) ()
       (00101010 acc))
      ((00000010 forms) (0)
       (10011100 ((form (00000101 forms)))
         (00000111
           ((00000010 form) (0)
            (00000111
              ((00000011 (00000101 form) (00000001 my-postcore-materialize-stable-peers))
               (1)
               (postcore-materialization-declarations-onto
                 (00000110 forms)
                 (00000100 (00100111 (00101111 form) (00110000 form)) acc)))
              ((00000011 (00000101 form) (00000001 my-postcore-materialize-stable-peers))
               (0)
               (postcore-materialization-declarations-onto
                 (00000110 forms)
                 acc))))
           ((00000010 form) (1)
            (postcore-materialization-declarations-onto (00000110 forms) acc))
           ((00000010 form) ()
            (postcore-materialization-declarations-onto (00000110 forms) acc))))))))

(00001001 postcore-materialization-declarations
  (00001000 (path)
    (postcore-materialization-declarations-onto
      (01001011 (10100110 path))
      (00000001 ()))))

(00001001 postcore-declarations
  (00101001
    (postcore-materialization-declarations "lib/time.lisp")
    (00101001
      (postcore-materialization-declarations "lib/process.lisp")
      (00101001
        (postcore-materialization-declarations "lib/tcp.lisp")
        (postcore-materialization-declarations "lib/fs.lisp")))))

(00001001 postcore-declarations-match-authority
  (00001000 (declarations)
    (00000111
      ((00000010 declarations) ()
       (00000001 registry-consistent))
      ((00000010 declarations) (0)
       (10011101 ((declaration (00000101 declarations))
              (semantic-id (00000101 declaration))
              (source (00101111 declaration))
              (row
                (postcore-find-authority-row
                  semantic-id
                  postcore-authority-rows))
              (stable-peers
                (postcore-surfaces-with-status (00000001 stable) row)))
         (00000111
           ((00000010 row) ()
            (00000001 registry-drift))
           ((00000010 row) (0)
            (00000111
              ((00000011 (postcore-member-status source stable-peers) (00000001 present))
               (1)
               (postcore-declarations-match-authority (00000110 declarations)))
              ((00000011 (postcore-member-status source stable-peers) (00000001 absent))
               (1)
               (00000001 registry-drift))))))))))

(00001001 postcore-expected-peer-groups-onto
  (00001000 (declarations acc)
    (00000111
      ((00000010 declarations) ()
       (00101010 acc))
      ((00000010 declarations) (0)
       (10011101 ((declaration (00000101 declarations))
              (semantic-id (00000101 declaration))
              (row
                (postcore-find-authority-row
                  semantic-id
                  postcore-authority-rows))
              (stable-peers
                (postcore-surfaces-with-status (00000001 stable) row)))
         (00000111
           ((00011011 (00101000 stable-peers) 1) 1
            (postcore-expected-peer-groups-onto
              (00000110 declarations)
              (00000100 (00000100 semantic-id stable-peers) acc)))
           ((00011011 (00101000 stable-peers) 1) 0
            (postcore-expected-peer-groups-onto
              (00000110 declarations)
              acc))))))))

(00001001 postcore-expected-peer-groups
  (postcore-expected-peer-groups-onto postcore-declarations (00000001 ())))

(00001001 postcore-find-group
  (00001000 (semantic-id groups)
    (00000111
      ((00000010 groups) ()
       (00000001 ()))
      ((00000010 groups) (0)
       (10011100 ((group (00000101 groups)))
         (00000111
           ((00011100 semantic-id (00000101 group)) 1
            group)
           ((00011100 semantic-id (00000101 group)) 0
            (postcore-find-group semantic-id (00000110 groups)))))))))

(00001001 postcore-peer-members-match
  (00001000 (expected actual)
    (00000111
      ((00000010 expected) ()
       (00000001 registry-consistent))
      ((00000010 expected) (0)
       (00000111
         ((00000011 (postcore-member-status (00000101 expected) actual) (00000001 present))
          (1)
          (postcore-peer-members-match (00000110 expected) actual))
         ((00000011 (postcore-member-status (00000101 expected) actual) (00000001 absent))
          (1)
          (00000001 registry-drift)))))))

(00001001 postcore-peer-sets-match
  (00001000 (expected actual)
    (00000111
      ((00011100 (00101000 expected) (00101000 actual)) 0
       (00000001 registry-drift))
      ((00011100 (00101000 expected) (00101000 actual)) 1
       (postcore-peer-members-match expected actual)))))

(00001001 postcore-projection-groups-match
  (00001000 (expected actual)
    (00000111
      ((00000010 expected) ()
       (00000001 registry-consistent))
      ((00000010 expected) (0)
       (10011101 ((expected-group (00000101 expected))
              (semantic-id (00000101 expected-group))
              (actual-group (postcore-find-group semantic-id actual)))
         (00000111
           ((00000010 actual-group) ()
            (00000001 registry-drift))
           ((00000010 actual-group) (0)
            (00000111
              ((00000011
                 (postcore-peer-sets-match
                   (00000110 expected-group)
                   (00000110 actual-group))
                 (00000001 registry-consistent))
               (1)
               (postcore-projection-groups-match (00000110 expected) actual))
              ((00000011
                 (postcore-peer-sets-match
                   (00000110 expected-group)
                   (00000110 actual-group))
                 (00000001 registry-drift))
               (1)
               (00000001 registry-drift))))))))))

(00001001 postcore-projection-matches-authority
  (00001000 (expected actual)
    (00000111
      ((00011100 (00101000 expected) (00101000 actual)) 0
       (00000001 registry-drift))
      ((00011100 (00101000 expected) (00101000 actual)) 1
       (postcore-projection-groups-match expected actual)))))

(00001001 postcore-surfaces-unbound
  (00001000 (surfaces)
    (00000111
      ((00000010 surfaces) ()
       (00000001 surfaces-unbound))
      ((00000010 surfaces) (0)
       (00000111
         ((00000011
            (my-postcore-binding-status (00000101 surfaces) (01001110))
            (00000001 absent))
          (1)
          (postcore-surfaces-unbound (00000110 surfaces)))
         ((00000011
            (my-postcore-binding-status (00000101 surfaces) (01001110))
            (00000001 present))
          (1)
          (00000001 surfaces-bound)))))))

(00001001 postcore-candidate-surfaces-unbound
  (00001000 (declarations)
    (00000111
      ((00000010 declarations) ()
       (00000001 candidates-unbound))
      ((00000010 declarations) (0)
       (10011101 ((semantic-id (00000101 (00000101 declarations)))
              (row
                (postcore-find-authority-row
                  semantic-id
                  postcore-authority-rows))
              (candidates
                (postcore-surfaces-with-status (00000001 candidate) row)))
         (00000111
           ((00000011
              (postcore-surfaces-unbound candidates)
              (00000001 surfaces-unbound))
            (1)
            (postcore-candidate-surfaces-unbound (00000110 declarations)))
           ((00000011
              (postcore-surfaces-unbound candidates)
              (00000001 surfaces-bound))
            (1)
            (00000001 candidates-bound))))))))

(00001001 postcore-registry-surface-count
  (00001000 (semantic-id-text entries)
    (00000111
      ((00000010 entries) ()
       0)
      ((00000010 entries) (0)
       (10011100 ((entry (00000101 entries)))
         (00000111
           ((00000011 (00101111 entry) semantic-id-text) (1)
            (00001100 1
               (postcore-registry-surface-count
                 semantic-id-text
                 (00000110 entries))))
           ((00000011 (00101111 entry) semantic-id-text) (0)
            (postcore-registry-surface-count
              semantic-id-text
              (00000110 entries)))))))))

(00001001 postcore-peers-match-id
  (00001000 (peers semantic-id-text)
    (00000111
      ((00000010 peers) ()
       (00000001 registry-consistent))
      ((00000010 peers) (0)
       (00000111
         ((00000011 (my-semantic-id-for-surface (00000101 peers)) semantic-id-text)
          (1)
          (postcore-peers-match-id (00000110 peers) semantic-id-text))
         ((00000011 (my-semantic-id-for-surface (00000101 peers)) semantic-id-text)
          (0)
          (00000001 registry-drift)))))))

(00001001 postcore-groups-match-generated-registry
  (00001000 (groups)
    (00000111
      ((00000010 groups) ()
       (00000001 registry-consistent))
      ((00000010 groups) (0)
       (10011101 ((group (00000101 groups))
              (semantic-id (00000101 group))
              (peers (00000110 group))
              (semantic-id-text (01000110 semantic-id))
              (projected-count
                (postcore-registry-surface-count
                  semantic-id-text
                  my-semantic-surface-registry)))
         (00000111
           ((00011100 projected-count (00101000 peers)) 1
            (00000111
              ((00000011 (postcore-peers-match-id peers semantic-id-text)
                   (00000001 registry-consistent))
               (1)
               (postcore-groups-match-generated-registry (00000110 groups)))
              ((00000011 (postcore-peers-match-id peers semantic-id-text)
                   (00000001 registry-drift))
               (1)
               (00000001 registry-drift))))
           ((00011100 projected-count (00101000 peers)) 0
            (00000001 registry-drift))))))))

(00001001 postcore-witness-failure
  (00001000 (case actual expected)
    (00100111
      (00000001 postcore-peer-materialization-witness)
      (00000001 (status fail))
      (00100111 (00000001 case) case)
      (00100111 (00000001 actual) actual)
      (00100111 (00000001 expected) expected))))

(00001001 postcore-check-rows
  (00001000 (rows)
    (00000111
      ((00000010 rows) ()
       (00000001 (postcore-peer-materialization-witness (status pass))))
      ((00000010 rows) (1)
       (postcore-witness-failure
         (00000001 malformed-row-tail)
         rows
         (00000001 ())))
      ((00000010 rows) (0)
       (10011100 ((row (00000101 rows)))
         (00000111
           ((00100010 (00101111 row) (00110000 row)) (1)
            (postcore-check-rows (00000110 rows)))
           ((00100010 (00101111 row) (00110000 row)) (0)
            (postcore-witness-failure
              (00000101 row)
              (00101111 row)
              (00110000 row)))))))))

(00001001 postcore-phase-one
  (postcore-check-rows
    (00100111
      ; Every numeric materialization declaration in the post-core libraries
      ; must name a stable source binding from the single semantic authority.
      (00100111
        (00000001 declaration-source-authority)
        (postcore-declarations-match-authority postcore-declarations)
        (00000001 registry-consistent))

      ; The bootstrap cache must be exactly the set of declared post-core IDs
      ; that currently have more than one unique stable spelling. IDs with only
      ; their source spelling need no cache row yet; promoting a candidate to
      ; stable therefore makes this witness RED until the cache is refreshed.
      (00100111
        (00000001 authority-derived-complete-projection)
        (postcore-projection-matches-authority
          postcore-expected-peer-groups
          my-postcore-stable-peer-projection)
        (00000001 registry-consistent))

      ; Declaring a post-core identity must never admit candidate spellings.
      (00100111
        (00000001 candidates-remain-unbound)
        (postcore-candidate-surfaces-unbound postcore-declarations)
        (00000001 candidates-unbound))

      ; The hand-executed runtime projection must exactly match the generated
      ; admitted registry projection for every currently exercised time ID.
      (00100111
        (00000001 generated-registry-parity)
        (postcore-groups-match-generated-registry
          my-postcore-stable-peer-projection)
        (00000001 registry-consistent))

      ; Both stable spellings route to the same opaque numeric identity.
      (00100111
        (00000001 semantic-id-en)
        (my-semantic-id-for-surface (00000001 utc-from-unix))
        "1080")
      (00100111
        (00000001 semantic-id-uk)
        (my-semantic-id-for-surface (00000001 всч-із-юнікс))
        "1080")

      ; The full UKR spelling is still candidate. It must be absent from both
      ; the admitted registry projection and the live environment.
      (00100111
        (00000001 candidate-not-admitted)
        (00000010
          (my-semantic-id-for-surface
            (00000001 всесвітній-координований-час-із-часу-юнікс)))
        (00000001 ()))
      (00100111
        (00000001 candidate-not-bound)
        (my-postcore-binding-status
          (00000001 всесвітній-координований-час-із-часу-юнікс)
          (01001110))
        (00000001 absent))

      ; Stable EN/UK peers begin as exactly the same closure and execute with
      ; the same deterministic result.
      (00100111
        (00000001 initial-peer-identity)
        (00000011 utc-from-unix всч-із-юнікс)
        (00000001 (1)))
      (00100111
        (00000001 invocation-parity)
        (00100010 (01011111 0 0) (01011111 0 0))
        (00000001 (1)))

      ; Ordinary lexical shadowing is independent: rebinding one spelling does
      ; not mutate or retarget the other spelling.
      (00100111
        (00000001 lexical-shadowing-independent)
        (10011100 ((всч-із-юнікс
                (00001000 (seconds nanosecond) (00000001 shadowed))))
          (00000011 utc-from-unix всч-із-юнікс))
        (00000001 (0))))))

; Stronger idempotence law: install an explicit existing peer binding, invoke
; materialization again at top level, and prove the macro does NOT overwrite it.
; This mutation is local to this one-shot witness process.
(00001001 postcore-existing-peer
  (00001000 (seconds nanosecond) (00000001 preserved-peer)))

(00001001 всч-із-юнікс postcore-existing-peer)
(my-postcore-materialize-stable-peers 1080 utc-from-unix)

(00001001 postcore-phase-two
  (postcore-check-rows
    (00100111
      (00100111
        (00000001 phase-one)
        postcore-phase-one
        (00000001 (postcore-peer-materialization-witness (status pass))))
      (00100111
        (00000001 rematerialization-preserves-existing-binding)
        (00000011 всч-із-юнікс postcore-existing-peer)
        (00000001 (1)))
      (00100111
        (00000001 rematerialization-does-not-retarget-source)
        (00000011 всч-із-юнікс utc-from-unix)
        (00000001 (0)))
      (00100111
        (00000001 preserved-binding-invocation)
        (всч-із-юнікс 0 0)
        (00000001 preserved-peer)))))

postcore-phase-two
