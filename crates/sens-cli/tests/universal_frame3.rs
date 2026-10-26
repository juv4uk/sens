//! Frame3 через фізичний Zig T5M — перенесено з crates/sens/src/universal_frame3.rs.
//!
//! Причина: `sens` тягнув `sens-cli` як dev-залежність, Cargo будував ДВІ копії
//! крейта `sens`, і `BinarySourceWord` у них ставав двома різними типами
//! (error[E0308] у universal_frame3.rs:378 і :381). Це валило збірку `sens`,
//! а з нею — карбування Core4 і весь реліз.
//!
//! Тут `zig_transport` рідний, цикл зникає, тип один.

use ::sens::universal_frame3::*;
use ::sens::*;

mod tests {
    use super::*;
    use ::sens::parse_binary_source_words;

    fn source(s: &str) -> Vec<BinarySourceWord> {
        parse_binary_source_words(s)
            .unwrap()
            .into_iter()
            .map(|t| t.word)
            .collect()
    }

    fn roundtrip(s: &str) {
        let words = source(s);
        let encoded = encode(&words).unwrap();
        assert_eq!(decode(&encoded).unwrap(), words);
        assert_eq!(encode(&decode(&encoded).unwrap()).unwrap(), encoded);
        for size in [1, 2, 3, 7, 64] {
            let mut reader = Frame3Decoder::new();
            for chunk in encoded.chunks(size) {
                reader.push(chunk).unwrap();
            }
            assert_eq!(reader.finish().unwrap(), words);
        }
        for end in 0..encoded.len() {
            assert!(decode(&encoded[..end]).is_err(), "truncation at {end}");
        }
        let mut added = encoded.clone();
        added.push(0);
        assert!(decode(&added).is_err());
    }

    #[test]
    fn exact_widths_and_multiple_roots() {
        for sample in [
            "",
            "0",
            "1",
            "10 01",
            "10 001 01",
            "10 000000001 01",
            "10 111111111 01",
            "10 01 10 01",
            "10 0 01 10 1 01",
        ] {
            roundtrip(sample);
        }
        // D2:00 та D2:11 — структурні, НЕ окремі атоми.
        roundtrip("10 0 00 1 01");
        roundtrip("10 1 11 0 01");
        for width in [1, 3, 4, 5, 6, 7, 8, 9] {
            let word = "0".repeat(width);
            roundtrip(&word);
            let max = "1".repeat(width);
            roundtrip(&max);
        }
    }

    #[test]
    fn long_repeats_and_mixed_byte_blocks() {
        let mut text = String::from("10 ");
        for _ in 0..150 {
            text.push_str("000000001 ");
        }
        text.push_str("01");
        roundtrip(&text);
        let words = source(&text);
        let data = encode(&words).unwrap();
        assert!(data.contains(&1));
    }

    #[test]
    fn physical_overhead_and_corruption() {
        let bytes = encode(&source("10 001 01")).unwrap();
        assert_eq!(&bytes[..3], &[b'S', b'3', 1]);
        for i in 0..bytes.len() {
            let mut damaged = bytes.clone();
            damaged[i] ^= 0x40;
            assert!(decode(&damaged).is_err(), "mutation at {i}");
        }
    }

    #[test]
    fn e1_zig_shared_raw_physical_golden_bytes_only() {
        // Cross-implementation physical fixture, not a Rust semantic verdict.
        let words = source("10 001 01");
        let bytes = [
            0x53, 0x33, 0x01, 0x03, 0x00, 0x03, 0x23, 0x20, 0x8a, 0x36, 0x20, 0x5d, 0x52,
        ];
        assert_eq!(encode(&words).unwrap(), bytes);
        assert_eq!(decode(&bytes).unwrap(), words);
    }

    #[test]
    fn e1_zig_rust_shared_physical_corpus() {
        // Independent byte parity ONLY: native binary SENS owns admission/eval.
        let corpus = include_str!(concat!(
            env!("CARGO_MANIFEST_DIR"),
            "/../../research/zig-codecs/transport/fixtures/e1-v1.bits"
        ));
        let mut tested = 0;
        for line in corpus
            .lines()
            .filter(|s| !s.is_empty() && !s.starts_with('#'))
        {
            let mut columns = line.split('|');
            let label = columns.next().expect("corpus case");
            let bits = columns.next().expect("exact binary words");
            let hex = columns.next().expect("physical E1 carrier hex");
            assert!(columns.next().is_none(), "too many columns case={label}");
            assert_eq!(hex.len() % 2, 0, "odd hex case={label}");
            let expected = hex
                .as_bytes()
                .as_chunks::<2>()
                .0
                .iter()
                .map(|pair| {
                    let digits = std::str::from_utf8(pair).expect("physical hex ASCII");
                    u8::from_str_radix(digits, 16).expect("valid physical hex")
                })
                .collect::<Vec<_>>();
            let words = source(bits);
            let actual = encode(&words).expect("physical encoder accepts corpus");
            if actual != expected {
                let offset = actual
                    .iter()
                    .zip(&expected)
                    .position(|(left, right)| left != right)
                    .unwrap_or_else(|| actual.len().min(expected.len()));
                panic!(
                    "E1_BYTE_PARITY_FAIL case={label} first_diff_offset={offset} \
                     expected_len={} actual_len={} expected={expected:02x?} actual={actual:02x?}",
                    expected.len(),
                    actual.len()
                );
            }
            assert_eq!(
                decode(&expected).expect("Rust physical decode+canonical roundtrip"),
                words,
                "E1_DECODE_MISMATCH case={label}"
            );
            tested += 1;
        }
        assert_eq!(tested, 16, "corpus lost fixtures");
    }

