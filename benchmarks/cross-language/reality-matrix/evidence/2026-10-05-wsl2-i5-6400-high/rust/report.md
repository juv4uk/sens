# SENS vs Rust — D3 smoke reality slice

This is a native-mechanism control, not a whole-language ranking.
The blocked headline corpus is not bypassed.
Evidence mode: performance; load context: high.

| axis | verdict | evidence |
|---|---|---|
| d3-quote-empty:warm_ready_execution_ns_per_op | competitor | median SENS=100.241 ns/op; Rust=2.565 ns/op |
| d3-quote-empty:process_maxrss_kb | inconclusive | RSS withheld: cumulative wait4 child-max is not a valid per-process comparison |
| d3-car-empty:warm_ready_execution_ns_per_op | competitor | median SENS=479.205 ns/op; Rust=2.565 ns/op |
| d3-car-empty:process_maxrss_kb | inconclusive | RSS withheld: cumulative wait4 child-max is not a valid per-process comparison |
| binary_artifact_bytes | inconclusive | observed SENS=1042552 bytes; Rust=368104 bytes; not ranked because the SENS benchmark helper and direct Rust control do not have a matched dependency/runtime closure |
