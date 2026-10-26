//! Діагностичний Rust-бенчмарк механізму читання байтів, а не Lisp-семантики.
//! Програма SENS є непрозорими байтами: жодних D1-очікувань у Rust.
use std::hint::black_box;
use std::path::PathBuf;
use std::time::{Duration, Instant};

const REPEATS: usize = 11;
const MIN_SAMPLE_TIME: Duration = Duration::from_millis(25);
const READS_PER_BATCH: usize = 16;

fn source_file() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .join("../..")
        .join("benchmarks/lists.lisp")
}

fn median_and_p90(mut ns_per_read: [u128; REPEATS]) -> (u128, u128) {
    ns_per_read.sort_unstable();
    (ns_per_read[REPEATS / 2], ns_per_read[9])
}

#[test]
#[ignore = "діагностичний IO benchmark: запускати явно, не як мовний тест"]
fn rust_mechanism_read_real_lisp_bytes() {
    let path = source_file();
    let reference = std::fs::read(&path).expect("вхідний Lisp-файл існує");
    assert!(!reference.is_empty(), "порожній файл не є бенчмарком IO");

    // Прогрів: тільки Rust fs::read, без виклику SENS або інших мов.
    for _ in 0..3 {
        let bytes = std::fs::read(black_box(&path)).expect("Rust IO warmup");
        assert_eq!(bytes, reference, "Rust IO зберігає кожен байт");
        black_box(bytes);
    }

    // Одна проба триває щонайменше 25 ms: одиничний швидкий read надто
    // чутливий до планувальника/таймера shared runner. Міряємо тільки
    // warm-cache file I/O; перевірка байтів не визначає семантику мови.
    let mut ns_per_read = [0_u128; REPEATS];
    for (sample, sample_ns_per_read) in ns_per_read.iter_mut().enumerate() {
        let began = Instant::now();
        let mut reads = 0_u64;
        let mut last_bytes = Vec::new();
        loop {
            for _ in 0..READS_PER_BATCH {
                // Рівність байтів перевіряється після таймера: у вимірі лишається
                // реальний fs::read + виділення/звільнення буфера, не assert_eq.
                last_bytes = black_box(
                    std::fs::read(black_box(&path)).expect("Rust IO read"),
                );
                reads += 1;
            }
            if began.elapsed() >= MIN_SAMPLE_TIME {
                break;
            }
        }

        let elapsed = began.elapsed().as_nanos();
        assert!(elapsed > 0 && reads > 0, "sample must have positive duration");
        assert_eq!(
            last_bytes, reference,
            "байти останнього прочитання зобов'язані збігатися"
        );
        *sample_ns_per_read = elapsed / u128::from(reads);
        eprintln!(
            "RUST_MECHANISM_SAMPLE id=fs-read-lisp sample={} elapsed_ns={} operations={} ns_per_read={} bytes={} scope=warm-cache-file-io",
            sample + 1, elapsed, reads, *sample_ns_per_read, reference.len()
        );
    }

    let (p50, p90) = median_and_p90(ns_per_read);
    let mut ordered = ns_per_read;
    ordered.sort_unstable();
    eprintln!(
        "RUST_MECHANISM_BENCH id=fs-read-lisp samples={} min_ns_per_read={} p50_ns_per_read={} p90_ns_per_read={} max_ns_per_read={} min_sample_ms={} reads_per_batch={} bytes={} warmup_reads=3 scope=warm-cache-file-io semantics=NOT_TESTED status=MEASURED",
        REPEATS, ordered[0], p50, p90, ordered[REPEATS - 1],
        MIN_SAMPLE_TIME.as_millis(), READS_PER_BATCH, reference.len()
    );
}

#[test]
fn rust_mechanism_quantiles_are_order_statistic_not_semantic_oracle() {
    let samples: [u128; REPEATS] = [9, 1, 3, 10, 11, 4, 2, 8, 5, 7, 6];
    let (p50, p90) = median_and_p90(samples);
    assert_eq!(p50, 6);
    assert_eq!(p90, 10);
}
