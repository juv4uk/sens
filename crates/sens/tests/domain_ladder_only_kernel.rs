//! Mechanical retirement guard. Rust carries exact domain identifiers;
//! obsolete semantic profiles and truthiness paths must not return here.
//!
//! No Rust-side table is allowed to determine language meaning for a domain.

const CORE: &str = include_str!("../src/eval/special_forms/core.rs");
const ENV: &str = include_str!("../src/environment.rs");
const BOOT: &str = include_str!("../src/bootstrap_measurement.rs");
const LIB: &str = include_str!("../src/lib.rs");
const DOMAIN: &str = include_str!("../src/domain_identity.rs");

#[test]
fn exact_domain_route_has_no_retired_cond_or_graded_predicate_engine() {
    for forbidden in [
        "fn answer_direction(",
        "fn migration_only_cond_truthy(",
        "fn answer(",
        "CondClauseMode",
        "CoreProfile",
        ".is_truthy()",
        "(query expected-result expression)",
    ] {
        assert!(
            !CORE.contains(forbidden),
            "Rust must not own retired language semantics: {forbidden}"
        );
    }
}

#[test]
fn rust_domain_identity_stays_width_qualified_not_a_second_meaning_table() {
    for rung in 1..=9 {
        assert!(DOMAIN.contains(&format!("D{rung}(")), "missing D{rung} carrier");
    }
    assert!(DOMAIN.contains("BinarySourceWord"));
    assert!(DOMAIN.contains("pub const fn packed_bits"));
}

#[test]
fn legacy_cond_profile_state_does_not_reenter_rust_environment() {
    for source in [ENV, BOOT, LIB] {
        assert!(!source.contains("CondClauseMode"));
        assert!(!source.contains("set_cond_clause_mode"));
        assert!(!source.contains("cond_clause_mode"));
    }
}

#[test]
fn d10_mechanical_width_does_not_add_semantic_dispatch() {
    use sens::domain_ladder::DomainCoordinate;
    assert!(DomainCoordinate::new(10, 0).is_some());
    assert!(DomainCoordinate::new(10, 1023).is_some());
    assert!(DomainCoordinate::new(10, 1024).is_none());
    assert!(DomainCoordinate::new(11, 0).is_none());
}
