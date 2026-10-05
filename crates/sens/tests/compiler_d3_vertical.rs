//! sens#3758 — first compiler-in-language vertical witness corpus.
//!
//! These cases are owned by SENS and use only canonical exact-width binary
//! source. CML/backends may consume the same programs and expected observables,
//! but must not replace them with a backend-owned semantic fixture.
//!
//! The positive nested-pair cases are deliberately discriminating:
//! CAR and CDR produce different values. The empty-input cases are negative
//! controls and must preserve the canonical Type failure.
//!
//! No historical Sid8/Sens8 identity is allowed anywhere in the lowered tree.

use sens::{
    eval_lowered_expressions, load_core_library, lower_program, parse_canonical_binary,
    CoreDomainIdentity, ErrorKind, Expr, ExprKind, Session,
};

struct Case {
    name: &'static str,
    head: u8,
    source: &'static str,
    expected: Expected,
}

enum Expected {
    Value(&'static str),
    Error(ErrorKind),
}

const CASES: &[Case] = &[
    Case {
        name: "car-nested-pair",
        head: 0b100,
        source: "10 100 00 10 111 00 10 111 00 000 00 000 01 00 000 01 01",
        expected: Expected::Value("(())"),
    },
    Case {
        name: "cdr-nested-pair",
        head: 0b011,
        source: "10 011 00 10 111 00 10 111 00 000 00 000 01 00 000 01 01",
        expected: Expected::Value("()"),
    },
    Case {
        name: "car-empty-type-error",
        head: 0b100,
        source: "10 100 00 000 01",
        expected: Expected::Error(ErrorKind::Type),
    },
    Case {
        name: "cdr-empty-type-error",
        head: 0b011,
        source: "10 011 00 000 01",
        expected: Expected::Error(ErrorKind::Type),
    },
];

fn assert_no_legacy_identity(expr: &Expr) {
    match &expr.kind {
        ExprKind::Sid(sid) => panic!("legacy Sid8 entered compiler witness: {sid}"),
        ExprKind::Call(sid, _) => panic!("legacy Sid8 call entered compiler witness: {sid}"),
        ExprKind::List(items) => {
            for item in items.iter() {
                assert_no_legacy_identity(item);
            }
        }
        ExprKind::Pair(head, tail) => {
            assert_no_legacy_identity(head);
            assert_no_legacy_identity(tail);
        }
        ExprKind::DomainCall(_, args) => {
            for arg in args.iter() {
                assert_no_legacy_identity(arg);
            }
        }
        ExprKind::Number(_, _)
        | ExprKind::Rational(_)
        | ExprKind::BinaryNumber(_)
        | ExprKind::NumericBuffer(_)
        | ExprKind::DomainIdentity(_)
        | ExprKind::String(_)
        | ExprKind::Symbol(_)
        | ExprKind::Local { .. } => {}
    }
}

fn top_d3(expr: &Expr) -> (usize, u8) {
    let ExprKind::DomainCall(identity @ CoreDomainIdentity::D3(_), _) = &expr.kind else {
        panic!(
            "compiler witness must lower to an exact D3 DomainCall, got {:?}",
            expr.kind
        );
    };
    (identity.width(), identity.packed_bits())
}

#[test]
fn compiler_vertical_corpus_is_exact_d3_and_has_no_legacy_byte_identity() {
    for case in CASES {
        let parsed = parse_canonical_binary(case.source)
            .unwrap_or_else(|error| panic!("{} canonical parse failed: {error:?}", case.name));
        let lowered = lower_program(&parsed);

        assert_eq!(lowered.len(), 1, "{}", case.name);
        assert_eq!(top_d3(&lowered[0]), (3, case.head), "{}", case.name);
        assert_no_legacy_identity(&lowered[0]);
    }
}

#[test]
fn compiler_vertical_corpus_matches_current_evaluator_observables() {
    for case in CASES {
        let parsed = parse_canonical_binary(case.source)
            .unwrap_or_else(|error| panic!("{} canonical parse failed: {error:?}", case.name));
        let lowered = lower_program(&parsed);

        let mut session = Session::default();
        load_core_library(&mut session)
            .unwrap_or_else(|error| panic!("{} core bootstrap failed: {error:?}", case.name));

        let observed = eval_lowered_expressions(&lowered, &mut session);
        match &case.expected {
            Expected::Value(expected) => {
                let result = observed
                    .unwrap_or_else(|error| panic!("{} expected value, got {error:?}", case.name));
                assert_eq!(result.value.to_string(), *expected, "{}", case.name);
            }
            Expected::Error(expected_kind) => {
                let error = observed
                    .expect_err(&format!("{} expected named failure", case.name));
                assert_eq!(&error.kind, expected_kind, "{}", case.name);
            }
        }
    }
}
