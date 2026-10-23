//! Bounded source-word fast-path benchmark; this is not the D1–24+ ladder.
//!
//! Measures source-word -> width-qualified DomainIdentity, not language execution.
//! The widest adapter variant uses u16; its top bit must survive. No registry, semantic callable projection,
//! spelling, historical 8-bit authority or benchmark-local domain-law table.

use sens::{
    BinarySourceWord, Bit1, Bit2, Bit3, Bit4, Bit5, Bit6, Bit7, Bit8, Bit9, DomainIdentity,
};
use std::{env, hint::black_box, process::ExitCode, time::Instant};

fn source_word(width: u8, raw: u16) -> BinarySourceWord {
    let low = raw as u8;
    match width {
        1 => BinarySourceWord::W1(Bit1::new(low & 0b1).unwrap()),
        2 => BinarySourceWord::W2(Bit2::new(low & 0b11).unwrap()),
        3 => BinarySourceWord::W3(Bit3::new(low & 0b111).unwrap()),
        4 => BinarySourceWord::W4(Bit4::new(low & 0b1111).unwrap()),
        5 => BinarySourceWord::W5(Bit5::new(low & 0b1_1111).unwrap()),
        6 => BinarySourceWord::W6(Bit6::new(low & 0b11_1111).unwrap()),
        7 => BinarySourceWord::W7(Bit7::new(low & 0b111_1111).unwrap()),
        8 => BinarySourceWord::W8(Bit8::new(low).unwrap()),
        9 => BinarySourceWord::W9(Bit9::new(raw & 0x01ff).unwrap()),
        _ => unreachable!(),
    }
}

fn verify_invariants() {
    for width in 1..=9 {
        let source = source_word(width, 1);
        let identity = source.domain_identity();
        assert_eq!(identity.width(), width as usize);
        assert_eq!(identity.packed_bits(), 1);
        assert_eq!(identity.source_word(), source);
    }

    let same_payload = [
        source_word(1, 1).domain_identity(),
        source_word(2, 1).domain_identity(),
        source_word(3, 1).domain_identity(),
        source_word(4, 1).domain_identity(),
        source_word(5, 1).domain_identity(),
        source_word(6, 1).domain_identity(),
        source_word(7, 1).domain_identity(),
        source_word(8, 1).domain_identity(),
        source_word(9, 1).domain_identity(),
    ];
    for left in 0..same_payload.len() {
        for right in left + 1..same_payload.len() {
            assert_ne!(same_payload[left], same_payload[right]);
        }
    }

    // High W9 payload bit must not truncate to historical u8.
    let high = source_word(9, 0x101);
    let identity = DomainIdentity::from_source_word(high);
    assert_eq!(identity.width(), 9);
    assert_eq!(identity.packed_bits(), 0x101);
    assert_eq!(identity.source_word(), high);
    assert_ne!(identity, source_word(8, 1).domain_identity());
}

#[inline(never)]
fn run_empty(iterations: u64) -> u64 {
    let mut acc = 0u64;
    for i in 0..iterations {
        acc = acc.wrapping_add(black_box(i) & 1);
    }
    black_box(acc)
}

#[inline(never)]
fn run_domain(width: u8, iterations: u64) -> u64 {
    let mut acc = 0u64;
    for i in 0..iterations {
        let raw = black_box((i as u16) ^ ((i as u16) >> 1));
        let source = source_word(width, raw);
        let identity = DomainIdentity::from_source_word(source);
        acc = acc
            .wrapping_add(identity.packed_bits() as u64)
            .wrapping_add(identity.width() as u64);
    }
    black_box(acc)
}

#[inline(never)]
fn run_mixed(iterations: u64) -> u64 {
    let mut acc = 0u64;
    for i in 0..iterations {
        let width = ((black_box(i) % 9) + 1) as u8;
        let source = source_word(width, (i as u16) ^ ((i as u16) >> 1));
        let identity = source.domain_identity();
        acc = acc
            .wrapping_add(identity.packed_bits() as u64)
            .wrapping_add(identity.width() as u64);
    }
    black_box(acc)
}

#[inline(never)]
fn run_width_roundtrip(iterations: u64) -> u64 {
    let mut acc = 0u64;
    for i in 0..iterations {
        let width = ((black_box(i) % 9) + 1) as u8;
        let source = source_word(width, (i as u16) ^ ((i as u16) >> 1));
        let identity = DomainIdentity::from_source_word(source);
        let restored = identity.source_word();
        acc = acc
            .wrapping_add(restored.packed_bits() as u64)
            .wrapping_add(restored.width() as u64);
    }
    black_box(acc)
}

