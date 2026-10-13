//! Iai-Callgrind measures Callgrind instruction refs, never wall-clock latency.
//! The D1-D10 lane measures reads only: corpus construction and validation
//! happen in setup outside the instrumented benchmark.
use iai_callgrind::{library_benchmark, library_benchmark_group};
use sens::{domain_ladder::DomainCoordinate, BitPacker, PackedBitstream};
use sens_measurement_triad::scan_d3_owner_residency;
use std::hint::black_box;

#[library_benchmark]
fn d3_owner_lookup_1024() -> usize {
    black_box(scan_d3_owner_residency(1_024))
}

library_benchmark_group!(
    name = d3_mechanical_owner;
    benchmarks = d3_owner_lookup_1024
);

/// Setup deliberately does not enter the measured Callgrind instruction count.
/// All 2046 width-qualified coordinates, including D10 spanning three bytes,
/// are independently checked against the canonical packed reader before use.
fn packed_domain_corpus(max_width: u8) -> (PackedBitstream, Vec<(usize, DomainCoordinate)>) {
    assert!((1..=10).contains(&max_width));
    let mut packer = BitPacker::new();
    let mut locations = Vec::new();
    for width in 1..=max_width {
        for bits in 0u16..(1u16 << width) {
            let coordinate = DomainCoordinate::new(width, bits).expect("exact domain");
            let offset = packer.push_coordinate(coordinate);
            locations.push((offset, coordinate));
        }
    }
    let packed = packer.finish();
    for &(offset, coordinate) in &locations {
        assert_eq!(
            packed.read_coordinate(offset, coordinate.width()),
            Some(coordinate),
            "bit-exact setup parity"
        );
    }
    (packed, locations)
}

#[library_benchmark]
#[bench::all_d1_d10(args = (10u8), setup = packed_domain_corpus)]
fn packed_reads_2046(corpus: (PackedBitstream, Vec<(usize, DomainCoordinate)>)) -> u64 {
    let (packed, locations) = corpus;
    let mut checksum = 0u64;
    for (offset, coordinate) in &locations {
        let actual = packed
            .read_coordinate(black_box(*offset), black_box(coordinate.width()))
            .expect("validated mechanical coordinate");
        checksum = checksum.wrapping_add(u64::from(actual.bits()));
    }
    black_box(checksum)
}

library_benchmark_group!(
    name = exact_domain_packed_reads;
    benchmarks = packed_reads_2046
);

iai_callgrind::main!(library_benchmark_groups = d3_mechanical_owner, exact_domain_packed_reads);
