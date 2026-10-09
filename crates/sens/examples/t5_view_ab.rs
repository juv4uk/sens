//! Same-SHA, same-run ABBA benchmark of visible exact-width word rendering.
//! Comparison is only projection, NOT D2 decoding or evaluation.
//! Run: cargo run --release --locked -p sens --example t5_view_ab -- OUTPUT_DIRECTORY

use std::{env, fs, hint::black_box, path::PathBuf, time::Instant};

const WARMUPS: usize = 4;
const REPS: usize = 25;
const SCALES: &[usize] = &[1, 128, 2048, 16384];
const SEED: &str = "10 001 00 000 01";

fn allocating_reference(words: &[sens::BinarySourceWord]) -> String {
    words.iter().map(ToString::to_string).collect::<Vec<_>>().join(" ")
}

fn clock(words: &[sens::BinarySourceWord], streaming: bool) -> u128 {
    let started = Instant::now();
    let result = if streaming {
        sens::render_ternary_words_spaced(black_box(words))
    } else {
        allocating_reference(black_box(words))
    };
    black_box(result);
    started.elapsed().as_nanos()
}

fn median_p95(samples: &[u128]) -> (u128, u128) {
    let mut sorted = samples.to_vec();
    sorted.sort_unstable();
    let median = (sorted[(sorted.len() - 1) / 2] + sorted[sorted.len() / 2]) / 2;
    let p95_index = (95 * sorted.len()).div_ceil(100) - 1;
    (median, sorted[p95_index])
}

fn run() -> Result<(), Box<dyn std::error::Error>> {
    let out = match env::args_os().nth(1) {
        Some(dir) => PathBuf::from(dir),
        None => return Err("usage: t5_view_ab OUTPUT_DIRECTORY".into()),
    };
    fs::create_dir_all(&out)?;
    let seed: Vec<_> = sens::parse_binary_source_words(SEED)?
        .into_iter()
        .map(|token| token.word)
        .collect();

    let mut table = String::from(
        "| Copies | Typed words | Visible bytes | Old median ns | New median ns | \
         Old p95 ns | New p95 ns | Old/New ratio |\n\
         |---:|---:|---:|---:|---:|---:|---:|---:|\n",
    );
    let mut raw = String::from("copies\twords\tmethod\titeration\tsample\tns\n");
    for &copies in SCALES {
        let mut words = Vec::with_capacity(seed.len() * copies);
        for _ in 0..copies {
            words.extend_from_slice(&seed);
        }
        let baseline = allocating_reference(&words);
        let candidate = sens::render_ternary_words_spaced(&words);
        if baseline != candidate {
            return Err(format!("exact binary output mismatch for {copies} copies").into());
        }
        let physical = sens::encode_ternary_words(&words)?;
        let roundtrip = sens::decode_ternary_words(&physical)?;
        if roundtrip != words {
            return Err(format!("packed T5 roundtrip mismatch for {copies} copies").into());
        }
        let mut old = Vec::with_capacity(REPS * 2);
        let mut new = Vec::with_capacity(REPS * 2);
        for iteration in 0..(WARMUPS + REPS) {
            // A/B/B/A cancels first-order monotonic drift and cache-position bias.
            for (sample, streaming) in [false, true, true, false].into_iter().enumerate() {
                let ns = clock(&words, streaming);
                if iteration >= WARMUPS {
                    let method = if streaming { "single-buffer" } else { "allocating" };
                    raw.push_str(&format!(
                        "{copies}\t{}\t{method}\t{}\t{sample}\t{ns}\n",
                        words.len(),
                        iteration - WARMUPS
                    ));
                    if streaming {
                        new.push(ns);
                    } else {
                        old.push(ns);
                    }
                }
            }
        }
        let (old_median, old_p95) = median_p95(&old);
        let (new_median, new_p95) = median_p95(&new);
        // Ratio < 1 is reported as a regression; no invented speed claim.
        let ratio = old_median as f64 / (new_median.max(1) as f64);
        table.push_str(&format!(
            "| {copies} | {} | {} | {old_median} | {new_median} | \
             {old_p95} | {new_p95} | {ratio:.3} |\n",
            words.len(),
            baseline.len(),
        ));
    }
    let commit = env::var("GITHUB_SHA").unwrap_or_else(|_| "local-unpinned".into());
    let report = format!(
        "### D1–D9 exact-width view: paired ABBA rendering\n\n\
         SHA: {commit}. {} warmups, {} measured ABBA iterations per scale \
         ({} samples per method).\n\n\
         Output parity + packed T5 roundtrip admitted before timing. \
         Timed scope = visible text rendering only; no disk, D2 parse, \
         semantic evaluation, or language-wide speed claim.\n\n{}",
        WARMUPS, REPS, REPS * 2, table
    );
    fs::write(out.join("view-render-abba.tsv"), raw)?;
    fs::write(out.join("view-render-abba.md"), &report)?;
    print!("{report}");
    Ok(())
}

fn main() {
    if let Err(error) = run() {
        eprintln!("t5-view-ab: {error}");
        std::process::exit(1);
    }
}
