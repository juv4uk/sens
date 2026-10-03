use sens::{Bija3, Bit3, Bit4, CoreD4, CoreDomainIdentity, Environment, Value};
use std::rc::Rc;

fn symbol(text: &str) -> Value {
    Value::Symbol(Rc::from(text))
}

fn assert_symbol(value: Value, expected: &str) {
    let Value::Symbol(ref actual) = value else {
        panic!("expected symbol value");
    };
    assert_eq!(actual.as_ref(), expected);
}

#[test]
fn equal_payloads_in_different_domains_keep_distinct_environment_slots() {
    let environment = Environment::root();
    let d3 = CoreDomainIdentity::from(Bija3::from_word(Bit3::new(0b001).unwrap()));
    let d4 = CoreDomainIdentity::from(CoreD4::from_word(Bit4::new(0b0001).unwrap()));

    assert_eq!(d3.packed_bits(), d4.packed_bits());
    assert_ne!(d3, d4);

    assert!(environment.bind_domain_slot_once(d3, symbol("d3")));
    assert!(environment.bind_domain_slot_once(d4, symbol("d4")));

    assert_symbol(environment.domain_slot(d3).expect("D3 slot"), "d3");
    assert_symbol(environment.domain_slot(d4).expect("D4 slot"), "d4");
}

#[test]
fn bind_once_is_scoped_to_exact_domain_identity() {
    let environment = Environment::root();
    let identity =
        CoreDomainIdentity::from(CoreD4::from_word(Bit4::new(0b0010).unwrap()));

    assert!(environment.bind_domain_slot_once(identity, symbol("first")));
    assert!(!environment.bind_domain_slot_once(identity, symbol("second")));
    assert_symbol(
        environment.domain_slot(identity).expect("bound domain slot"),
        "first",
    );
}

#[test]
fn lexical_children_share_session_domain_slots() {
    let root = Environment::root();
    let child = root.child();
    let identity =
        CoreDomainIdentity::from(CoreD4::from_word(Bit4::new(0b0011).unwrap()));

    assert!(root.bind_domain_slot_once(identity, symbol("shared")));
    assert_symbol(child.domain_slot(identity).expect("child sees root slot"), "shared");
}
