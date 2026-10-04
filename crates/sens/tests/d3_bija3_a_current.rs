//! #3202/#3203 — current production D3 map ratchet.
//!
//! Human spellings are projection only. This test observes the exact Core.D3
//! identity produced by current lowering and rejects the superseded ordering.

use sens::{lower_program, parse, CoreDomainIdentity, ExprKind};

fn lowered_d3(source: &str) -> u8 {
    let parsed = parse(source).unwrap_or_else(|error| panic!("{source}: {error:?}"));
    let lowered = lower_program(&parsed);
    assert_eq!(lowered.len(), 1, "{source}");
    let ExprKind::DomainCall(CoreDomainIdentity::D3(word), _) = &lowered[0].kind else {
        panic!("{source}: expected exact D3 DomainCall, got {:?}", lowered[0].kind);
    };
    word.word().packed_bits()
}

#[test]
fn current_surfaces_lower_to_owner_ratified_bija3_a() {
    for (source, expected) in [
        ("(як-є x)", 0b001),
        ("(атом? x)", 0b010),
        ("(решта x)", 0b011),
        ("(перше x)", 0b100),
        ("(тотожне? x y)", 0b101),
        ("(за-умовою (x y))", 0b110),
        ("(сполучити x y)", 0b111),
    ] {
        assert_eq!(lowered_d3(source), expected, "{source}");
    }
}

#[test]
fn superseded_role_coordinates_are_not_an_alternate_current_map() {
    assert_ne!(lowered_d3("(за-умовою (x y))"), 0b011);
    assert_ne!(lowered_d3("(сполучити x y)"), 0b100);
    assert_ne!(lowered_d3("(перше x)"), 0b101);
    assert_ne!(lowered_d3("(решта x)"), 0b110);
    assert_ne!(lowered_d3("(тотожне? x y)"), 0b111);
}
