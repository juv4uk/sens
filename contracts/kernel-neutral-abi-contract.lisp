;; kernel-neutral-abi-contract/1 — the function table, written as SENS code.
;;
;; Every registry call head in this file is the eight-bit code, never the name.
;; Definitions use 00001001 define. 00001011 def is the historical syntax-only
;; form, and this contract does not use it: see the owner rule in issue #1438,
;; "def (00001011) не використовувати; визначення — 00001001".
;; The legend, and the only codes this file is allowed to call:
;;   00001001 define   00001000 lambda   00000111 cond      00000001 quote
;;   00000010 atom?    00000011 eq?      00000100 cons     00000101 car
;;   00000110 cdr
;; That is not a stylistic choice. PRIMITIVE_TABLE in
;; crates/sens/src/eval/canon.rs admits exactly ten callable mechanisms, and
;; this contract uses nine of them. `list`, `assoc`, `equal?`, `or`, `not?` and
;; `let` have no admitted mechanism by code, so a SENS contract must build its
;; own lists and do its own comparison. kernel-join, kernel-one and
;; kernel-fact-scan exist below for exactly that reason.
;;
;; HOW A JUDGEMENT IS WRITTEN HERE
;; cond's canonical form is (QUERY EXPECTED RESULT), where EXPECTED is bare
;; data and selection is an exact structural comparison of the query's
;; result. atom? answers (structural-kind empty-list), (structural-kind pair)
;; or (structural-kind atom); eq? answers (identity-relation same) or
;; (identity-relation distinct). Every clause below therefore names the exact
;; domain result it accepts. No clause here leans on a truthiness reading of
;; those records, so a clause can never fire for the wrong reason. `t` appears
;; only as the final otherwise.
;;
;; THE SHAPES THIS FILE DEPENDS ON
;;   claim   (NAME VALUE)          a proper two-element list
;;   fact    (KEY . VALUE)          a dotted cell, as a C table row reads
;;   facts   a quoted list of fact cells, always supplied from outside
;;   record  a non-empty list, one failed check
;;   group   a list of records, or () when the group passed
;; kernel-one is the only bridge from record to group.
;;
;; WHY THIS FILE IS CODE AND NOT A DATA DOCUMENT
;; A quoted alist of dotted pairs is one reader's spelling. A contract that is
;; only data has to agree with the spelling in order to be read at all, and
;; nothing in it decides anything. Here the substrate's own shape is named
;; once — as quoted table data, which is what the C header declares — and
;; every judgement about it is code: named functions, named predicates, and
;; one report a reader can run.
;;
;; WHY THE FUNCTION TABLE IS THE SUBSTRATE
;; sens and the four external kernels genuinely share exactly one thing: the
;; crates/wsm-kernel-c-abi/include/wsm_kernel.h file. The substrate of this
;; contract is not its typedefs, it is WsmKernelVTable — the table of slots
;; every participant must fill:
;;
;;     abi_version, kernel, context, start, exchange, snapshot, stop
;;
;; This contract is written from that table, in table order. Anything a kernel
;; cannot express through those four slots is not part of this contract.
;;
;; WHO OWNS WHAT
;;   sens        owns `semantic_id` and every meaning attached to a result
;;   common-lisp a WsmKernelKind, one of the four table rows
;;   prolog      a WsmKernelKind, one of the four table rows
;;   clips       a WsmKernelKind, one of the four table rows
;;   datalog     a WsmKernelKind, one of the four table rows
;; The table does not say who owns meaning, so the contract says it: sens does,
;; and a kernel receives one opaque byte it must not interpret.
;;
;; EPISTEMIC DISCIPLINE
;;   - "0/1" is an encoding, never a truth claim.
;;   - Absent evidence is 0, and 0 means "not witnessed". Never assume 1.
;;   - "unknown" is not a representable state. If you cannot say 0/1 you do not
;;     yet have a clause; you have an observation log.
;;   - "compatible with all kernels" is an ABI-level claim only.
;;
;; NON-GOALS, stated so nobody re-adds them by accident
;;   - This does not change the C enum. WsmKernelKind 0 is not a member; this
;;     contract gives 0 a reading, it does not invent a member.
;;   - This does not migrate, deprecate or reinterpret any historical contract.
;;   - This does not define a shared result type. Result value equality is
;;     explicitly not claimed here.

