//! Criterion wall-time is informational unless the host is controlled and pinned.
use criterion::{criterion_group, criterion_main, Criterion, Throughput};
use sens_measurement_triad::{scan_d3_owner_residency, verify_d3_owner_projection};
use std::{hint::black_box, time::Duration};

fn measure_owner_projection(c: &mut Criterion) {
    verify_d3_owner_projection();
    let mut group = c.benchmark_group("exact_d3_owner_residency");
    group.sample_size(50);
    group.warm_up_time(Duration::from_secs(3));
    group.measurement_time(Duration::from_secs(5));
    group.throughput(Throughput::Elements(1_024));
    group.bench_function("1024_owner_lookups", |b| {
        b.iter(|| black_box(scan_d3_owner_residency(black_box(1_024))))
    });
    group.finish();
}

criterion_group!(benches, measure_owner_projection);
criterion_main!(benches);
