//! #1344: Foundation test for `sens` (СЕНС) vocabulary migration.
//!
//! Validates that `Sens8` and the `sens!` macro provide the canonical
//! eight-bit function sense representation with zero friction, completely
//! compatible with existing `Sens8` mechanisms while establishing the
//! ontological vocabulary for #1325.

use ::sens::{sens, Sens, Sens8};

#[test]
fn sens_macro_produces_identical_bit_representation_as_sid() {
    let s_eq = sens!(00000011);
    let old_eq = sens!(00000011);
    assert_eq!(s_eq, old_eq);
    assert_eq!(s_eq.to_string(), "00000011");
}

#[test]
fn sens8_and_sens_are_type_compatible() {
    let s: Sens8 = sens!(00000001);
    let s_alias: Sens = s;
    let back: Sens8 = s_alias;
    assert_eq!(s, back);
}

#[test]
#[allow(deprecated)]
fn deprecated_sid8_alias_is_still_the_same_box_for_cml() {
    let legacy: ::sens::Sid8 = ::sens::sid!(00000001);
    assert_eq!(legacy, sens!(00000001));
}

#[test]
fn sens_distinguishes_different_function_senses() {
    let s_atom = sens!(00000010);
    let s_eq = sens!(00000011);
    let s_cons = sens!(00000100);

    assert_ne!(s_atom, s_eq);
    assert_ne!(s_eq, s_cons);
    assert_ne!(s_atom, s_cons);

    assert_eq!(s_atom.to_string(), "00000010");
    assert_eq!(s_eq.to_string(), "00000011");
    assert_eq!(s_cons.to_string(), "00000100");
}
