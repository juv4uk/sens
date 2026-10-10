//! #2334: preserve the Lisp-owned NTH selector under exact two-clause D3 COND.
//! No host implementation of NTH, implicit truthiness, or legacy COND oracle.
use sens::{eval_program, load_core_library, Session};

fn observed(source: &str) -> Result<String, String> {
    let mut session = Session::default();
    load_core_library(&mut session).map_err(|err| format!("core: {err:?}"))?;
    eval_program(source, &mut session)
        .map(|result| result.value.to_string())
        .map_err(|err| format!("{:?}: {}", err.kind, err.message))
}

#[test]
fn core_nth_selects_head_and_recurses_for_nonzero_indices() {
    // Compare independent selectors instead of copying the NTH implementation
    // or inventing a Rust-owned interpretation of list semantics.
    for (index, selector) in [
        (0, "(00000101 (00000001 (a b c d)))"),
        (1, "(00000101 (00000110 (00000001 (a b c d))))"),
        (2, "(00000101 (00000110 (00000110 (00000001 (a b c d)))))"),
        (3, "(00000101 (00000110 (00000110 (00000110 (00000001 (a b c d))))))"),
    ] {
        let source = format!("(nth {index} (00000001 (a b c d)))");
        let actual = observed(&source).unwrap_or_else(|error| panic!("{source}: {error}"));
        let expected = observed(selector).unwrap_or_else(|error| panic!("{selector}: {error}"));
        assert_eq!(actual, expected, "NTH {index} must preserve D3 CAR/CDR selection");
    }
}

#[test]
fn core_nth_nested_data_is_not_flattened() {
    let source = "(nth 2 (00000001 ((a b) c (d e))))";
    let expected = "(00000101 (00000110 (00000110 (00000001 ((a b) c (d e))))))";
    assert_eq!(
        observed(source).unwrap_or_else(|err| panic!("{source}: {err}")),
        observed(expected).unwrap_or_else(|err| panic!("{expected}: {err}")),
    );
}

#[test]
fn core_nth_source_and_core4_snapshot_have_identical_two_clause_law() {
    const CORE: &str = include_str!("../../../lib/core.lisp");
    const CORE4: &str = include_str!("../../../lib/core4.lisp");
    const NTH: &str = r#"(00001001 nth
  (00001000 (i lst)
    (00000111
      ((00000011 i 0) (00000101 lst))
      ((00000010 (00000001 ()))
       (00101011 (00001101 i 1) (00000110 lst))))))"#;
    for (path, source) in [("core.lisp", CORE), ("core4.lisp", CORE4)] {
        assert!(source.contains(NTH), "{path} must carry identical exact-D1 NTH");
        assert_eq!(source.matches("(00001001 nth\n").count(), 1,
                   "{path} must not carry competing definitions");
    }
}
