//! #1104 observer for the Lisp-owned current ErrorKind vocabulary.
//!
//! The admitted names live in contracts/error-kind-vocabulary.lisp.
//! Rust remains an exhaustive implementation observer: adding/removing an
//! ErrorKind still requires handling every variant here, but the expected
//! vocabulary is read from Lisp-owned contract data rather than duplicated as
//! a Rust constant.

use my_lisp::{parse, ErrorKind, Expr, ExprKind};

fn name_of(kind: &ErrorKind) -> &'static str {
    match kind {
        ErrorKind::Parse => "Parse",
        ErrorKind::UnknownSymbol => "UnknownSymbol",
        ErrorKind::Arity => "Arity",
        ErrorKind::Type => "Type",
        ErrorKind::InvalidForm => "InvalidForm",
        ErrorKind::UnsatisfiedConditional => "UnsatisfiedConditional",
        ErrorKind::MechanismUnavailable => "MechanismUnavailable",
        ErrorKind::OutOfMemory => "OutOfMemory",
        ErrorKind::NumericOverflow => "NumericOverflow",
        ErrorKind::DivisionByZero => "DivisionByZero",
    }
}

fn pair_value<'a>(entries: &'a [Expr], key: &str) -> Option<&'a Expr> {
    entries.iter().find_map(|entry| {
        let ExprKind::Pair(k, v) = &entry.kind else {
            return None;
        };
        let ExprKind::Symbol(name) = &k.kind else {
            return None;
        };
        (&**name == key).then_some(v.as_ref())
    })
}

fn contract_names() -> Vec<String> {
    let source = include_str!("../../../contracts/error-kind-vocabulary.lisp");
    let forms = parse(source).expect("error-kind-vocabulary.lisp must parse");
    assert_eq!(forms.len(), 1, "error vocabulary must remain one Lisp data document");

    let ExprKind::List(document) = &forms[0].kind else {
        panic!("error vocabulary document must be a list");
    };
    assert_eq!(document.len(), 2, "error vocabulary document shape drifted");

    let ExprKind::Symbol(tag) = &document[0].kind else {
        panic!("error vocabulary document must start with a symbolic tag");
    };
    assert_eq!(&**tag, "error-kind-vocabulary/1");

    let ExprKind::List(entries) = &document[1].kind else {
        panic!("error vocabulary body must be an alist");
    };
    let categories = pair_value(entries, "categories")
        .expect("error vocabulary must define categories");

    let ExprKind::List(values) = &categories.kind else {
        panic!("error vocabulary categories must be a list");
    };

    values
        .iter()
        .map(|value| match &value.kind {
            ExprKind::String(name) => name.to_string(),
            _ => panic!("error vocabulary categories must be strings"),
        })
        .collect()
}

#[test]
fn error_kind_vocabulary_matches_lisp_owned_contract() {
    let all_kinds = [
        ErrorKind::Parse,
        ErrorKind::UnknownSymbol,
        ErrorKind::Arity,
        ErrorKind::Type,
        ErrorKind::InvalidForm,
        ErrorKind::UnsatisfiedConditional,
        ErrorKind::MechanismUnavailable,
        ErrorKind::OutOfMemory,
        ErrorKind::NumericOverflow,
        ErrorKind::DivisionByZero,
    ];

    let observed: Vec<String> = all_kinds
        .iter()
        .map(|kind| name_of(kind).to_string())
        .collect();
    let expected = contract_names();

    assert_eq!(
        observed,
        expected,
        concat!(
            "Rust ErrorKind drifted from contracts/error-kind-vocabulary.lisp; ",
            "change language-owned admission/provenance first, then update the ",
            "exhaustive implementation observer"
        )
    );
}
