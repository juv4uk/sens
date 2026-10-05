# SENS vs WebAssembly — D3 reality slice

This is a mechanism/Pareto control, not a whole-language ranking.
Evidence mode: performance; load context: high.

| axis | verdict | evidence |
|---|---|---|
| d3-quote-empty:program_semantic_or_module_bits | sens | SENS=13.000; Wasm=288.000 |
| d3-quote-empty:program_container_or_module_bytes | sens | SENS=2.000; Wasm=36.000 |
| d3-quote-empty:ingest_vs_compile_ns | inconclusive | observation only: SENS=16000.000; Wasm=383704.000; phase/runtime boundary is not equivalent |
| d3-quote-empty:warm_ready_execution_ns_per_op | sens | SENS=94.967; Wasm=113.836 |
| d3-quote-empty:cold_total_internal_ns | inconclusive | observation only: SENS=8974992.000; Wasm=469195.500; phase/runtime boundary is not equivalent |
| d3-quote-empty:process_maxrss_kb | inconclusive | RSS withheld pending shared owner #3698 |
| d3-car-empty:program_semantic_or_module_bits | sens | SENS=26.000; Wasm=480.000 |
| d3-car-empty:program_container_or_module_bytes | sens | SENS=4.000; Wasm=60.000 |
| d3-car-empty:ingest_vs_compile_ns | inconclusive | observation only: SENS=19410.000; Wasm=481377.500; phase/runtime boundary is not equivalent |
| d3-car-empty:warm_ready_execution_ns_per_op | competitor | SENS=480.299; Wasm=124.886 |
| d3-car-empty:cold_total_internal_ns | inconclusive | observation only: SENS=9285814.500; Wasm=510985.500; phase/runtime boundary is not equivalent |
| d3-car-empty:process_maxrss_kb | inconclusive | RSS withheld pending shared owner #3698 |
