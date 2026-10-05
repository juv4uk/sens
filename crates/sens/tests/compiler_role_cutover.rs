//! sens#3810 — SENS compiler role is authoritative; Rust role is oracle only.

use sens::{
    compiler_execution_role, compiler_execution_role_from_sens, Bija3, Bit3, Bit4, Bit8,
    CoreD4, CoreD8, CoreDomainIdentity,
};

fn d3(raw: u8) -> CoreDomainIdentity {
    CoreDomainIdentity::D3(Bija3::from_word(Bit3::new(raw).expect("D3 word")))
}

#[test]
fn language_role_matches_differential_oracle_for_every_d3_identity() {
    for raw in 0u8..=0b111 {
        let identity = d3(raw);
        let language = compiler_execution_role_from_sens(identity)
            .unwrap_or_else(|error| panic!("D3:{raw:03b} SENS role failed: {error:?}"));
        let oracle = compiler_execution_role(identity);
        assert_eq!(language, oracle, "D3:{raw:03b}");
    }
}

#[test]
fn wider_same_payload_does_not_gain_d3_role() {
    let d4 =
        CoreDomainIdentity::D4(CoreD4::from_word(Bit4::new(0b0100).expect("D4 exact word")));
    assert_eq!(compiler_execution_role_from_sens(d4).unwrap(), None);
}

#[test]
fn d8_research_coordinate_stays_fail_closed() {
    let d8 =
        CoreDomainIdentity::D8(CoreD8::from_word(Bit8::new(0b0000_0100).expect("D8 word")));
    assert_eq!(compiler_execution_role_from_sens(d8).unwrap(), None);
}

#[test]
fn production_adapter_does_not_call_the_rust_identity_to_role_oracle() {
    let source = include_str!("../src/compiler_language.rs");
    assert!(
        !source.contains("crate::compiler_execution_role("),
        "production adapter must not delegate identity->role back to Rust oracle"
    );
    for forbidden in ["0b100", "0b011", "0b111"] {
        assert!(
            !source.contains(forbidden),
            "production adapter must not contain D3 semantic coordinates: {forbidden}"
        );
    }
}
