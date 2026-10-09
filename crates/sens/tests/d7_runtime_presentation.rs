//! Physical W7 and human D7 projection, without Rust-authored resident meanings.
//! Name content and the two reserved coordinates are verified from Lisp-owned
//! authority by scripts/check-d7-runtime-projection.py, not asserted here.

use sens::{
    Bit7, BinarySourceWord, DomainIdentity, PresentationLanguage, Value,
    render_value_for_presentation,
};

#[test]
fn exact_d7_is_human_presentable_without_gaining_callability() {
    let mut displayed = 0usize;
    for raw in 0u8..=127 {
        let word = BinarySourceWord::W7(Bit7::new(raw).unwrap());
        let identity = DomainIdentity::from_source_word(word);
        assert_eq!(identity.width(), 7);
        assert_eq!(identity.packed_bits(), u16::from(raw));
        assert_eq!(identity.source_word(), word);
        assert_eq!(identity.core_operation(), None, "D7 width cannot create a callable function");

        let value = Value::DomainIdentity(identity);
        let exact = format!("{raw:07b}");
        assert_eq!(value.to_string(), exact);
        assert_eq!(render_value_for_presentation(&value, PresentationLanguage::Canonical), exact);
        assert_eq!(render_value_for_presentation(&value, PresentationLanguage::English), exact);

        let uk = render_value_for_presentation(&value, PresentationLanguage::Ukrainian);
        let sa = render_value_for_presentation(&value, PresentationLanguage::Sanskrit);
        if sa != exact {
            displayed += 1;
            assert!(!uk.is_empty(), "D7 human display cannot be empty");
            assert_ne!(uk, format!("#<домен {exact}>"), "D7 display must have matching UK/SA entries");
        } else {
            assert_eq!(uk, format!("#<домен {exact}>"), "unadmitted W7 must render as exact identity");
        }
    }
    assert!(displayed > 0, "ratified D7 must be reflected in human presentation");
}

#[test]
fn d7_and_same_payload_d8_keep_separate_physical_identifiers() {
    let d7 = DomainIdentity::from_source_word(BinarySourceWord::W7(Bit7::new(1).unwrap()));
    let d8 = DomainIdentity::from_source_word(
        BinarySourceWord::W8(sens::Bit8::new(1).unwrap())
    );
    assert_ne!(d7, d8);
    assert_eq!((d7.width(), d7.packed_bits()), (7, 1));
    assert_eq!((d8.width(), d8.packed_bits()), (8, 1));
}
