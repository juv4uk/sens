//! #4774 first ORIGINAL program: current evaluator must execute the
//! ALREADY RATIFIED D4:1110 LIST value-call mechanism. This is NOT an
//! admission of old .lisp source and does not define any Text7/global law.
//!
//! Physical T5 bytes -> exact domain words -> existing canonical D2 reader
//! -> current pure Rust evaluator. No historical SID aliases or new resident.

use sens::{encode_binary_projection_ternary, eval_parsed_expressions,
           open_ternary_program, parse_canonical_binary, Session, Value};

fn run_t5_exact(source: &str) -> Result<Value, String> {
    let bytes = encode_binary_projection_ternary(source)
        .map_err(|e| format!("T5 encode: {e:?}"))?;
    let visible = open_ternary_program(&bytes)
        .map_err(|e| format!("T5 decode: {e:?}"))?;
    if visible != source {
        return Err(format!("typed word boundaries changed: {visible} != {source}"));
    }
    let parsed = parse_canonical_binary(&visible)
        .map_err(|e| format!("D2 reader: {}", e.render(&visible)))?;
    eval_parsed_expressions(&parsed, &mut Session::default())
        .map(|result| result.value)
        .map_err(|e| format!("current oracle: {}", e.render(&visible)))
}

#[test]
fn ratified_d4_list_zero_arguments_returns_structural_nil() {
    // D2 ( D4:1110 LIST D2 ) => no args => NIL.
    assert_eq!(run_t5_exact("10 1110 01").unwrap().to_string(), "()");
}

#[test]
fn ratified_d4_list_of_one_nil_is_one_cons_cell() {
    assert_eq!(run_t5_exact("10 1110 00 000 01").unwrap().to_string(), "(())");
}

#[test]
fn ratified_d4_list_of_two_nil_values_is_two_cons_cells() {
    assert_eq!(run_t5_exact("10 1110 00 000 00 000 01").unwrap().to_string(), "(() ())");
}

#[test]
fn ratified_d4_list_receives_nested_quote_result_not_quote_ast() {
    // This exact call form was necessary on the owner-audited original
    // lib/machine/block.lisp (#4761), and failed in real #4774 T5+eval.
    let nested = "10 1110 00 10 001 00 000 01 01";
    let direct = "10 1110 00 000 01";
    let a = run_t5_exact(nested)
        .unwrap_or_else(|reason| panic!("D4 LIST nested D3 QUOTE failure: {reason}"));
    let b = run_t5_exact(direct).expect("D4 LIST structural nil");
    assert_eq!(a.to_string(), "(())");
    assert_eq!(a.to_string(), b.to_string());
}

#[test]
fn ratified_d4_list_preserves_order_and_values() {
    // List [Nil, [Nil]], where the second value itself comes from LIST.
    let nested = "10 1110 00 000 00 10 1110 00 000 01 01";
    assert_eq!(run_t5_exact(nested).unwrap().to_string(), "(() (()))");
}


#[test]
fn ratified_d4_append_two_empty_proper_lists_returns_nil() {
    assert_eq!(run_t5_exact("10 1111 00 000 00 000 01")
        .unwrap().to_string(), "()");
}

#[test]
fn ratified_d4_append_copies_left_spine_preserving_order() {
    // APPEND (LIST ()) (LIST ()) -> (() ()), exactly two proper lists.
    let source = "10 1111 00 10 1110 00 000 01 00 10 1110 00 000 01 01";
    assert_eq!(run_t5_exact(source).unwrap().to_string(), "(() ())");
}

#[test]
fn ratified_d4_append_original_machine_block_nested_list_case() {
    // Machine-block-append uses APPEND block (LIST form).
    // Here block = QUOTE Nil and form = QUOTE Nil, so result = (()).
    let source = "10 1111 00 10 001 00 000 01 00 10 1110 00 10 001 00 000 01 01 01";
    assert_eq!(run_t5_exact(source).unwrap().to_string(), "(())");
}

#[test]
fn ratified_d4_append_rejects_unproved_arity_and_improper_values() {
    // Unlike variadic historical extension, the audited 1959-60 original
    // machine-block contract takes exactly two proper list values.
    assert!(run_t5_exact("10 1111 01").is_err());
    assert!(run_t5_exact("10 1111 00 000 01").is_err());
    // Quote an ATOM domain identity as a non-list value, never silently coerce.
    let source = "10 1111 00 10 001 00 010 01 00 000 01";
    assert!(run_t5_exact(source).is_err());
}
