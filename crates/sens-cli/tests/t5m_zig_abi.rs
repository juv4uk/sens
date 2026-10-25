//! Перевіряє фізичний T5M через справжній Zig ABI, не через Python-копію.
//! Ширина лишається частиною точного слова; транспорт не визначає семантику.

use sens_cli::zig_transport::{decode_t5m_exact_words, encode_t5m_exact_words, ExactT5MWord};

fn word(width: usize, bits: impl IntoIterator<Item = u8>) -> ExactT5MWord {
    ExactT5MWord::new(width, bits.into_iter().collect()).expect("valid exact-width bits")
}

#[test]
fn zig_t5m_abi_preserves_arbitrary_widths_bits_and_leading_zeroes() {
    let mut source = Vec::new();
    for width in [1, 2, 7, 9, 10, 11, 12, 14, 24, 25, 48, 96, 192, 384] {
        source.push(word(width, std::iter::repeat_n(0, width)));

        let mut high_bit = vec![0; width];
        high_bit[0] = 1;
        source.push(word(width, high_bit));

        let mut low_bit = vec![0; width];
        low_bit[width - 1] = 1;
        source.push(word(width, low_bit));

        source.push(word(width, std::iter::repeat_n(1, width)));
    }

    let physical = encode_t5m_exact_words(&source).expect("Zig T5M ABI encode");
    let restored = decode_t5m_exact_words(&physical).expect("Zig T5M ABI decode");
    assert_eq!(restored, source);

    let one = [word(1, [1])];
    assert_eq!(encode_t5m_exact_words(&one).unwrap(), [0xa1]);

    let fixture = [
        word(2, [1, 0]),
        word(3, [0, 0, 1]),
        word(2, [0, 0]),
        word(3, [0, 0, 0]),
        word(2, [0, 1]),
    ];
    assert_eq!(
        encode_t5m_exact_words(&fixture).unwrap(),
        [0x63, 0x89, 0x06, 0xa1]
    );
}

#[test]
fn zig_t5m_abi_rejects_malformed_physical_inputs() {
    for invalid in [
        &[][..],
        &[0xf3][..],
        &[0xf2][..],
        &[0xa2][..],
        &[0xa1, 0xf2][..],
    ] {
        assert!(
            decode_t5m_exact_words(invalid).is_err(),
            "malformed T5M accepted: {invalid:02x?}"
        );
    }
}

#[test]
fn exact_t5m_word_constructor_rejects_invalid_width_and_bits() {
    assert!(ExactT5MWord::new(0, vec![]).is_err());
    assert!(ExactT5MWord::new(2, vec![1]).is_err());
    assert!(ExactT5MWord::new(1, vec![2]).is_err());
}