;; ==================================================================
;; 1. The codes, exactly as the table declares them.
;; ==================================================================

(00001001 kernel-abi-version 2)
(00001001 kernel-no 0)
(00001001 kernel-yes 1)
(00001001 kernel-kind-common-lisp 1)
(00001001 kernel-kind-prolog 2)
(00001001 kernel-kind-clips 3)
(00001001 kernel-kind-datalog 4)
(00001001 kernel-kind-unassigned 0)
(00001001 kernel-status-ok 0)
(00001001 kernel-status-invalid-argument 1)
(00001001 kernel-status-not-running 2)
(00001001 kernel-status-buffer-too-small 3)
(00001001 kernel-status-kernel-failure 4)

;; The C table has no bool, so predicates cross as integers: 0 = no, 1 = yes,
;; the same convention WsmStatus already uses for OK = 0.

;; ==================================================================
;; 2. The function table itself, in table order.
;; ==================================================================

(00001001 kernel-slot-order (00000001 (start exchange snapshot stop)))
(00001001 kernel-slot-count 4)

(00001001
  kernel-slot-start
  (00000001
    ((arguments 1)
      (given (00000001 context))
      (returns (00000001 WsmStatus))
      (writes-response 0)
    )
  )
)

(00001001
  kernel-slot-exchange
  (00000001
    ((arguments 4)
      (given (00000001 (context request response written)))
      (returns (00000001 WsmStatus))
      (writes-response 1)
      (takes-request 1)
    )
  )
)

(00001001
  kernel-slot-snapshot
  (00000001
    ((arguments 3)
      (given (00000001 (context response written)))
      (returns (00000001 WsmStatus))
      (writes-response 1)
      (takes-request 0)
    )
  )
)

(00001001
  kernel-slot-stop
  (00000001
    ((arguments 1)
      (given (00000001 context))
      (returns (00000001 WsmStatus))
      (writes-response 0)
    )
  )
)

;; The three values the table carries beside the slots.
(00001001 kernel-table-scalars (00000001 (abi_version kernel context)))
(00001001 kernel-table-scalar-count 3)

;; ==================================================================
;; 3. The claims this ABI-level contract makes, and the ones it refuses.
;;    A claim is (NAME VALUE). Absent evidence is 0 and stays 0.
;; ==================================================================

(00001001
  kernel-boolean-clauses
  (00000001
    ((one-abi-per-kernel-for-every-row 0)
      (every-slot-filled 1)
      (every-slot-returns-wsm-status 1)
      (kernel-may-invent-own-status 0)
      (status-zero-is-ok-not-absent 1)
      (semantic-id-opaque-to-kernel 1)
      (kernel-may-query-semantic-registry 0)
      (kernel-may-mint-semantic-identity 0)
      (kernel-may-omit-slot 0)
      (kernel-private-verb-in-table 0)
      (unknown-is-representable 0)
      (not-witnessed-reads-as 0)
      (assumed-yes-permitted 0)
      (lisp-t-crosses-the-table 0)
      (owner-is-a-table-row 0)
      (common-lisp-witnessed 0)
      (prolog-witnessed 0)
      (clips-witnessed 0)
      (datalog-witnessed 0)
    )
  )
)

(00001001 kernel-claim-is-abi-level-only kernel-yes)
(00001001 kernel-claim-covers-semantic-equivalence kernel-no)
(00001001 kernel-claim-covers-dialect-compatibility kernel-no)
(00001001 kernel-claim-covers-result-value-equality kernel-no)