fn run_case(case: &str, iterations: u64) -> Option<u64> {
    Some(match case {
        "empty" => run_empty(iterations),
        "d1" => run_domain(1, iterations),
        "d2" => run_domain(2, iterations),
        "d3" => run_domain(3, iterations),
        "d4" => run_domain(4, iterations),
        "d5" => run_domain(5, iterations),
        "d6" => run_domain(6, iterations),
        "d7" => run_domain(7, iterations),
        "d8" => run_domain(8, iterations),
        "d9" => run_domain(9, iterations),
        "mixed" => run_mixed(iterations),
        "width-roundtrip" => run_width_roundtrip(iterations),
        _ => return None,
    })
}

fn run_series(case: &str, iterations: u64, samples: usize) -> Result<(), String> {
    const TARGET_SAMPLE_NS: u128 = 25_000_000;
    const MAX_BATCH_REPS: u64 = 10_000_000;

    if iterations == 0 || samples < 5 || samples.is_multiple_of(2) {
        return Err("iterations must be positive; samples must be odd and >= 5".into());
    }
    if run_case(case, iterations).is_none() {
        return Err(format!("unknown case: {case}"));
    }

    // Invariants were proven by verify_invariants before entering this path.
    for _ in 0..3 {
        black_box(run_case(case, iterations).expect("validated benchmark case"));
    }
    let mut values = Vec::with_capacity(samples);
    for sample in 0..samples {
        let mut reps = 1u64;
        let (elapsed_ns, checksum) = loop {
            let started = Instant::now();
            let mut checksum = 0u64;
            for _ in 0..reps {
                checksum = checksum.wrapping_add(
                    run_case(case, iterations).expect("validated benchmark case")
                );
            }
            black_box(checksum);
            let elapsed = started.elapsed().as_nanos();
            if elapsed >= TARGET_SAMPLE_NS {
                break (elapsed, checksum);
            }
            if reps >= MAX_BATCH_REPS {
                return Err(format!(
                    "adaptive sample too short: case={case} reps={reps} elapsed_ns={elapsed}"
                ));
            }
            let factor = TARGET_SAMPLE_NS.div_ceil(elapsed.max(1));
            let factor = u64::try_from(factor).unwrap_or(u64::MAX);
            reps = reps.saturating_mul(factor).clamp(reps.saturating_add(1), MAX_BATCH_REPS);
        };
        let operations = u128::from(iterations) * u128::from(reps);
        let ns_per_iteration = elapsed_ns as f64 / operations as f64;
        if !ns_per_iteration.is_finite() || ns_per_iteration <= 0.0 {
            return Err(format!("invalid timing sample: case={case}"));
        }
        values.push(ns_per_iteration);
        println!(
            "RUST_DOMAIN_SAMPLE\tcase={case}\tsample={}\titerations={iterations}\treps={reps}\telapsed_ns={elapsed_ns}\tns_per_iteration={ns_per_iteration:.3}\tchecksum={checksum}\ttarget_sample_ns={TARGET_SAMPLE_NS}",
            sample + 1,
        );
    }
    let mut sorted = values.clone();
    sorted.sort_by(f64::total_cmp);
    let median_index = (sorted.len() - 1) / 2;
    let p90_index = ((sorted.len() * 9).div_ceil(10)).saturating_sub(1).min(sorted.len() - 1);
    println!(
        "RUST_DOMAIN_SUMMARY\tcase={case}\tsamples={samples}\tp50_ns_per_iteration={:.3}\tp90_ns_per_iteration={:.3}\titerations_per_repetition={iterations}\tinvariant=exact-width-roundtrip\ttarget_sample_ns={TARGET_SAMPLE_NS}",
        sorted[median_index],
        sorted[p90_index],
    );
    Ok(())
}

fn main() -> ExitCode {
    verify_invariants();

    let args: Vec<String> = env::args().collect();
    if args.len() == 5 && args[1] == "series" {
        let iterations = match args[3].parse::<u64>() {
            Ok(value) if value > 0 => value,
            _ => {
                eprintln!("RUST_DOMAIN_INVALID_INPUT: iterations must be positive");
                return ExitCode::from(2);
            }
        };
        let samples = match args[4].parse::<usize>() {
            Ok(value) if value >= 5 && value % 2 == 1 => value,
            _ => {
                eprintln!("RUST_DOMAIN_INVALID_INPUT: samples must be odd and >= 5");
                return ExitCode::from(2);
            }
        };
        return match run_series(&args[2], iterations, samples) {
            Ok(()) => ExitCode::SUCCESS,
            Err(error) => {
                eprintln!("RUST_DOMAIN_INVALID_INPUT_OR_TIMING: {error}");
                ExitCode::from(2)
            }
        };
    }

    let mut args = args.into_iter().skip(1);
    let case = args.next().unwrap_or_else(|| "empty".to_owned());
    let iterations = args
        .next()
        .and_then(|s| s.parse::<u64>().ok())
        .filter(|n| *n > 0)
        .unwrap_or(200_000);

    let Some(checksum) = run_case(&case, iterations) else {
        eprintln!("unknown case: {case}");
        return ExitCode::from(2);
    };

    println!("case={case} iterations={iterations} checksum={checksum}");
    ExitCode::SUCCESS
}
