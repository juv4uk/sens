// D11 families: fixed workloads shared with the Zig implementation.
// Timed boundary: operation bundle only; reusable fixed buffers; no heap allocation.
// SENS owns the language law. This program measures Rust mechanics only.
use std::env;
use std::hint::black_box;
use std::os::raw::{c_int, c_long};

const SAMPLE_COUNT: usize = 15;
const MIN_SAMPLE_NS: u64 = 2_000_000;
const MAX_REPETITIONS: usize = 1 << 20;
const CLOCK_MONOTONIC: c_int = 1;

#[repr(C)]
struct Timespec {
    tv_sec: c_long,
    tv_nsec: c_long,
}

#[link(name = "c")]
extern "C" {
    fn clock_gettime(clock_id: c_int, tp: *mut Timespec) -> c_int;
}

fn now_ns() -> u64 {
    let mut ts = Timespec { tv_sec: 0, tv_nsec: 0 };
    let status = unsafe { clock_gettime(CLOCK_MONOTONIC, &mut ts) };
    assert_eq!(status, 0, "clock_gettime(CLOCK_MONOTONIC) failed");
    (ts.tv_sec as u64) * 1_000_000_000 + ts.tv_nsec as u64
}

#[derive(Default)]
struct Workspace {
    filtered: [i64; 8],
    keys: [i64; 8],
    counts: [usize; 8],
}

fn filter_equal(xs: &[i64], predicate: i64, output: &mut [i64]) -> usize {
    output.fill(0);
    let mut count = 0;
    for &value in xs {
        if value == predicate {
            output[count] = value;
            count += 1;
        }
    }
    count
}

fn alist_lookup(key: i64, rows: &[(i64, i64)]) -> Option<(i64, i64)> {
    rows.iter().copied().find(|&(candidate, _)| candidate == key)
}

fn frequencies(xs: &[i64], keys: &mut [i64], counts: &mut [usize]) -> usize {
    keys.fill(0);
    counts.fill(0);
    let mut distinct = 0;
    for &value in xs {
        if let Some(index) = keys[..distinct].iter().position(|&key| key == value) {
            counts[index] += 1;
        } else {
            keys[distinct] = value;
            counts[distinct] = 1;
            distinct += 1;
        }
    }
    distinct
}

fn once(xs: &[i64], alist: &[(i64, i64)], work: &mut Workspace) -> usize {
    let filtered = filter_equal(black_box(xs), 1, &mut work.filtered);
    let found = alist_lookup(2, black_box(alist));
    let distinct = frequencies(xs, &mut work.keys, &mut work.counts);
    black_box(&work.filtered[..filtered]);
    black_box(&work.keys[..distinct]);
    black_box(&work.counts[..distinct]);
    black_box(found);
    filtered + usize::from(found.is_some()) + distinct
}

fn preflight() {
    let xs = [1i64, 2, 1, 3, 1, 4, 1];
    let alist = [(1i64, 10i64), (2, 20), (3, 30)];
    let mut work = Workspace::default();
    let filtered = filter_equal(&xs, 1, &mut work.filtered);
    assert_eq!(filtered, 4, "FILTER count");
    assert_eq!(&work.filtered[..filtered], &[1, 1, 1, 1], "FILTER values");
    assert_eq!(alist_lookup(2, &alist), Some((2, 20)), "ASSOC first exact pair");
    let distinct = frequencies(&xs, &mut work.keys, &mut work.counts);
    assert_eq!(distinct, 4, "FREQUENCIES distinct count");
    assert_eq!(&work.keys[..distinct], &[1, 2, 3, 4], "FREQUENCIES key order");
    assert_eq!(&work.counts[..distinct], &[4, 1, 1, 1], "FREQUENCIES values");
    assert_eq!(filtered + 1 + distinct, 9, "shared checksum");
    println!("D11_FAMILIES_PREFLIGHT impl=rust filtered=4 assoc_value=20 distinct=4 counts=4,1,1,1 checksum=9 allocations=0");
}

fn run_sample(sample: usize) {
    assert!(sample < SAMPLE_COUNT, "sample index out of range");
    let xs = black_box([1i64, 2, 1, 3, 1, 4, 1]);
    let alist = black_box([(1i64, 10i64), (2, 20), (3, 30)]);
    let mut work = Workspace::default();

    let mut warm_sink = 0usize;
    for _ in 0..4 {
        warm_sink += once(&xs, &alist, &mut work);
    }
    black_box(warm_sink);

    let mut repetitions = 1usize;
    loop {
        let start = now_ns();
        let mut sink = 0usize;
        for _ in 0..repetitions {
            sink += once(&xs, &alist, &mut work);
        }
        black_box(sink);
        let elapsed = now_ns() - start;
        if elapsed >= MIN_SAMPLE_NS || repetitions >= MAX_REPETITIONS {
            println!(
                "D11_FAMILIES_SAMPLE impl=rust sample={} reps={} ns_per_round={} checksum={} allocations=0",
                sample,
                repetitions,
                std::cmp::max(1, elapsed / repetitions as u64),
                sink / repetitions
            );
            return;
        }
        repetitions = (repetitions * 2).min(MAX_REPETITIONS);
    }
}

fn main() {
    if env::var("D11_FAMILIES_PREFLIGHT_ONLY").map(|value| value == "1").unwrap_or(false) {
        preflight();
        return;
    }
    if let Ok(raw) = env::var("D11_FAMILIES_SAMPLE") {
        let sample = raw.parse::<usize>().expect("D11_FAMILIES_SAMPLE must be an integer");
        run_sample(sample);
        return;
    }
    preflight();
    for sample in 0..SAMPLE_COUNT {
        run_sample(sample);
    }
}
