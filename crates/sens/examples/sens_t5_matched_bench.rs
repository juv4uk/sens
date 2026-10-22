//! SENS T5 matched mechanical benchmark (manual, release).
//! Third track next to zig/rust. Same exact physical T5 words, but the encode
//! and decode path is OUR SENS-owned codec semantics (т5-тріти-списку,
//! т5-заповнити, т5-накопичити, т5-з-байтів): trits = (separator 2 between
//! words) + bits, pad the tail with trit 2 to a multiple of 5, fold 5 trits
//! LEFT-to-RIGHT into one byte. Transport benchmarking only, NOT a SENS
//! semantic oracle.
use std::hint::black_box;
use std::time::Instant;

use sens::{parse_binary_source_words, BinarySourceWord};

fn fnv64(bytes: &[u8]) -> u64 {
    bytes.iter().fold(0xcbf29ce484222325u64, |hash, byte| {
        (hash ^ u64::from(*byte)).wrapping_mul(0x100000001b3)
    })
}

/// Bits of one typed source word, most-significant first (exact width).
fn word_bits(w: BinarySourceWord) -> Vec<u8> {
    let width = w.width();
    let packed = w.packed_bits();
    (0..width)
        .rev()
        .map(|shift| ((packed >> shift) & 1) as u8)
        .collect()
}

/// SENS т5-тріти-списку + т5-заповнити: separator 2 between words, pad tail to %5.
fn sens_trits(words: &[BinarySourceWord]) -> Vec<u8> {
    let mut out = Vec::new();
    for (i, w) in words.iter().enumerate() {
        if i != 0 {
            out.push(2);
        }
        out.extend_from_slice(&word_bits(*w));
    }
    while out.len() % 5 != 0 {
        out.push(2);
    }
    out
}

/// SENS т5-накопичити (fold left-to-right) -> one byte per 5 trits.
fn sens_encode(words: &[BinarySourceWord]) -> Vec<u8> {
    let trits = sens_trits(words);
    trits
        .chunks(5)
        .map(|group| {
            let mut acc: u32 = 0;
            for &t in group {
                acc = acc * 3 + u32::from(t);
            }
            acc as u8
        })
        .collect()
}

/// SENS т5-з-байтів: bytes -> trits, strip trailing 2 -> list of bit words.
fn sens_decode(bytes: &[u8]) -> Vec<Vec<u8>> {
    let mut trits = Vec::with_capacity(bytes.len() * 5);
    for &b in bytes {
        let mut v = u32::from(b);
        let mut group = [0u8; 5];
        for i in (0..5).rev() {
            group[i] = (v % 3) as u8;
            v /= 3;
        }
        trits.extend_from_slice(&group);
    }
    while trits.last() == Some(&2) {
        trits.pop();
    }
    let mut words = Vec::new();
    let mut cur: Vec<u8> = Vec::new();
    for t in trits {
        if t == 2 {
            words.push(std::mem::take(&mut cur));
        } else {
            cur.push(t);
        }
    }
    if !cur.is_empty() {
        words.push(cur);
    }
    words
}

fn trial(
    operation: &str,
    words: &[BinarySourceWord],
    physical: &[u8],
    forms: usize,
    repetitions: usize,
) {
    let begin = Instant::now();
    for _ in 0..repetitions {
        match operation {
            "encode" => {
                black_box(sens_encode(black_box(words)));
            }
            "decode" => {
                black_box(sens_decode(black_box(physical)));
            }
            _ => panic!("unsupported benchmark operation"),
        }
    }
    let elapsed = begin.elapsed().as_nanos();
    println!(
        "sample impl=sens forms={} op={} elapsed_ns={} reps={}",
        forms, operation, elapsed, repetitions
    );
}

fn main() {
    let cases = [1usize, 16, 128, 1024];
    let reps = [12000usize, 3000, 600, 100];
    let pattern: Vec<BinarySourceWord> = parse_binary_source_words("10 100 01")
        .expect("typed binary test words")
        .into_iter()
        .map(|token| token.word)
        .collect();
    assert_eq!(pattern.len(), 3);
    for (forms, repetitions) in cases.into_iter().zip(reps) {
        let mut words = Vec::<BinarySourceWord>::with_capacity(forms * pattern.len());
        for _ in 0..forms {
            words.extend_from_slice(&pattern);
        }
        let physical = sens_encode(&words);
        let recovered = sens_decode(&physical);
        let expected: Vec<Vec<u8>> = words.iter().map(|w| word_bits(*w)).collect();
        assert_eq!(recovered, expected, "mechanical SENS T5 parity");
        println!(
            "fixture impl=sens forms={} words={} bytes={} fnv64={:x}",
            forms,
            words.len(),
            physical.len(),
            fnv64(&physical)
        );
        print!("physical impl=sens forms={} hex=", forms);
        for byte in &physical {
            print!("{byte:02x}");
        }
        println!();
        for _ in 0..3 {
            black_box(sens_encode(&words));
            black_box(sens_decode(&physical));
        }
        for _ in 0..5 {
            trial("encode", &words, &physical, forms, repetitions);
            trial("decode", &words, &physical, forms, repetitions);
        }
    }
}
