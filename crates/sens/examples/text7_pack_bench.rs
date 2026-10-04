//! Benchmark the generic bit-by-bit packer against the block-specialized 7-bit codec.
//!
//! Run from the repository root:
//!   cargo run --release -p sens --example text7_pack_bench
//!
//! The benchmark excludes UTF-8->Text7 projection. Both paths receive the
//! same already-admitted 7-bit cells, isolating packing/unpacking.

use sens::{pack7_cells, unpack7_cells, Bit7, BitPacker, PackedBitstream};
use std::{fs, hint::black_box, time::Instant};

const CORPUS: &str = "docs/research/data/1700-uk-literals-vs-upc7.tsv";
const TARGET_ROWS: usize = 617;
const ROUNDS: usize = 10_000;

fn load_cells() -> Vec<Vec<u8>> {
    let text = fs::read_to_string(CORPUS).expect("read 1700-uk-literals-vs-upc7.tsv");
    let mut rows = Vec::with_capacity(TARGET_ROWS);

    for line in text.lines().skip(1) {
        let mut cols = line.split('\t');
        let _path = cols.next();
        let _line = cols.next();
        let result = cols.next();
        let _blocker = cols.next();
        let prefix = cols.next();

        if result == Some("encodes") {
            let prefix = prefix.expect("encoded row has literal_prefix");
            let cells = sens::encode_text7(prefix, sens::Text7Layout::Uk)
                .expect("corpus row marked encodes must admit as Ukrainian Text7");
            rows.push(cells.cells().to_vec());
            if rows.len() == TARGET_ROWS {
                break;
            }
        }
    }

    assert_eq!(rows.len(), TARGET_ROWS, "corpus must contain 617 admitted rows");
    rows
}

fn generic_pack(corpus: &[Vec<u8>]) -> Vec<PackedBitstream> {
    corpus
        .iter()
        .map(|cells| {
            let mut packer = BitPacker::with_capacity_bits(cells.len() * 7);
            for &cell in cells {
                packer.push(Bit7::new(cell).expect("canonical seven-bit cell"));
            }
            packer.finish()
        })
        .collect()
}

fn generic_unpack(packed: &[PackedBitstream]) -> usize {
    let mut checksum = 0usize;
    for stream in packed {
        for index in (0..stream.bit_len()).step_by(7) {
            checksum = checksum.wrapping_mul(131)
                ^ usize::from(stream.read::<7>(index).expect("cell").packed_bits());
        }
    }
    black_box(checksum);
    checksum
}

fn bulk_pack(corpus: &[Vec<u8>]) -> Vec<(Vec<u8>, usize)> {
    corpus
        .iter()
        .map(|cells| pack7_cells(cells).expect("canonical seven-bit cells"))
        .collect()
}

fn bulk_unpack(packed: &[(Vec<u8>, usize)]) -> usize {
    let mut checksum = 0usize;
    for (bytes, bit_len) in packed {
        for cell in unpack7_cells(bytes, *bit_len).expect("valid packed stream") {
            checksum = checksum.wrapping_mul(131) ^ usize::from(cell);
        }
    }
    black_box(checksum);
    checksum
}

fn median(values: &mut [f64]) -> f64 {
    values.sort_by(f64::total_cmp);
    values[values.len() / 2]
}

fn bench<F: Fn() -> usize>(f: F) -> f64 {
    let warmup = black_box(f());
    black_box(warmup);
    let mut samples = Vec::with_capacity(7);

    for _ in 0..7 {
        let start = Instant::now();
        let mut checksum = 0usize;
        for _ in 0..ROUNDS {
            checksum ^= black_box(f());
        }
        black_box(checksum);
        samples.push(start.elapsed().as_secs_f64() * 1e9 / ROUNDS as f64);
    }

    median(&mut samples)
}

fn main() {
    let corpus = load_cells();

    let generic = generic_pack(&corpus);
    let bulk = bulk_pack(&corpus);

    for (g, (bytes, bit_len)) in generic.iter().zip(&bulk) {
        assert_eq!(g.bytes(), bytes);
        assert_eq!(g.bit_len(), *bit_len);
    }

    let generic_pack_ns = bench(|| {
        let out = generic_pack(black_box(&corpus));
        black_box(out.iter().map(PackedBitstream::byte_len).sum())
    });
    let bulk_pack_ns = bench(|| {
        let out = bulk_pack(black_box(&corpus));
        black_box(out.iter().map(|(bytes, _)| bytes.len()).sum::<usize>())
    });

    let generic_unpack_ns = bench(|| generic_unpack(black_box(&generic)));
    let bulk_unpack_ns = bench(|| bulk_unpack(black_box(&bulk)));

    let total_bytes: usize = bulk.iter().map(|(bytes, _)| bytes.len()).sum();
    let total_cells: usize = corpus.iter().map(Vec::len).sum();

    println!("corpus_rows={TARGET_ROWS}");
    println!("total_cells={total_cells}");
    println!("packed_bytes={total_bytes}");
    println!("rounds={ROUNDS}");
    println!("generic_pack_ns_per_round={generic_pack_ns:.1}");
    println!("bulk_pack_ns_per_round={bulk_pack_ns:.1}");
    println!("pack_speedup={:.3}", generic_pack_ns / bulk_pack_ns);
    println!("generic_unpack_ns_per_round={generic_unpack_ns:.1}");
    println!("bulk_unpack_ns_per_round={bulk_unpack_ns:.1}");
    println!("unpack_speedup={:.3}", generic_unpack_ns / bulk_unpack_ns);
}
