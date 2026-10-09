//! Rust знає лише механічну драбину доменів: точну ширину, payload і зворотне перетворення.
//! Закони resident-ів та значення бітів визначаються Lisp-контрактами SENS.

use sens::{
    Bit1, Bit2, Bit3, Bit4, Bit5, Bit6, Bit7, Bit8, Bit9, BinarySourceWord, DomainIdentity,
};

fn assert_ladder_round_trip(source: BinarySourceWord, width: usize, payload: u16) {
    assert_eq!(source.width(), width);
    assert_eq!(source.packed_bits(), payload);
    assert_eq!(source.to_string().len(), width);

    let identity = DomainIdentity::from_source_word(source);
    assert_eq!(identity.width(), width);
    assert_eq!(identity.packed_bits(), payload);
    assert_eq!(identity.source_word(), source);
}

#[test]
fn exact_width_ladder_round_trips_payloads_without_truncation() {
    for raw in 0..=1 {
        assert_ladder_round_trip(BinarySourceWord::W1(Bit1::new(raw).unwrap()), 1, raw as u16);
    }
    for raw in 0..=3 {
        assert_ladder_round_trip(BinarySourceWord::W2(Bit2::new(raw).unwrap()), 2, raw as u16);
    }
    for raw in 0..=7 {
        assert_ladder_round_trip(BinarySourceWord::W3(Bit3::new(raw).unwrap()), 3, raw as u16);
    }
    for raw in 0..=15 {
        assert_ladder_round_trip(BinarySourceWord::W4(Bit4::new(raw).unwrap()), 4, raw as u16);
    }
    for raw in 0..=31 {
        assert_ladder_round_trip(BinarySourceWord::W5(Bit5::new(raw).unwrap()), 5, raw as u16);
    }
    for raw in 0..=63 {
        assert_ladder_round_trip(BinarySourceWord::W6(Bit6::new(raw).unwrap()), 6, raw as u16);
    }
    for raw in 0..=127 {
        assert_ladder_round_trip(BinarySourceWord::W7(Bit7::new(raw).unwrap()), 7, raw as u16);
    }
    for raw in 0..=255 {
        assert_ladder_round_trip(BinarySourceWord::W8(Bit8::new(raw).unwrap()), 8, raw as u16);
    }
    for raw in 0..=511 {
        assert_ladder_round_trip(BinarySourceWord::W9(Bit9::new(raw).unwrap()), 9, raw);
    }
}

#[test]
fn same_payload_at_different_widths_keeps_distinct_domain_identity() {
    let d1 = BinarySourceWord::W1(Bit1::new(1).unwrap()).domain_identity();
    let d2 = BinarySourceWord::W2(Bit2::new(1).unwrap()).domain_identity();
    let d3 = BinarySourceWord::W3(Bit3::new(1).unwrap()).domain_identity();

    assert_eq!(d1.packed_bits(), d2.packed_bits());
    assert_eq!(d2.packed_bits(), d3.packed_bits());
    assert_ne!(d1, d2);
    assert_ne!(d2, d3);
    assert_ne!(d1, d3);
}

#[test]
fn width_carriers_reject_payloads_that_do_not_fit() {
    assert!(Bit1::new(2).is_none());
    assert!(Bit2::new(4).is_none());
    assert!(Bit3::new(8).is_none());
    assert!(Bit4::new(16).is_none());
    assert!(Bit5::new(32).is_none());
    assert!(Bit6::new(64).is_none());
    assert!(Bit7::new(128).is_none());
    assert!(Bit8::new(256).is_none());
    assert!(Bit9::new(512).is_none());
}
