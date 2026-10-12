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

(0011 postcore-authority-form
  (100 (110101001 (110110111 "lib/surface/semantic-registry.lisp"))))

(0011 postcore-authority-rows postcore-authority-form)

(0011 postcore-member-status
  (0010 (needle items)
    (110
      ((010 items) ()
       (001 absent))
      ((010 items) (0)
       (110
         ((101 needle (100 items)) (1)
          (001 present))
         ((101 needle (100 items)) (0)
          (postcore-member-status needle (011 items))))))))

(0011 postcore-find-authority-row
  (0010 (semantic-id rows)
    (110
      ((010 rows) ()
       (001 ()))
      ((010 rows) (0)
       (001000 ((row (100 rows)))
         (110
           ((11110111 semantic-id (100 row)) 1
            row)
           ((11110111 semantic-id (100 row)) 0
            (postcore-find-authority-row semantic-id (011 rows)))))))))

(0011 postcore-surfaces-with-status-onto
  (0010 (status surfaces acc)
    (110
      ((010 surfaces) ()
       (10100 acc))
      ((010 surfaces) (0)
       (001001 ((surface (100 surfaces))
              (word (1001 surface))
              (surface-status (10011 surface)))
         (110
           ((101 surface-status status) (1)
            (110
              ((101 word (001 —)) (1)
               (postcore-surfaces-with-status-onto
                 status
                 (011 surfaces)
                 acc))
              ((101 word (001 —)) (0)
               (110
                 ((101 (postcore-member-status word acc) (001 present))
                  (1)
                  (postcore-surfaces-with-status-onto
                    status
                    (011 surfaces)
                    acc))
                 ((101 (postcore-member-status word acc) (001 absent))
                  (1)
                  (postcore-surfaces-with-status-onto
                    status
                    (011 surfaces)
                    (111 word acc)))))))
           ((101 surface-status status) (0)
            (postcore-surfaces-with-status-onto status (011 surfaces) acc))))))))

(0011 postcore-surfaces-with-status
  (0010 (status registry-row)
    (110
      ((010 registry-row) ()
       (001 ()))
      ((010 registry-row) (0)
       (postcore-surfaces-with-status-onto status (011 registry-row) (001 ()))))))

(0011 postcore-materialization-declarations-onto
  (0010 (forms acc)
    (110
      ((010 forms) ()
       (10100 acc))
      ((010 forms) (0)
       (001000 ((form (100 forms)))
         (110
           ((010 form) (0)
            (110
              ((101 (100 form) (001 my-postcore-materialize-stable-peers))
               (1)
               (postcore-materialization-declarations-onto
                 (011 forms)
                 (111 (1110 (1001 form) (10011 form)) acc)))
              ((101 (100 form) (001 my-postcore-materialize-stable-peers))
               (0)
               (postcore-materialization-declarations-onto
                 (011 forms)
                 acc))))
           ((010 form) (1)
            (postcore-materialization-declarations-onto (011 forms) acc))
           ((010 form) ()
            (postcore-materialization-declarations-onto (011 forms) acc))))))))

(0011 postcore-materialization-declarations
  (0010 (path)
    (postcore-materialization-declarations-onto
      (110101001 (110110111 path))
      (001 ()))))

(0011 postcore-declarations
  (1111
    (postcore-materialization-declarations "lib/time.lisp")
    (1111
      (postcore-materialization-declarations "lib/process.lisp")
      (1111
        (postcore-materialization-declarations "lib/tcp.lisp")
        (postcore-materialization-declarations "lib/fs.lisp")))))

(0011 postcore-declarations-match-authority
  (0010 (declarations)
    (110
      ((010 declarations) ()
       (001 registry-consistent))
      ((010 declarations) (0)
       (001001 ((declaration (100 declarations))
              (semantic-id (100 declaration))
              (source (1001 declaration))
              (row
                (postcore-find-authority-row
                  semantic-id
                  postcore-authority-rows))
              (stable-peers
                (postcore-surfaces-with-status (001 stable) row)))
         (110
           ((010 row) ()
            (001 registry-drift))
           ((010 row) (0)
            (110
              ((101 (postcore-member-status source stable-peers) (001 present))
               (1)
               (postcore-declarations-match-authority (011 declarations)))
              ((101 (postcore-member-status source stable-peers) (001 absent))
               (1)
               (001 registry-drift))))))))))

(0011 postcore-expected-peer-groups-onto
  (0010 (declarations acc)
    (110
      ((010 declarations) ()
       (10100 acc))
      ((010 declarations) (0)
       (001001 ((declaration (100 declarations))
              (semantic-id (100 declaration))
              (row
                (postcore-find-authority-row
                  semantic-id
                  postcore-authority-rows))
              (stable-peers
                (postcore-surfaces-with-status (001 stable) row)))
         (110
           ((11011 (000000 stable-peers) 1) 1
            (postcore-expected-peer-groups-onto
              (011 declarations)
              (111 (111 semantic-id stable-peers) acc)))
           ((11011 (000000 stable-peers) 1) 0
            (postcore-expected-peer-groups-onto
              (011 declarations)
              acc))))))))

