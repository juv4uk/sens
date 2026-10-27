//! Тільки фізична T5M ідентичність та межа канонічного двійкового читача.
//! Результати QUOTE/COND/D1 перевіряє SENS, не Rust.
use sens::{parse_canonical_packed_words, BitPacker};
use sens_cli::zig_transport;

const SOURCE: &str = include_str!("../../../tests/fixtures/migration-multiform-cohort-main/two-forms.lisp");
const MULTIFORM_T5M: &[u8] = include_bytes!("../../../tests/fixtures/migration-multiform-cohort-main/two-forms.sens");

fn decode_t5m_via_zig(bytes: &[u8]) -> Result<Vec<sens::BinarySourceWord>, String> {
    zig_transport::decode_t5m_words(bytes)
}

#[test]
fn physical_domain_words_share_exact_d2_grammar_with_visible_reference() {
    let words = decode_t5m_via_zig(MULTIFORM_T5M).expect("canonical physical T5M");
    let mut packer = BitPacker::new();
    for word in words.iter().copied() {
        sens::append_binary_source_word(&mut packer, word);
    }
    let widths = words.iter().map(|word| word.width()).collect::<Vec<_>>();
    let physical =
        parse_canonical_packed_words(&packer.finish(), &widths).expect("typed binary reader");
    let visible = sens::parse_mixed_exact_domain(SOURCE)
        .expect("canonical Ukrainian source parsed directly by SENS");
    assert_eq!(physical.len(), visible.len());
    for (from_bytes, from_reference) in physical.iter().zip(visible.iter()) {
        let left = sens::lower_program(std::slice::from_ref(from_bytes));
        let right = sens::lower_program(std::slice::from_ref(from_reference));
        assert_eq!(
            sens::expr_to_exact_program_data(&left[0]).unwrap(),
            sens::expr_to_exact_program_data(&right[0]).unwrap(),
            "physical and visible views must preserve identical exact domain identities"
        );
    }
}

#[test]
fn named_lisp_cannot_enter_canonical_binary_reader() {
    let err =
        sens::parse_canonical_binary("(quote ())").expect_err("human Lisp names are not physical source");
    assert_eq!(err.kind, sens::ErrorKind::Parse);
}
