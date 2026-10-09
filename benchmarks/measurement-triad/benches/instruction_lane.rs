//! Iai-Callgrind measures Callgrind instruction refs, never wall-clock latency.
use iai_callgrind::{library_benchmark, library_benchmark_group};
use sens_measurement_triad::scan_d3_owner_residency;

#[library_benchmark]
fn d3_owner_lookup_1024() -> usize {
    std::hint::black_box(scan_d3_owner_residency(1_024))
}

library_benchmark_group!(
    name = d3_mechanical_owner;
    benchmarks = d3_owner_lookup_1024
);

iai_callgrind::main!(library_benchmark_groups = d3_mechanical_owner);
