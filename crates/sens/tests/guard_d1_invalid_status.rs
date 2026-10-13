//! Real evaluator witness: invalid Guard decisions produce D1:NO, not structural NIL.
//! Two bounded predicates are independently bootstrapped to avoid D24+ dependency.
use sens::{
    eval_parsed_expressions, parse_mixed_exact_domain, Session, ExprKind,
};

const ALL: &str = include_str!("../../../lib/guard.lisp");
const ACCEPTED: &[(&str, &[&str])] = &[
    ("guard-decision?", &["allow", "warn", "reject", "unknown"]),
    ("guard-evidence-status?", &["confirmed", "partial", "unresolved", "broken"]),
];

fn session() -> Session {
    let mut session = Session::default();
    let split = ALL.find("(0011 guard-unknown-routes")
        .expect("next unmodified Guard module boundary");
    let definitions = parse_mixed_exact_domain(&ALL[..split])
        .expect("both definitions must load as exact D3/D4 source");
    assert_eq!(definitions.len(), 2);
    eval_parsed_expressions(&definitions, &mut session)
        .expect("define the two Guard predicates in the current evaluator");
    session
}

fn predicate(session: &mut Session, name: &str, argument: &str) -> Option<bool> {
    let code = format!("({name} (001 {argument}))");
    let ast = parse_mixed_exact_domain(&code)
        .unwrap_or_else(|e| panic!("parse {code}: {e:?}"));
    eval_parsed_expressions(&ast, session)
        .unwrap_or_else(|e| panic!("execute {code}: {e:?}"))
        .value.as_predicate_bit()
}

#[test]
fn eight_admitted_guard_states_are_exact_d1_yes() {
    let mut s = session();
    for (name, states) in ACCEPTED {
        for state in *states {
            assert_eq!(predicate(&mut s, name, state), Some(true),
                "{name}/{state}: must have exact D1:YES");
        }
    }
}

#[test]
fn invalid_guard_state_is_exact_d1_no_not_empty() {
    let mut s = session();
    for (name, _) in ACCEPTED {
        for status in ["unrecognized", "no-such-value"] {
            assert_eq!(predicate(&mut s, name, status), Some(false),
                "{name}/{status}: must have exact D1:NO, not structural EMPTY");
        }
    }
}

#[test]
fn d4_not_accepts_guard_invalid_d1_but_rejects_empty() {
    let mut s = session();
    let ast = parse_mixed_exact_domain(
        "(0100 (guard-decision? (001 unsupported)))"
    ).expect("exact D4 NOT syntax");
    let bit = eval_parsed_expressions(&ast, &mut s)
        .expect("strict D1:NO can be negated")
        .value;
    assert_eq!(bit.as_predicate_bit(), Some(true));
    let rejected = parse_mixed_exact_domain("(0100 (001 ()))")
        .expect("structural NIL input");
    let err = eval_parsed_expressions(&rejected, &mut s)
        .expect_err("D4 NOT must not coerce empty to D1:NO");
    assert!(err.message.contains("D1"), "unexpected type error: {err:?}");
}

#[test]
fn direct_d1_matches_original_evaluated_guard_for_every_status() {
    let split = ALL.find("(0011 guard-unknown-routes").unwrap();
    let old = ALL[..split]
        .replace("#d1:0", "(0100 (010 (001 ())))")
        .replace("#d1:1", "(010 (001 ()))");
    let old_definitions = parse_mixed_exact_domain(&old)
        .expect("historical exact guard predicates parse");
    let mut historical = Session::default();
    eval_parsed_expressions(&old_definitions, &mut historical)
        .expect("historical 2 predicates evaluate");

    let mut migrated = session();
    for (name, valid) in ACCEPTED {
        for status in valid.iter().copied().chain(["unrecognized", "no-such-value"]) {
            let old_out = predicate(&mut historical, name, status);
            let new_out = predicate(&mut migrated, name, status);
            assert_eq!(new_out, old_out,
                "{name}/{status}: direct W1 must match historical ATOM/NOT");
        }
    }
}

#[test]
fn direct_cond_short_circuits_and_d3_empty_stays_outside_d1() {
    let mut s = session();
    let exact = parse_mixed_exact_domain(
        "(110 (#d1:1 (001 chosen)) (#d1:1 (unknown-unreachable)))"
    ).expect("D3 COND accepts direct D1");
    let chosen = eval_parsed_expressions(&exact, &mut s)
        .expect("second branch must never evaluate")
        .value;
    assert_eq!(chosen.to_string(), "chosen");

    let no = parse_mixed_exact_domain("#d1:0").unwrap();
    let zero = eval_parsed_expressions(&no, &mut s).unwrap().value;
    let empty = parse_mixed_exact_domain("(001 ())").unwrap();
    let nil = eval_parsed_expressions(&empty, &mut s).unwrap().value;
    assert_eq!(zero.as_predicate_bit(), Some(false));
    assert_eq!(nil.as_predicate_bit(), None);
    assert_ne!(nil, zero);
}

#[test]
fn source_does_not_encode_status_predicates_as_plain_numeric_or_host_bool() {
    let definitions = parse_mixed_exact_domain(&ALL[..ALL.find("(0011 guard-unknown-routes").unwrap()])
        .expect("bounded Guard module");
    for expr in &definitions {
        assert!(matches!(expr.kind, ExprKind::List(_)));
    }
    assert!(!ALL.contains("((010 (001 ())) 0)"));
    assert!(!ALL.contains("((010 (001 ())) 1)"));
}