(0011 postcore-expected-peer-groups
  (postcore-expected-peer-groups-onto postcore-declarations (001 ())))

(0011 postcore-find-group
  (0010 (semantic-id groups)
    (110
      ((010 groups) ()
       (001 ()))
      ((010 groups) (0)
       (001000 ((group (100 groups)))
         (110
           ((11110111 semantic-id (100 group)) 1
            group)
           ((11110111 semantic-id (100 group)) 0
            (postcore-find-group semantic-id (011 groups)))))))))

(0011 postcore-peer-members-match
  (0010 (expected actual)
    (110
      ((010 expected) ()
       (001 registry-consistent))
      ((010 expected) (0)
       (110
         ((101 (postcore-member-status (100 expected) actual) (001 present))
          (1)
          (postcore-peer-members-match (011 expected) actual))
         ((101 (postcore-member-status (100 expected) actual) (001 absent))
          (1)
          (001 registry-drift)))))))

(0011 postcore-peer-sets-match
  (0010 (expected actual)
    (110
      ((11110111 (000000 expected) (000000 actual)) 0
       (001 registry-drift))
      ((11110111 (000000 expected) (000000 actual)) 1
       (postcore-peer-members-match expected actual)))))

(0011 postcore-projection-groups-match
  (0010 (expected actual)
    (110
      ((010 expected) ()
       (001 registry-consistent))
      ((010 expected) (0)
       (001001 ((expected-group (100 expected))
              (semantic-id (100 expected-group))
              (actual-group (postcore-find-group semantic-id actual)))
         (110
           ((010 actual-group) ()
            (001 registry-drift))
           ((010 actual-group) (0)
            (110
              ((101
                 (postcore-peer-sets-match
                   (011 expected-group)
                   (011 actual-group))
                 (001 registry-consistent))
               (1)
               (postcore-projection-groups-match (011 expected) actual))
              ((101
                 (postcore-peer-sets-match
                   (011 expected-group)
                   (011 actual-group))
                 (001 registry-drift))
               (1)
               (001 registry-drift))))))))))

(0011 postcore-projection-matches-authority
  (0010 (expected actual)
    (110
      ((11110111 (000000 expected) (000000 actual)) 0
       (001 registry-drift))
      ((11110111 (000000 expected) (000000 actual)) 1
       (postcore-projection-groups-match expected actual)))))

(0011 postcore-surfaces-unbound
  (0010 (surfaces)
    (110
      ((010 surfaces) ()
       (001 surfaces-unbound))
      ((010 surfaces) (0)
       (110
         ((101
            (my-postcore-binding-status (100 surfaces) (11100111))
            (001 absent))
          (1)
          (postcore-surfaces-unbound (011 surfaces)))
         ((101
            (my-postcore-binding-status (100 surfaces) (11100111))
            (001 present))
          (1)
          (001 surfaces-bound)))))))

(0011 postcore-candidate-surfaces-unbound
  (0010 (declarations)
    (110
      ((010 declarations) ()
       (001 candidates-unbound))
      ((010 declarations) (0)
       (001001 ((semantic-id (100 (100 declarations)))
              (row
                (postcore-find-authority-row
                  semantic-id
                  postcore-authority-rows))
              (candidates
                (postcore-surfaces-with-status (001 candidate) row)))
         (110
           ((101
              (postcore-surfaces-unbound candidates)
              (001 surfaces-unbound))
            (1)
            (postcore-candidate-surfaces-unbound (011 declarations)))
           ((101
              (postcore-surfaces-unbound candidates)
              (001 surfaces-bound))
            (1)
            (001 candidates-bound))))))))

(0011 postcore-registry-surface-count
  (0010 (semantic-id-text entries)
    (110
      ((010 entries) ()
       0)
      ((010 entries) (0)
       (001000 ((entry (100 entries)))
         (110
           ((101 (1001 entry) semantic-id-text) (1)
            (01010 1
               (postcore-registry-surface-count
                 semantic-id-text
                 (011 entries))))
           ((101 (1001 entry) semantic-id-text) (0)
            (postcore-registry-surface-count
              semantic-id-text
              (011 entries)))))))))

(0011 postcore-peers-match-id
  (0010 (peers semantic-id-text)
    (110
      ((010 peers) ()
       (001 registry-consistent))
      ((010 peers) (0)
       (110
         ((101 (my-semantic-id-for-surface (100 peers)) semantic-id-text)
          (1)
          (postcore-peers-match-id (011 peers) semantic-id-text))
         ((101 (my-semantic-id-for-surface (100 peers)) semantic-id-text)
          (0)
          (001 registry-drift)))))))

(0011 postcore-groups-match-generated-registry
  (0010 (groups)
    (110
      ((010 groups) ()
       (001 registry-consistent))
      ((010 groups) (0)
       (001001 ((group (100 groups))
              (semantic-id (100 group))
              (peers (011 group))
              (semantic-id-text (110111001 semantic-id))
              (projected-count
                (postcore-registry-surface-count
                  semantic-id-text
                  my-semantic-surface-registry)))
         (110
           ((11110111 projected-count (000000 peers)) 1
            (110
              ((101 (postcore-peers-match-id peers semantic-id-text)
                   (001 registry-consistent))
               (1)
               (postcore-groups-match-generated-registry (011 groups)))
              ((101 (postcore-peers-match-id peers semantic-id-text)
                   (001 registry-drift))
               (1)
               (001 registry-drift))))
           ((11110111 projected-count (000000 peers)) 0
            (001 registry-drift))))))))

