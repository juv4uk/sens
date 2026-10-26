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
    fn encode_ternary_words(words: &[::sens::BinarySourceWord]) -> Result<Vec<u8>, String> {
        sens_cli::zig_transport::encode_t5m_direct(words)
    }
    fn decode_ternary_words(bytes: &[u8]) -> Result<Vec<::sens::BinarySourceWord>, String> {
        sens_cli::zig_transport::decode_t5m_words(bytes)
    }

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
        assert!(data.contains(&REPEAT));
    }

    #[test]
    fn physical_overhead_and_corruption() {
        let bytes = encode(&source("10 001 01")).unwrap();
        assert_eq!(&bytes[..3], &MAGIC);
        assert_eq!(
            physical_crc32(&bytes[..bytes.len() - 4]).to_be_bytes(),
            bytes[bytes.len() - 4..]
        );
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
                .chunks_exact(2)
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
    #[cfg(feature = "rust-f3-reference")]
    #[test]
    fn e1_t5_f3c_exact_physical_size_matrix() {

        let corpus = include_str!(concat!(
            env!("CARGO_MANIFEST_DIR"),
            "/../../research/zig-codecs/transport/fixtures/e1-v1.bits"
        ));
        let mut cases = 0usize;
        let mut total_e1 = 0usize;
        let mut total_t5 = 0usize;
        let mut t5_cases = 0usize;
        let mut f3c_cases = 0usize;
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

            let t5 = encode_ternary_words(&words).ok().filter(|bytes| {
                decode_ternary_words(bytes).is_ok_and(|recovered| recovered == words)
            });
            let f3c = t5.as_ref().and_then(|bytes| {
                ::sens::frame3_small::encode_explicit_small_f3(bytes)
                    .ok()
                    .flatten()
                    .filter(|packed| {
                        ::sens::frame3_small::decode_explicit_small_f3(packed)
                            .is_ok_and(|recovered| recovered == *bytes)
                    })
            });
            let t5_bytes = t5.as_ref().map(|v| v.len());
            let f3c_bytes = f3c.as_ref().map(|v| v.len());
            let size_repr =
                |n: Option<usize>| n.map_or_else(|| "NA".to_string(), |size| size.to_string());
            println!(
                "E1_SIZE_RECORD case={label} words={} exact_bits={bits} e1_bytes={} t5_bytes={} f3c_bytes={}",
                words.len(), physical_e1.len(), size_repr(t5_bytes), size_repr(f3c_bytes)
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
            if f3c_bytes.is_some() {
                f3c_cases += 1;
            }
            cases += 1;
        }
        // A separately proven SENS tiny F3C witness is included to avoid
        // claiming F3C lacks useful cases just because the fixed E1 set has none.
        // This is NOT a 17th case in the immutable E1 byte-parity corpus.
        let tiny_t5 = [0x63, 0x89, 0x06, 0xa1];
        let tiny_f3c = [0xf3, 0x40, 0x60];
        let tiny_words =
            decode_ternary_words(&tiny_t5).expect("original tiny SENS fixture must decode exactly");
        let e1_tiny = encode(&tiny_words).expect("E1 physical carrier for tiny fixture");
        assert_eq!(decode(&e1_tiny).unwrap(), tiny_words);
        assert_eq!(encode_ternary_words(&tiny_words).unwrap(), tiny_t5);
        assert_eq!(
            ::sens::frame3_small::encode_explicit_small_f3(&tiny_t5).unwrap(),
            Some(tiny_f3c.to_vec())
        );
        assert_eq!(
            ::sens::frame3_small::decode_explicit_small_f3(&tiny_f3c).unwrap(),
            tiny_t5
        );
        let tiny_bits: usize = tiny_words.iter().map(|word| word.width()).sum();
        println!(
            "E1_F3C_TINY_REFERENCE case=admitted_quote words={} exact_bits={} \
             e1_bytes={} t5_bytes=4 f3c_bytes=3 semantic_authority=SENS",
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
            "E1_SIZE_SUMMARY cases={cases} t5_representable={t5_cases} f3c_eligible={f3c_cases} \
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
    fn malformed_physical_aliases_rejected_even_with_matching_crc() {
        fn framed(mut payload: Vec<u8>) -> Vec<u8> {
            let crc = physical_crc32(&payload);
            payload.extend_from_slice(&crc.to_be_bytes());
            payload
        }
        // Той самий атом 0 у повторному режимі: неканонічний alias raw.
        let alias = framed(vec![b'S', b'3', 1, 1, REPEAT, 1, 1, 0]);
        assert_eq!(decode(&alias), Err(Frame3Error::NonCanonical));
        // Довжина 1, записана двома байтами, заборонена.
        let nonminimal = framed(vec![b'S', b'3', 1, 0x81, 0, RAW, 1, 0x10, 0]);
        assert_eq!(decode(&nonminimal), Err(Frame3Error::NonCanonical));
        // Додані padding bits є неканонічними, навіть із новим CRC.
        let padding = framed(vec![b'S', b'3', 1, 1, RAW, 1, 0x10, 1]);
        assert_eq!(decode(&padding), Err(Frame3Error::NonCanonical));
        // Exact-width D2 CLOSE не може бути самостійним верхнім виразом.
        let bad_d2 = framed(vec![b'S', b'3', 1, 1, RAW, 1, 0x20, 0x40]);
        assert_eq!(decode(&bad_d2), Err(Frame3Error::InvalidD2));
        let bad_tag = framed(vec![b'S', b'3', 1, 1, 0xff, 1, 0x10, 0]);
        assert_eq!(decode(&bad_tag), Err(Frame3Error::Malformed));
    }

    #[test]
    fn oversized_chunk_poisoned_stream() {
        let valid = encode(&source("0")).unwrap();
        let mut decoder = Frame3Decoder::new();
        decoder.push(&valid).unwrap();
        assert_eq!(
            decoder.push(&vec![0; MAX_FILE_BYTES]),
            Err(Frame3Error::TooLarge)
        );
        assert_eq!(decoder.finish(), Err(Frame3Error::TooLarge));
    }

    #[test]
    fn dp_matches_independent_bounded_enumeration() {
        fn brute(words: &[BinarySourceWord]) -> usize {
            if words.is_empty() {
                return 0;
            }
            let mut best = usize::MAX;
            for n in 1..=words.len().min(MAX_BLOCK_WORDS) {
                let chunk = &words[..n];
                let bits: usize = chunk.iter().map(|w| w.width()).sum();
                let raw = 1 + varint_len(n) + n.div_ceil(2) + bits.div_ceil(8);
                best = best.min(raw + brute(&words[n..]));
                if chunk.iter().all(|w| *w == chunk[0]) {
                    let run = 1 + varint_len(n) + 1 + chunk[0].width().div_ceil(8);
                    best = best.min(run + brute(&words[n..]));
                }
            }
            best
        }
        for width in 1..=9 {
            for n in 0..=7 {
                let words = std::iter::repeat(new_word(width, 0).unwrap())
                    .take(n)
                    .collect::<Vec<_>>();
                assert_eq!(choose_plan(&words)[0].bytes, brute(&words));
            }
        }
    }
}