    /// Exact physical sizes for the same 16 verified E1 carrier vectors.
    /// These are bytes, NOT throughput, execution cost or semantic authority.
    /// F3C eligibility is decided by the existing explicit tiny program
    /// codec, not silently projected to zero or to an E1/T5 length.
    #[test]
    fn e1_t5_exact_physical_size_matrix() {

        let corpus = include_str!(concat!(
            env!("CARGO_MANIFEST_DIR"),
            "/../../research/zig-codecs/transport/fixtures/e1-v1.bits"
        ));
        let mut cases = 0usize;
        let mut total_e1 = 0usize;
        let mut total_t5 = 0usize;
        let mut t5_cases = 0usize;
        let mut e1_smaller = 0usize;
        let mut t5_smaller = 0usize;
        let mut equal = 0usize;

        for line in corpus
            .lines()
            .filter(|line| !line.is_empty() && !line.starts_with('#'))
        {
            let mut parts = line.split('|');
            let label = parts.next().expect("fixture label");
            let binary = parts.next().expect("exact-width binary fixture");
            let expected_hex = parts.next().expect("canonical E1 hex");
            assert!(parts.next().is_none(), "fixture has extra columns: {label}");
            let words = source(binary);
            let bits: usize = words.iter().map(|w| w.width()).sum();
            let physical_e1 = encode(&words).expect("admitted E1 fixture");
            let encoded_hex = physical_e1
                .iter()
                .map(|byte| format!("{byte:02x}"))
                .collect::<String>();
            assert_eq!(encoded_hex, expected_hex, "E1 fixture changed: {label}");
            assert_eq!(
                decode(&physical_e1).unwrap(),
                words,
                "E1 width loss: {label}"
            );

            let t5 = sens_cli::zig_transport::encode_t5m_direct(&words)
                .ok()
                .filter(|bytes| {
                    sens_cli::zig_transport::decode_t5m_words(bytes)
                        .is_ok_and(|recovered| recovered == words)
                });
            let t5_bytes = t5.as_ref().map(|v| v.len());
            let size_repr =
                |n: Option<usize>| n.map_or_else(|| "NA".to_string(), |size| size.to_string());
            println!(
                "E1_T5_SIZE_RECORD case={label} words={} exact_bits={} e1_bytes={} t5_bytes={}",
                words.len(), bits, physical_e1.len(), size_repr(t5_bytes)
            );
            total_e1 += physical_e1.len();
            if let Some(t5_size) = t5_bytes {
                t5_cases += 1;
                total_t5 += t5_size;
                if physical_e1.len() < t5_size {
                    e1_smaller += 1;
                } else if physical_e1.len() > t5_size {
                    t5_smaller += 1;
                } else {
                    equal += 1;
                }
            }
            cases += 1;
        }
        // Independent tiny T5M witness: compare only canonical physical E1/T5 bytes.
        // The retired Rust F3 reference transport is deliberately not part of this test.
        let tiny_t5 = [0x63, 0x89, 0x06, 0xa1];
        let tiny_words = sens_cli::zig_transport::decode_t5m_words(&tiny_t5)
            .expect("canonical tiny T5M fixture must decode exactly");
        let e1_tiny = encode(&tiny_words).expect("E1 physical carrier for tiny fixture");
        assert_eq!(decode(&e1_tiny).unwrap(), tiny_words);
        assert_eq!(
            sens_cli::zig_transport::encode_t5m_direct(&tiny_words).unwrap(),
            tiny_t5
        );
        let tiny_bits: usize = tiny_words.iter().map(|word| word.width()).sum();
        println!(
            "E1_T5_TINY case=admitted_quote words={} exact_bits={} e1_bytes={} t5_bytes=4 semantic_authority=SENS",
            tiny_words.len(),
            tiny_bits,
            e1_tiny.len()
        );
        assert_eq!(
            cases, 16,
            "the fixed byte parity corpus cannot silently shrink"
        );
        assert_eq!(e1_smaller + t5_smaller + equal, t5_cases);
        println!(
            "E1_SIZE_SUMMARY cases={cases} t5_representable={t5_cases} \
             sum_e1_bytes={total_e1} sum_t5_comparable_bytes={total_t5} \
             e1_smaller={e1_smaller} t5_smaller={t5_smaller} equal={equal} \
             speed=NOT_MEASURED semantic_authority=SENS"
        );
    }

    #[test]
    fn wrong_d2_rejected() {
        assert_eq!(encode(&source("01")), Err(Frame3Error::InvalidD2));
        assert_eq!(encode(&source("10")), Err(Frame3Error::InvalidD2));
        assert_eq!(
            decode(b"T5 not a universal frame"),
            Err(Frame3Error::BadVersion)
        );
    }

    #[test]
    fn oversized_chunk_poisoned_stream() {
        let valid = encode(&source("0")).unwrap();
        let mut decoder = Frame3Decoder::new();
        decoder.push(&valid).unwrap();
        assert_eq!(
            decoder.push(&vec![0; 1 << 20]),
            Err(Frame3Error::TooLarge)
        );
        assert_eq!(decoder.finish(), Err(Frame3Error::TooLarge));
    }


}