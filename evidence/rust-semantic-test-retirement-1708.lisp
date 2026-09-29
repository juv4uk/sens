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

  (next
    "inventory remaining crates/sens/tests and cfg(test) modules; move or delete semantic assertions before binary-only cutover."))