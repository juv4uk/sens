(sens-runtime-lookup-inventory/1
  (issue 1556)
  (baseline "origin/main@4abb15f2")
  (role research-only)
  (semantic-authority-change none)

  (measured-layout
    (Sens8-bytes 1)
    (Value-bytes 64)
    (Option-Value-bytes 64)
    (Option-function-pointer-bytes 8)
    (full-256-value-table-bytes 16384)
    (full-256-function-pointer-table-bytes 2048))

  (row
    (target primitive-dispatch)
    (path "crates/sens/src/eval/canon.rs")
    (current direct-index-256)
    (key exact-Sens8-packed-byte)
    (hot-path yes)
    (classification already-optimal)
    (action keep))

  (row
    (target special-route-dispatch)
    (path "crates/sens/src/eval/canon.rs")
    (current direct-index-bounded-seven)
    (key exact-Sens8-packed-byte-minus-one)
    (hot-path yes)
    (classification already-direct)
    (action keep))

  (row
    (target fasl-sens-decode)
    (path "crates/sens/src/syntax.rs")
    (current byte-direct-to-Sens8)
    (key one-wire-byte)
    (hot-path load-time)
    (classification already-optimal)
    (action keep))
  (row
    (target language-definition-code-slots)
    (path "crates/sens/src/environment.rs")
    (current HashMap-u8-Value)
    (key exact-Sens8-packed-byte)
    (hot-path fallback-after-primitive)
    (candidate direct-index-256)
    (memory-if-dense-bytes 16384)
    (classification benchmark-before-change)
    (reason "Value is 64 bytes; dense table costs 16 KiB per shared session limits object even when sparse"))

  (row
    (target exact-host-capability-registry)
    (path "crates/sens/src/eval/capabilities.rs")
    (current HashMap-Sens8-function-pointer)
    (key exact-Sens8)
    (candidate direct-index-256)
    (memory-if-dense-bytes 2048)
    (production-dispatch currently-test-only)
    (classification mechanically-clean-but-not-hot-yet)
    (action defer-until-production-caller-or-measured-need))

  (row
    (target semantic-registry-id-to-row)
    (path "crates/sens/src/semantic_registry.rs")
    (current linear-find-over-256-contiguous-generated-rows)
    (key exact-Sens8-packed-byte)
    (candidate direct-index-256)
    (authority generated-projection-only)
    (hot-path mixed)
    (classification safe-candidate)
    (action benchmark-call-sites-first))

  (row
    (target tooling-signature-kind)
    (path "crates/sens/src/language_items.rs")
    (current linear-find-over-58-generated-rows)
    (key exact-Sens8-packed-byte)
    (hot-path no)
    (classification direct-table-not-justified)
    (action keep-until-measured))
  (row
    (target necessary-form-dispatch)
    (path "crates/sens/src/eval/necessary_forms.rs")
    (current linear-find-over-small-generated-table)
    (key exact-Sens8-packed-byte)
    (hot-path evaluator-control)
    (cardinality tiny)
    (classification direct-256-table-not-obviously-better)
    (action measure-before-change))

  (row
    (target surface-to-Sens8-resolution)
    (path "crates/sens/src/semantic_registry.rs")
    (current HashMap-surface-Sens8)
    (key human-surface)
    (post-resolution no)
    (classification appropriate)
    (reason "pre-resolution human spelling lookup is not an exact-Sens8 address-space problem")
    (action keep))

  (priority
    (first primitive-dispatch already-done)
    (second semantic-registry-exact-id-row-measure)
    (third code-slot-array-vs-hash-benchmark)
    (fourth exact-host-capability-array-only-when-production-used))

  (invariant
    "direct indexing may store only mechanism/projection/cache data; SENS-owned law remains authority")

  (negative-rule
    "do not replace a sparse or cold lookup with a 256-slot table merely because Sens8 is one byte")

  (next-evidence
    (microbench code-slot-hash-vs-array)
    (whole-workload fib-loop-closures)
    (instruction-count before-after)
    (rss-before-after)
    (semantic-registry exact-id callsite profile)))