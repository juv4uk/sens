//! #2953 — current clean-room D4 selector source.
//!
//! Human spellings are first-class projections of exact selector identities.
//! Active Core must not replace those values with duplicate Lisp closures.
//! Historical 8-bit compatibility calls delegate one-way to the same law.

use sens::{
    eval_program, load_core_library, Bit4, CoreD4, DomainIdentity, Session, Value,
};

fn d4(bits: u8) -> DomainIdentity {
    DomainIdentity::D4(CoreD4::from_word(Bit4::new(bits).unwrap()))
}

#[test]
fn ukrainian_selector_surfaces_are_first_class_clean_room_d4_values() {
    let session = Session::default();

    assert_eq!(
        session.environment.get("перше-від-першого"),
        Some(Value::DomainIdentity(d4(0b1000)))
    );
    assert_eq!(
        session.environment.get("перше-від-решти"),
        Some(Value::DomainIdentity(d4(0b1001)))
    );
    assert_eq!(
        session.environment.get("решта-від-решти"),
        Some(Value::DomainIdentity(d4(0b0111)))
    );
}

#[test]
fn active_core_keeps_selector_surface_exact_and_historical_byte_delegates_to_law() {
    let mut session = Session::default();
    load_core_library(&mut session).expect("active Core bootstrap");

    // Loading active Core must not replace the exact selector value with a
    // language-defined closure.
    assert_eq!(
        session.environment.get("перше-від-решти"),
        Some(Value::DomainIdentity(d4(0b1001)))
    );

    // Historical compatibility byte for the same spelling delegates to the
    // current clean-room selector law (D4:1001), not to a duplicate closure.
    let result = eval_program("(00110100 (00000001 (10 20)))", &mut session)
        .expect("historical selector compatibility must remain one-way");
    assert_eq!(result.value.to_string(), "20");
}