;; ==================================================================
;; 4. The shapes the rest of the contract needs.
;;    A missing key yields (), and () is distinct from every witnessed value,
;;    so absence stays visible and is never defaulted to a passing value.
;; ==================================================================

;; An alist cell, the shape a C table row has: (KEY . VALUE).
(00001001 kernel-cell (00001000 (key value) (00000100 key value)))

;; eq? refuses anything that is not an atom, so the structural-kind check
;; above the eq? clause is what keeps a list away from it.
(00001001
  kernel-portable-boolean?
  (00001000
    (value)
    (00000111
      ((00000010 value)
        (structural-kind atom)
        (00000111
          ((00000011 value 0)
            (identity-relation same)
            (00000001 kernel-yes)
          )
          ((00000011 value 1)
            (identity-relation same)
            (00000001 kernel-yes)
          )
          (t (00000001 kernel-no))
        )
      )
      (t (00000001 kernel-no))
    )
  )
)

(00001001
  kernel-fact-scan
  (00001000
    (scan key)
    (00000111
      ((00000010 scan) (structural-kind empty-list) (00000001 ()))
      ((00000011 (00000101 (00000101 scan)) key)
        (identity-relation same)
        (00000110 (00000101 scan))
      )
      (t (kernel-fact-scan (00000110 scan) key))
    )
  )
)

(00001001 kernel-fact (00001000 (facts key) (kernel-fact-scan facts key)))

;; This file never uses a dotted parameter list: in this SENS a dotted tail
;; binds to the last argument rather than to the remaining ones, so
;; (first . rest) is not a usable variadic form. Everything below is
;; arity-explicit.
(00001001
  kernel-join
  (00001000
    (left right)
    (00000111
      ((00000010 left) (structural-kind empty-list) right)
      ((00000010 left)
        (structural-kind pair)
        (00000100 (00000101 left) (kernel-join (00000110 left) right))
      )
      (t right)
    )
  )
)

;; A record becomes a group of one; () stays (), so a group never carries an
;; empty element that a reader would have to skip.
(00001001
  kernel-one
  (00001000
    (result)
    (00000111
      ((00000010 result) (structural-kind empty-list) (00000001 ()))
      (t (00000100 result (00000001 ())))
    )
  )
)

;; The first record in a group, or () when the group passed. The group here
;; comes from kernel-join, so every element is a record; the empty-list test
;; is on the group, not on the element.
(00001001
  kernel-first-failure
  (00001000
    (checks)
    (00000111
      ((00000010 checks) (structural-kind empty-list) (00000001 ()))
      (t (00000101 checks))
    )
  )
)

;; ==================================================================
;; 5. The boolean clauses, judged. A clause crosses the C table only as an
;;    integer. `t`, `yes`, `no` and every other dialect's spelling are one
;;    reader's habit and cannot be transported. A clause with a name and no
;;    value behind it is malformed, not passing.
;; ==================================================================

;; One clause, judged on its own. A claim is exactly (NAME VALUE), so the
;; clause tail must be a one-element list: a pair whose own tail is the
;; empty list. A one-element clause ((NAME)), a dotted clause (NAME . X)
;; and a three-element clause ((NAME 0 1)) all fail that shape and are
;; reported as an odd clause tail. A clause of the right shape whose value
;; is not 0 or 1 is a non-portable boolean, not a shape error.
(00001001
  kernel-clause-record
  (00001000
    (clauses)
    (00000111
      ((00000010 (00000110 (00000101 clauses)))
        (structural-kind pair)
        (00000111
          ((00000010 (00000110 (00000110 (00000101 clauses))))
            (structural-kind empty-list)
            (00000111
              ((kernel-portable-boolean? (00000101 (00000110 (00000101 clauses))))
                kernel-yes
                (00000001 ())
              )
              (t
                (00000100
                  (00000001 non-portable-boolean)
                  (00000100 (00000101 clauses) (00000001 ()))
                )
              )
            )
          )
          (t
            (00000100
              (00000001 odd-clause-tail)
              (00000100 (00000101 clauses) (00000001 ()))
            )
          )
        )
      )
      (t
        (00000100
          (00000001 odd-clause-tail)
          (00000100 (00000101 clauses) (00000001 ()))
        )
      )
    )
  )
)

