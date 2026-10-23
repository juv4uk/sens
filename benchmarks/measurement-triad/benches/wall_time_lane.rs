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
    // Незалежні розміри відрізняють фіксовану вартість виклику від
    // масштабування механічного lookup. Стара 1024-база зберігає своє ім'я.
    for (label, iterations) in [
        ("256_owner_lookups", 256_usize),
        ("1024_owner_lookups", 1_024_usize),
        ("4096_owner_lookups", 4_096_usize),
    ] {
        // Це перевірка механічної таблиці D3; мовного оракула тут немає.
        assert_eq!(scan_d3_owner_residency(iterations), iterations * 7 / 8);
        group.throughput(Throughput::Elements(iterations as u64));
        group.bench_function(label, |b| {
            b.iter(|| black_box(scan_d3_owner_residency(black_box(iterations))))
        });
    }
    group.finish();
}

criterion_group!(benches, measure_owner_projection);
criterion_main!(benches);
