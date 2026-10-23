//! Бенчмарк механізму копіювання байтів Rust — без семантики SENS.
//! rustc -O benchmarks/mechanism/rust-byte-copy-bench.rs -o /tmp/sens-rust-bench
//! /tmp/sens-rust-bench
use std::hint::black_box;
use std::time::Instant;

const SOURCE: &[u8] = include_bytes!("../../lib/core4.lisp");
const SAMPLES: usize = 11;
const BATCH: usize = 512;

fn main() {
    assert!(!SOURCE.is_empty(), "source must not be empty");
    let mut dest = vec![0u8; SOURCE.len()];
    let mut samples = [0u128; SAMPLES];
    let mut checksum = 0u8;
    for sample in 0..=SAMPLES {
        let start = Instant::now();
        for _ in 0..BATCH {
            black_box(dest.as_mut_slice()).copy_from_slice(black_box(SOURCE));
            checksum ^= black_box(dest[0]);
        }
        let elapsed = start.elapsed().as_nanos();
        assert_eq!(dest.as_slice(), SOURCE, "Rust mechanism lost bytes");
        if sample > 0 {
            samples[sample - 1] = elapsed;
        }
    }
    samples.sort_unstable();
    assert!(samples[0] > 0, "clock resolution too coarse");
    println!(
        "RUST_BYTE_COPY_BENCH source=lib/core4.lisp bytes={} batch={} samples={} p50_ns={} p90_ns={} min_ns={} max_ns={} checksum={} scope=mechanism_only",
        SOURCE.len(), BATCH, SAMPLES, samples[5], samples[9], samples[0], samples[10], checksum
    );
}
