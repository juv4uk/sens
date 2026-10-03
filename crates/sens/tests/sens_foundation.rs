//! Domain-era foundation for canonical callable identity (#2817/#2821).
//!
//! The old Sens8/Sid8 model survives only as explicit compatibility payload.
//! Core identity is domain-qualified: equal packed bits in D3/D4/D5/D6 are
//! different semantic identities.

use sens::{
    Bija3, Bit3, Bit4, Bit5, CallableIdentity, CoreD4, CoreD5, CoreDomainIdentity,
};

#[test]
fn equal_payloads_in_different_domains_are_not_equal() {
    let d3 = CallableIdentity::core(CoreDomainIdentity::from(
        Bija3::from_word(Bit3::new(1).unwrap()),
    ));
    let d4 = CallableIdentity::core(CoreDomainIdentity::from(
        CoreD4::from_word(Bit4::new(1).unwrap()),
    ));
    let d5 = CallableIdentity::core(CoreDomainIdentity::from(
        CoreD5::from_word(Bit5::new(1).unwrap()),
    ));

    assert_eq!(d3.packed_bits(), 1);
    assert_eq!(d4.packed_bits(), 1);
    assert_eq!(d5.packed_bits(), 1);
    assert_ne!(d3, d4);
    assert_ne!(d3, d5);
    assert_ne!(d4, d5);
}

#[test]
fn exact_width_is_part_of_core_identity() {
    let d3 = CallableIdentity::core(CoreDomainIdentity::from(
        Bija3::from_word(Bit3::new(0b101).unwrap()),
    ));
    let d4 = CallableIdentity::core(CoreDomainIdentity::from(
        CoreD4::from_word(Bit4::new(0b0101).unwrap()),
    ));
    let d5 = CallableIdentity::core(CoreDomainIdentity::from(
        CoreD5::from_word(Bit5::new(0b00101).unwrap()),
    ));

    assert_eq!(d3.exact_width(), 3);
    assert_eq!(d4.exact_width(), 4);
    assert_eq!(d5.exact_width(), 5);
    assert_eq!(d3.to_string(), "101");
    assert_eq!(d4.to_string(), "0101");
    assert_eq!(d5.to_string(), "00101");
}

#[test]
fn historical_eight_bit_payload_never_aliases_core_identity() {
    let core = CallableIdentity::core(CoreDomainIdentity::from(
        Bija3::from_word(Bit3::new(0b101).unwrap()),
    ));
    let legacy = CallableIdentity::legacy8(0b0000_0101);

    assert_eq!(core.packed_bits(), legacy.packed_bits());
    assert_ne!(core, legacy);
    assert_eq!(core.legacy8_bits(), None);
    assert_eq!(legacy.legacy8_bits(), Some(0b0000_0101));
}

#[test]
fn compatibility_payload_is_not_a_core_domain() {
    let legacy = CallableIdentity::legacy8(0b1111_1111);
    assert_eq!(legacy.exact_width(), 8);
    assert_eq!(legacy.core_identity(), None);
    assert_eq!(legacy.to_string(), "11111111");
}
