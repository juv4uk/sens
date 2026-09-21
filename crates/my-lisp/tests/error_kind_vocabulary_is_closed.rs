//! #1104 observer for the Lisp-owned current ErrorKind vocabulary.
//!
//! The admitted names live in contracts/error-kind-vocabulary.lisp.
//! Rust remains an exhaustive implementation observer: adding/removing an
//! ErrorKind still requires handling every variant here, but the expected
//! vocabulary is read from Lisp-owned contract data rather than duplicated as
//! a Rust constant.

use my_lisp::{parse, ErrorKind, Expr, ExprKind};

const LEDGER_PATH: &str = "contracts/error-kind-vocabulary.lisp";

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

fn contract_forms() -> Vec<Expr> {
    let source = include_str!("../../../contracts/error-kind-vocabulary.lisp");
    parse(source).expect("error-kind-vocabulary.lisp must parse")
}

fn contract_entries(forms: &[Expr]) -> &[Expr] {
    assert_eq!(
        forms.len(),
        1,
        "error vocabulary must remain one Lisp data document"
    );

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
    entries
}

fn strings_from_list(expr: &Expr, context: &str) -> Vec<String> {
    let ExprKind::List(values) = &expr.kind else {
        panic!("{context} must be a list");
    };
    values
        .iter()
        .map(|value| match &value.kind {
            ExprKind::String(name) => name.to_string(),
            _ => panic!("{context} values must be strings"),
        })
        .collect()
}

fn contract_names() -> Vec<String> {
    let forms = contract_forms();
    let entries = contract_entries(&forms);
    let categories =
        pair_value(entries, "categories").expect("error vocabulary must define categories");
    strings_from_list(categories, "error vocabulary categories")
}

fn contract_provenance_names() -> Vec<String> {
    let forms = contract_forms();
    let entries = contract_entries(&forms);
    let provenance =
        pair_value(entries, "provenance").expect("error vocabulary must define provenance");
    let ExprKind::List(groups) = &provenance.kind else {
        panic!("error vocabulary provenance must be a list");
    };

    let mut names = Vec::new();
    for group in groups.iter() {
        let ExprKind::Pair(_source, values) = &group.kind else {
            panic!("each error vocabulary provenance group must be a dotted pair");
        };
        names.extend(strings_from_list(
            values,
            "error vocabulary provenance category group",
        ));
    }
    names
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

#[test]
fn every_admitted_error_category_has_exactly_one_language_owned_provenance() {
    let mut categories = contract_names();
    let mut provenance = contract_provenance_names();

    let category_count = categories.len();
    categories.sort();
    categories.dedup();
    assert_eq!(
        categories.len(),
        category_count,
        "error vocabulary categories must be unique"
    );

    let provenance_count = provenance.len();
    provenance.sort();
    provenance.dedup();
    assert_eq!(
        provenance.len(),
        provenance_count,
        "each error category must have exactly one provenance owner"
    );

    assert_eq!(
        categories, provenance,
        "every current error category must be accounted for by language-owned provenance"
    );
}

#[test]
fn normative_docs_point_to_the_lisp_owned_vocabulary_instead_of_owning_a_live_list() {
    let docs = [
        (
            "docs/language-core-axioms.md",
            include_str!("../../../docs/language-core-axioms.md"),
        ),
        (
            "docs/COMPILER-AUTHORITY-BOUNDARY.md",
            include_str!("../../../docs/COMPILER-AUTHORITY-BOUNDARY.md"),
        ),
        (
            "docs/capabilities.md",
            include_str!("../../../docs/capabilities.md"),
        ),
        (
            "tests/fixtures/README.md",
            include_str!("../../../tests/fixtures/README.md"),
        ),
    ];

    for (path, source) in docs {
        assert!(
            source.contains(LEDGER_PATH),
            "{path} must point current error-vocabulary claims to {LEDGER_PATH}"
        );
    }

    let fixture_docs = include_str!("../../../tests/fixtures/README.md");
    for stale in [
        "one of the eight `ErrorKind`",
        "одна з восьми назв `ErrorKind`",
        "einer von acht `ErrorKind`",
    ] {
        assert!(
            !fixture_docs.contains(stale),
            "fixture docs reintroduced stale live-vocabulary prose: {stale}"
        );
    }
}
