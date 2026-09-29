//! #1708 mechanism/boundary-only coordinate witness.
//! Language semantics are Lisp-owned under #1709.

use sens::semantic_registry_export::semantic_id_for_admitted_surface;

#[test]
fn coordinate_rows_use_current_function_ids_without_minting_new_identity() {
    assert_eq!(semantic_id_for_admitted_surface("+"), Some(sens::sens!(00001100)));
    assert_eq!(semantic_id_for_admitted_surface("eq?"), Some(sens::sens!(00000011)));
    assert_eq!(semantic_id_for_admitted_surface("cons"), Some(sens::sens!(00000100)));
    assert_eq!(semantic_id_for_admitted_surface("car"), Some(sens::sens!(00000101)));
    assert_eq!(semantic_id_for_admitted_surface("cond"), Some(sens::sens!(00000111)));

    for label in [
        "exact-rational-arithmetic",
        "identity-relation",
        "pair-construction",
        "pair-elimination",
        "no-mathematical-law-claimed",
    ] {
        assert_eq!(
            semantic_id_for_admitted_surface(label),
            None,
            "{label} is evidence/data, not a Function8 identity"
        );
    }
}
