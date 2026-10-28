//! Criterion wall-time is informational unless the host is controlled and pinned.
use criterion::{criterion_group, criterion_main, Criterion, Throughput};
use sens::{domain_ladder::DomainCoordinate, BitPacker};
use sens_measurement_triad::scan_d3_owner_residency;
use std::{hint::black_box, time::Duration};

fn measure_owner_projection(c: &mut Criterion) {
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
        // Лише вимір функції; очікувану семантику D3 не обчислює Rust.
        group.throughput(Throughput::Elements(iterations as u64));
        group.bench_function(label, |b| {
            b.iter(|| black_box(scan_d3_owner_residency(black_box(iterations))))
        });
    }
    group.finish();
}


fn measure_packed_domain_reads(c: &mut Criterion) {
    // Rust вимірює механічне читання точних координат, не семантику SENS.
    // Корпус та бітова парність перевіряються ДО запуску Criterion.
    let mut packer = BitPacker::new();
    let mut locations = Vec::new();
    for width in 1u8..=10 {
        for bits in 0..(1u16 << width) {
            let coordinate = DomainCoordinate::new(width, bits).expect("exact width");
            let offset = packer.push_coordinate(coordinate);
            locations.push((offset, coordinate));
        }
    }
    let packed = packer.finish();
    assert_eq!(locations.len(), 2_046);
    assert_eq!(packed.bit_len(), 18_434);
    for &(offset, coordinate) in &locations {
        assert_eq!(packed.read_coordinate(offset, coordinate.width()), Some(coordinate));
    }
    let mut group = c.benchmark_group("exact_d1_d10_packed_reader");
    group.sample_size(50);
    group.warm_up_time(Duration::from_secs(3));
    group.measurement_time(Duration::from_secs(5));
    group.throughput(Throughput::Elements(locations.len() as u64));
    group.bench_function("2046_mixed_width_reads", |b| {
        b.iter(|| {
            let mut checksum = 0u64;
            for &(offset, coordinate) in black_box(&locations) {
                let decoded = packed.read_coordinate(
                    black_box(offset), black_box(coordinate.width())
                ).expect("validated mechanical input");
                checksum = checksum.wrapping_add(u64::from(decoded.bits()));
            }
            black_box(checksum)
        })
    });
    group.finish();
}

criterion_group!(benches, measure_owner_projection, measure_packed_domain_reads);
criterion_main!(benches);
