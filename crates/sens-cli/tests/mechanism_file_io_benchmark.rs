//! Діагностичний Rust-бенчмарк механізму читання байтів, а не Lisp-семантики.
//! Програма SENS є непрозорими байтами: жодних D1-очікувань у Rust.
use std::hint::black_box;
use std::path::PathBuf;
use std::time::Instant;

const REPEATS: usize = 11;

fn source_file() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .join("../..")
        .join("benchmarks/lists.lisp")
}

fn median_and_p90(mut elapsed_ns: [u128; REPEATS]) -> (u128, u128) {
    elapsed_ns.sort_unstable();
    (elapsed_ns[REPEATS / 2], elapsed_ns[9])
}

#[test]
#[ignore = "діагностичний IO benchmark: запускати явно, не як мовний тест"]
fn rust_mechanism_read_real_lisp_bytes() {
    let path = source_file();
    let reference = std::fs::read(&path).expect("вхідний Lisp-файл існує");
    assert!(!reference.is_empty(), "порожній файл не є бенчмарком IO");
    // Розігрів: тільки Rust fs::read, без виклику SENS або інших мов.
    for _ in 0..3 {
        let bytes = std::fs::read(black_box(&path)).expect("Rust IO warmup");
        assert_eq!(bytes, reference, "Rust IO зберігає кожен байт");
    }
    let mut samples = [0_u128; REPEATS];
    for sample in &mut samples {
        let began = Instant::now();
        let bytes = std::fs::read(black_box(&path)).expect("Rust IO read");
        *sample = began.elapsed().as_nanos();
        assert_eq!(bytes, reference, "байти файлу зобов'язані збігатися");
        black_box(bytes);
    }
    let (p50, p90) = median_and_p90(samples);
    eprintln!(
        "RUST_MECHANISM_BENCH id=fs-read-lisp samples={} p50_ns={} p90_ns={} bytes={} scope=warm-cache-file-io semantics=NOT_TESTED status=MEASURED",
        REPEATS, p50, p90, reference.len()
    );
}

#[test]
fn rust_mechanism_quantiles_are_order_statistic_not_semantic_oracle() {
    let samples: [u128; REPEATS] = [9, 1, 3, 10, 11, 4, 2, 8, 5, 7, 6];
    let (p50, p90) = median_and_p90(samples);
    assert_eq!(p50, 6);
    assert_eq!(p90, 10);
}
