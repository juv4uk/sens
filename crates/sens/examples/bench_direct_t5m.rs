//! Measurement-only pilot: separate physical decode, D2 admission,
//! visible-source baseline, and repeated interpretation on the SAME hardware.
//! Reports observations, never asserts a synthetic speedup or a native ISA.
use sens::{render_binary_words_spaced, 
    eval_parsed_expressions, lower_program,
    parse_canonical_binary, PhysicalT5Program, Session,
};
#[path = "support/reference_t5m.rs"]
mod reference_t5m;
use std::{hint::black_box, time::Instant};
use sens_cli::zig_transport;
const QUOTE: &[u8] =
    include_bytes!("../../../tests/fixtures/migration-quote-cohort-main/quote-legacy.sens");
const ATOM: &[u8] = include_bytes!("../../../tests/fixtures/migration-atom-cohort/atom-empty.sens");
const COND: &[u8] = include_bytes!("../../../tests/fixtures/migration-d1-cond-cohort/branch.sens");

fn measure(mut task: impl FnMut(), count: usize) -> f64 {
    let start = Instant::now();
    for _ in 0..count {
        task();
    }
    start.elapsed().as_secs_f64() * 1e9 / count as f64
}

fn main() {
    let iterations: usize = std::env::args()
        .nth(1)
        .map(|s| s.parse().expect("iterations must be a positive integer"))
        .unwrap_or(2_000);
    assert!((1..=1_000_000).contains(&iterations));
    eprintln!(
        "measurement only; ns/op includes allocations and host overhead; iterations={iterations}"
    );
    println!("fixture,bytes,forms,t5m_reference_decode_only_ns,t5m_exact_word_admission_ns,t5m_reference_decode_parse_lower_ns,visible_parse_lower_ns,cached_lowered_eval_ns");
    for (label, bytes) in [("quote", QUOTE), ("atom", ATOM), ("cond", COND)] {
        let words = zig_transport::decode_t5m_words(bytes).unwrap();
        let program = reference_t5m::program(bytes).unwrap();
        let visible = render_binary_words_spaced(&zig_transport::decode_t5m_words(bytes)).unwrap();
        let reference = parse_canonical_binary(&visible).unwrap();
        let expected = eval_parsed_expressions(&reference, &mut Session::default()).unwrap();
        let actual = program.execute(&mut Session::default()).unwrap();
        assert_eq!(expected.value, actual.value);
        assert_eq!(expected.output, actual.output);
        // Untimed warmups. No reliance on timing to establish semantics.
        for _ in 0..100 {
            black_box(zig_transport::decode_t5m_words(black_box(bytes)).unwrap());
            black_box(PhysicalT5Program::from_exact_words(black_box(&words)).unwrap());
            black_box(reference_t5m::program(black_box(bytes)).unwrap());
            black_box(lower_program(
                &parse_canonical_binary(black_box(&visible)).unwrap(),
            ));
            black_box(program.execute(&mut Session::default()).unwrap());
        }
        let decode_ns = measure(
            || {
                black_box(zig_transport::decode_t5m_words(black_box(bytes)).unwrap());
            },
            iterations,
        );
        let admission_ns = measure(
            || {
                black_box(PhysicalT5Program::from_exact_words(black_box(&words)).unwrap());
            },
            iterations,
        );
        let direct_ns = measure(
            || {
                black_box(reference_t5m::program(black_box(bytes)).unwrap());
            },
            iterations,
        );
        let visible_ns = measure(
            || {
                black_box(lower_program(
                    &parse_canonical_binary(black_box(&visible)).unwrap(),
                ));
            },
            iterations,
        );
        // Warm cached AST with a persistent session. In particular, do NOT
        // include construction/bootstrap of the runtime in this lane.
        let mut warmed_session = Session::default();
        let cached_ns = measure(
            || {
                black_box(program.execute(black_box(&mut warmed_session)).unwrap());
            },
            iterations,
        );
        println!(
            "{label},{},{},{decode_ns:.2},{admission_ns:.2},{direct_ns:.2},{visible_ns:.2},{cached_ns:.2}",
            bytes.len(),
            program.form_count()
        );
    }
}