;; Every offending clause, not just the first: a contract that hides the
;; second bad clause behind the first is not a contract.
(00001001
  kernel-clause-failures
  (00001000
    (clauses)
    (00000111
      ((00000010 clauses) (structural-kind empty-list) (00000001 ()))
      (t
        (kernel-join
          (kernel-one (kernel-clause-record clauses))
          (kernel-clause-failures (00000110 clauses))
        )
      )
    )
  )
)

;; The contract's own boolean clauses, judged against the rule that will
;; judge the header's. A contract that cannot survive its own checker is
;; not a contract.
(00001001
  kernel-static-clause-failures
  (00001000 () (kernel-clause-failures kernel-boolean-clauses))
)

;; ==================================================================
;; 6. The codes, checked. A contract that disagrees with its own substrate
;;    is fiction: every code stated here must be the code the real header
;;    declares, and a fact nobody supplied is a failure, never a pass.
;; ==================================================================

(00001001
  kernel-code-value
  (00001000
    (key)
    (00000111
      ((00000011 key (00000001 abi-version))
        (identity-relation same)
        kernel-abi-version
      )
      ((00000011 key (00000001 kind-common-lisp))
        (identity-relation same)
        kernel-kind-common-lisp
      )
      ((00000011 key (00000001 kind-prolog))
        (identity-relation same)
        kernel-kind-prolog
      )
      ((00000011 key (00000001 kind-clips))
        (identity-relation same)
        kernel-kind-clips
      )
      ((00000011 key (00000001 kind-datalog))
        (identity-relation same)
        kernel-kind-datalog
      )
      ((00000011 key (00000001 status-ok))
        (identity-relation same)
        kernel-status-ok
      )
      ((00000011 key (00000001 status-invalid-argument))
        (identity-relation same)
        kernel-status-invalid-argument
      )
      ((00000011 key (00000001 status-not-running))
        (identity-relation same)
        kernel-status-not-running
      )
      ((00000011 key (00000001 status-buffer-too-small))
        (identity-relation same)
        kernel-status-buffer-too-small
      )
      ((00000011 key (00000001 status-kernel-failure))
        (identity-relation same)
        kernel-status-kernel-failure
      )
      (t (00000001 ()))
    )
  )
)

(00001001
  kernel-abr-codes
  (00000001
    (abi-version
      kind-common-lisp
      kind-prolog
      kind-clips
      kind-datalog
      status-ok
      status-invalid-argument
      status-not-running
      status-buffer-too-small
      status-kernel-failure
    )
  )
)

(00001001
  kernel-check-one-code
  (00001000
    (facts key)
    (00000111
      ((00000011 (kernel-fact facts key) (00000001 ()))
        (identity-relation same)
        (00000100 (00000001 missing-fact) (00000100 key (00000001 ())))
      )
      ((00000011 (kernel-fact facts key) (kernel-code-value key))
        (identity-relation same)
        (00000001 ())
      )
      (t
        (00000100
          (00000001 code-mismatch)
          (00000100
            key
            (00000100
              (00000100
                (00000001 header)
                (00000100 (kernel-fact facts key) (00000001 ()))
              )
              (00000100
                (00000100
                  (00000001 contract)
                  (00000100 (kernel-code-value key) (00000001 ()))
                )
                (00000001 ())
              )
            )
          )
        )
      )
    )
  )
)

(00001001
  kernel-code-failures
  (00001000
    (facts keys)
    (00000111
      ((00000010 keys) (structural-kind empty-list) (00000001 ()))
      (t
        (kernel-join
          (kernel-one (kernel-check-one-code facts (00000101 keys)))
          (kernel-code-failures facts (00000110 keys))
        )
      )
    )
  )
)

