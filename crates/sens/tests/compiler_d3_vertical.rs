//! sens#3758 — first compiler-in-language vertical witness corpus.
//!
//! The cases come from one SENS-owned machine-readable evidence corpus:
//! `contracts/compiler-d3-selector-corpus-v1.tsv`.
//!
//! Semantic authority still remains in language-contract.lisp + the D3 law.
//! The corpus fixes reproducible source/provenance/expected observations so
//! downstream compilers can consume the same evidence without copying it.
//!
//! No historical Sid8/Sens8 identity is allowed anywhere in the lowered tree.

use sens::{
    eval_lowered_expressions, load_core_library, lower_program, parse_binary_source_words,
    parse_canonical_binary, sha256_source, CoreDomainIdentity, ErrorKind, Expr, ExprKind, Session,
};

const CORPUS: &str =
    include_str!("../../../contracts/compiler-d3-selector-corpus-v1.tsv");

struct Case {
    name: String,
    head: u8,
    source: String,
    digest: String,
    expected: Expected,
}

enum Expected {
    Value(String),
    Error(ErrorKind),
}

fn sha256_hex(bytes: &[u8]) -> String {
    sha256_source(bytes)
        .iter()
        .map(|byte| format!("{byte:02x}"))
        .collect()
}

fn cases() -> Vec<Case> {
    CORPUS
        .lines()
        .filter(|line| {
            let trimmed = line.trim();
            !trimmed.is_empty() && !trimmed.starts_with('#')
        })
        .map(|line| {
            let fields = line.split('\t').collect::<Vec<_>>();
            assert_eq!(
                fields.len(),
                6,
                "compiler D3 corpus row must have exactly six TSV fields: {line:?}"
            );

            let head_bits = fields[1];
            assert_eq!(
                head_bits.len(),
                3,
                "{} head identity must remain exact D3",
                fields[0]
            );
            assert!(
                head_bits.bytes().all(|byte| matches!(byte, b'0' | b'1')),
                "{} head identity must be binary",
                fields[0]
            );
            let head = u8::from_str_radix(head_bits, 2)
                .unwrap_or_else(|error| panic!("{} invalid D3 head: {error}", fields[0]));

            let expected = match (fields[4], fields[5]) {
                ("value", value) => Expected::Value(value.to_string()),
                ("error", "Type") => Expected::Error(ErrorKind::Type),
                (kind, value) => {
                    panic!(
                        "{} unsupported corpus expectation {kind:?}/{value:?}",
                        fields[0]
                    )
                }
            };

            Case {
                name: fields[0].to_string(),
                head,
                source: fields[2].to_string(),
                digest: fields[3].to_string(),
                expected,
            }
        })
        .collect()
}

fn assert_no_legacy_identity(expr: &Expr) {
    match &expr.kind {
        ExprKind::Sid(sid) => panic!("legacy byte identity entered compiler witness: {sid}"),
        ExprKind::Call(sid, _) => panic!("legacy byte call entered compiler witness: {sid}"),
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
    let ExprKind::DomainCall(identity, _) = &expr.kind else {
        panic!(
            "compiler witness must lower to an exact DomainCall, got {:?}",
            expr.kind
        );
    };
    match identity {
        CoreDomainIdentity::D3(word) => (3, word.word().packed_bits()),
        other => panic!("compiler witness must stay in D3, got {other:?}"),
    }
}

#[test]
fn machine_readable_compiler_corpus_has_exact_source_digests() {
    let cases = cases();
    assert_eq!(cases.len(), 4, "first selector corpus remains four bounded cases");

    for case in &cases {
        assert_eq!(
            sha256_hex(case.source.as_bytes()),
            case.digest,
            "{} source bytes drifted from recorded provenance",
            case.name
        );
    }
}

#[test]
fn compiler_vertical_corpus_is_exact_d3_and_has_no_legacy_byte_identity() {
    for case in cases() {
        let tokens = parse_binary_source_words(&case.source)
            .unwrap_or_else(|error| panic!("{} source-word parse failed: {error:?}", case.name));
        assert!(
            tokens.iter().all(|token| matches!(token.word.width(), 2 | 3)),
            "{} introduced a non-D2/D3 source word",
            case.name
        );

        let parsed = parse_canonical_binary(&case.source)
            .unwrap_or_else(|error| panic!("{} canonical parse failed: {error:?}", case.name));
        let lowered = lower_program(&parsed);

        assert_eq!(lowered.len(), 1, "{}", case.name);
        assert_eq!(top_d3(&lowered[0]), (3, case.head), "{}", case.name);
        assert_no_legacy_identity(&lowered[0]);
    }
}

#[test]
fn compiler_vertical_corpus_matches_current_evaluator_observables() {
    for case in cases() {
        let parsed = parse_canonical_binary(&case.source)
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
                let error = match observed {
                    Ok(result) => panic!(
                        "{} expected named failure, got value {}",
                        case.name, result.value
                    ),
                    Err(error) => error,
                };
                assert_eq!(&error.kind, expected_kind, "{}", case.name);
            }
        }
    }
}