(0011 postcore-witness-failure
  (0010 (case actual expected)
    (1110
      (001 postcore-peer-materialization-witness)
      (001 (status fail))
      (1110 (001 case) case)
      (1110 (001 actual) actual)
      (1110 (001 expected) expected))))

(0011 postcore-check-rows
  (0010 (rows)
    (110
      ((010 rows) ()
       (001 (postcore-peer-materialization-witness (status pass))))
      ((010 rows) (1)
       (postcore-witness-failure
         (001 malformed-row-tail)
         rows
         (001 ())))
      ((010 rows) (0)
       (001000 ((row (100 rows)))
         (110
           ((11110111 (1001 row) (10011 row)) (1)
            (postcore-check-rows (011 rows)))
           ((11110111 (1001 row) (10011 row)) (0)
            (postcore-witness-failure
              (100 row)
              (1001 row)
              (10011 row)))))))))

(0011 postcore-phase-one
  (postcore-check-rows
    (1110
      ; Every numeric materialization declaration in the post-core libraries
      ; must name a stable source binding from the single semantic authority.
      (1110
        (001 declaration-source-authority)
        (postcore-declarations-match-authority postcore-declarations)
        (001 registry-consistent))

      ; The bootstrap cache must be exactly the set of declared post-core IDs
      ; that currently have more than one unique stable spelling. IDs with only
      ; their source spelling need no cache row yet; promoting a candidate to
      ; stable therefore makes this witness RED until the cache is refreshed.
      (1110
        (001 authority-derived-complete-projection)
        (postcore-projection-matches-authority
          postcore-expected-peer-groups
          my-postcore-stable-peer-projection)
        (001 registry-consistent))

      ; Declaring a post-core identity must never admit candidate spellings.
      (1110
        (001 candidates-remain-unbound)
        (postcore-candidate-surfaces-unbound postcore-declarations)
        (001 candidates-unbound))

      ; The hand-executed runtime projection must exactly match the generated
      ; admitted registry projection for every currently exercised time ID.
      (1110
        (001 generated-registry-parity)
        (postcore-groups-match-generated-registry
          my-postcore-stable-peer-projection)
        (001 registry-consistent))

      ; Both stable spellings route to the same opaque numeric identity.
      (1110
        (001 semantic-id-en)
        (my-semantic-id-for-surface (001 utc-from-unix))
        "1080")
      (1110
        (001 semantic-id-uk)
        (my-semantic-id-for-surface (001 всч-із-юнікс))
        "1080")

      ; The full UKR spelling is still candidate. It must be absent from both
      ; the admitted registry projection and the live environment.
      (1110
        (001 candidate-not-admitted)
        (010
          (my-semantic-id-for-surface
            (001 всесвітній-координований-час-із-часу-юнікс)))
        (001 ()))
      (1110
        (001 candidate-not-bound)
        (my-postcore-binding-status
          (001 всесвітній-координований-час-із-часу-юнікс)
          (11100111))
        (001 absent))

      ; Stable EN/UK peers begin as exactly the same closure and execute with
      ; the same deterministic result.
      (1110
        (001 initial-peer-identity)
        (101 utc-from-unix всч-із-юнікс)
        (001 (1)))
      (1110
        (001 invocation-parity)
        (11110111 (101110110 0 0) (101110110 0 0))
        (001 (1)))

      ; Ordinary lexical shadowing is independent: rebinding one spelling does
      ; not mutate or retarget the other spelling.
      (1110
        (001 lexical-shadowing-independent)
        (001000 ((всч-із-юнікс
                (0010 (seconds nanosecond) (001 shadowed))))
          (101 utc-from-unix всч-із-юнікс))
        (001 (0))))))

; Stronger idempotence law: install an explicit existing peer binding, invoke
; materialization again at top level, and prove the macro does NOT overwrite it.
; This mutation is local to this one-shot witness process.
(0011 postcore-existing-peer
  (0010 (seconds nanosecond) (001 preserved-peer)))

(0011 всч-із-юнікс postcore-existing-peer)
(my-postcore-materialize-stable-peers 1080 utc-from-unix)

(0011 postcore-phase-two
  (postcore-check-rows
    (1110
      (1110
        (001 phase-one)
        postcore-phase-one
        (001 (postcore-peer-materialization-witness (status pass))))
      (1110
        (001 rematerialization-preserves-existing-binding)
        (101 всч-із-юнікс postcore-existing-peer)
        (001 (1)))
      (1110
        (001 rematerialization-does-not-retarget-source)
        (101 всч-із-юнікс utc-from-unix)
        (001 (0)))
      (1110
        (001 preserved-binding-invocation)
        (всч-із-юнікс 0 0)
        (001 preserved-peer)))))

postcore-phase-two