;; The four rows of the table. A row is compatible by construction; it is
;; compatible by evidence only once a real run has crossed the table. This
;; contract starts at 0 and stays there until a witness run says otherwise.
(00001001
  kernel-unwitnessed-rows
  (00000001 ((common-lisp 0) (prolog 0) (clips 0) (datalog 0)))
)

;; ==================================================================
;; 7. The report. `facts` arrives from outside this file — the C header,
;;    read by an external witness. This function never invents a fact.
;; ==================================================================

;; An absent slot count is absence, not a disagreement: the two are reported
;; separately, because a header that never spoke must not look like a header
;; that spoke wrongly.
(00001001
  kernel-slot-count-failure
  (00001000
    (facts)
    (00000111
      ((00000011 (kernel-fact facts (00000001 slot-count)) (00000001 ()))
        (identity-relation same)
        (00000100
          (00000001 missing-fact)
          (00000100 (00000001 slot-count) (00000001 ()))
        )
      )
      ((00000011 (kernel-fact facts (00000001 slot-count)) kernel-slot-count)
        (identity-relation same)
        (00000001 ())
      )
      (t
        (00000100
          (00000001 slot-count-mismatch)
          (00000100
            (00000100
              (00000001 table)
              (00000100 kernel-slot-count (00000001 ()))
            )
            (00000100
              (00000100
                (00000001 header)
                (00000100
                  (kernel-fact facts (00000001 slot-count))
                  (00000001 ())
                )
              )
              (00000001 ())
            )
          )
        )
      )
    )
  )
)

(00001001
  kernel-slot-count-failures
  (00001000 (facts) (kernel-one (kernel-slot-count-failure facts)))
)

(00001001
  kernel-compatibility-detail
  (00001000
    (rows)
    (00000100
      (00000001 compatible-at-abi-level)
      (00000100
        (00000100 (00000001 rows) (00000100 rows (00000001 ())))
        (00000100
          (00000100
            (00000001 claims)
            (00000100 kernel-claim-is-abi-level-only (00000001 ()))
          )
          (00000001 ())
        )
      )
    )
  )
)

(00001001
  kernel-fail-report
  (00001000
    (detail)
    (00000100
      (00000001 kernel-neutral-abi-report)
      (00000100
        (00000100
          (00000001 status)
          (00000100 (00000001 fail) (00000001 ()))
        )
        (00000100
          (00000100 (00000001 detail) (00000100 detail (00000001 ())))
          (00000001 ())
        )
      )
    )
  )
)

(00001001
  kernel-pass-report
  (00001000
    (detail)
    (00000100
      (00000001 kernel-neutral-abi-report)
      (00000100
        (00000100
          (00000001 status)
          (00000100 (00000001 pass) (00000001 ()))
        )
        (00000100
          (00000100 (00000001 detail) (00000100 detail (00000001 ())))
          (00000001 ())
        )
      )
    )
  )
)

(00001001
  kernel-neutral-abi-report
  (00001000
    (facts)
    (00000111
      ((00000010 facts)
        (structural-kind empty-list)
        (kernel-fail-report
          (00000100 (00000001 missing-fact) (00000100 facts (00000001 ())))
        )
      )
      ((00000010 (kernel-first-failure (kernel-join (kernel-static-clause-failures) (kernel-join (kernel-code-failures facts kernel-abr-codes) (kernel-slot-count-failures facts)))))
        (structural-kind empty-list)
        (kernel-pass-report
          (kernel-compatibility-detail kernel-unwitnessed-rows)
        )
      )
      (t
        (kernel-fail-report
          (kernel-first-failure
            (kernel-join
              (kernel-static-clause-failures)
              (kernel-join
                (kernel-code-failures facts kernel-abr-codes)
                (kernel-slot-count-failures facts)
              )
            )
          )
        )
      )
    )
  )
)

