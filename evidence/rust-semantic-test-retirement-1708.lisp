; #1708 — first Rust semantic-test retirement inventory.
; Lisp owns language meaning; Rust owns mechanism/boundary/safety evidence.

(rust-semantic-test-retirement/1
  (owner sens)
  (governing-issue "1708")

  (row
    (path "crates/sens/tests/core4_eq_answer_1258.rs")
    (classification historical-semantic-debt)
    (action delete-obsolete)
    (reason "Superseded Core4-only EQ and graded-answer semantics; new law belongs to Lisp #1709/#1705."))

  (row
    (path "crates/sens/tests/core2_runtime_profile.rs")
    (classification semantic-law)
    (action delete-obsolete)
    (reason "Encoded historical T/NIL, truthiness and profile-specific COND semantics superseded by #1703."))

  (row
    (path "crates/sens/tests/semantic_coordinate_law_axis.rs")
    (classification mixed)
    (action split)
    (kept rust-boundary)
    (removed semantic-law)
    (reason "Retain surface-to-Function8 non-minting boundary only; Lisp owns EQ/COND/arithmetic law."))

  (row
    (path "crates/sens/tests/core_profile_runtime_1272.rs")
    (classification mechanism)
    (action keep-rust)
    (reason "Carries only selected-Core signal/propagation and does not define language truth semantics."))

  (row
    (path ".github/workflows/core2-runtime-profile.yml")
    (classification mechanism)
    (action split)
    (reason "Active workflow now runs only selected-Core carrier mechanics; old Core2 semantic assertions removed."))

  (row
    (path ".github/workflows/core2-profile-contract.yml")
    (classification historical-semantic-debt)
    (action manual-archive)
    (reason "Historical Contract-6/T-NIL semantics no longer block pull requests or main; preserved only as manual archive evidence."))

  (row
    (path "crates/sens/tests/sens_self_carry_1397.rs")
    (classification mixed)
    (action split)
    (kept function-number-boundary)
    (removed decimal-default-seven-bit-assumption)
    (reason "Use explicit #b numeric projection so the witness cannot freeze the future bare-binary reader."))

  (row
    (path "crates/sens/tests/uk_surface.rs")
    (classification mixed)
    (action split)
    (removed old-mixed-result-domain-assertion)
    (reason "Surface plumbing remains; old predicate/result-domain semantic expectations move to Lisp authority."))

  (row
    (path "crates/sens/tests/mccarthy.rs")
    (classification mixed)
    (action follow-up)
    (reason "Large legacy file mixes mechanism, parser, arithmetic, old truth and language semantic assertions; split only after Lisp witness lane #1709 is executable."))

  (next
    "continue with mccarthy.rs and other mixed Rust semantic suites after #1709 can receive active language expectations."))