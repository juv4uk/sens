//! Mechanical runner for SENS-owned semantic witnesses.
//!
//! The semantic expectation is encoded inside each binary SENS program.
//! Rust loads admitted language libraries and reports only whether the
//! self-verdict program executes successfully. It contains no truth table,
//! expected result value, or duplicate language law.

use sens::{
    eval_parsed_expressions, eval_pinned_legacy_core_source,
    parse_canonical_binary, parse_mixed_exact_domain_reasoning_source, Session,
};

const RESULT_STATUS: &str = include_str!("../../../lib/result-status.lisp");
const RESULT_STATUS_D1_WITNESS: &str =
    include_str!("../../../tests/semantic/result-status-d1-law.bits");

fn load_reasoning(session: &mut Session, path: &str, source: &str) {
    let parsed = parse_mixed_exact_domain_reasoning_source(path, source)
        .unwrap_or_else(|error| panic!("mechanical parse failed for {path}: {error}"));
    eval_parsed_expressions(&parsed, session)
        .unwrap_or_else(|error| panic!("mechanical library load failed for {path}: {error}"));
}

#[test]
fn result_status_exact_d1_binary_self_verdict() {
    assert!(
        RESULT_STATUS_D1_WITNESS
            .bytes()
            .all(|byte| matches!(byte, b'0' | b'1' | b' ' | b'\n' | b'\r' | b'\t')),
        "semantic witness must be exact binary SENS source"
    );

    let mut session = Session::default();
    eval_pinned_legacy_core_source(
        "lib/core.lisp",
        include_str!("../../../lib/core.lisp"),
        &mut session,
    )
    .expect("mechanical Core loader must admit current source");
    load_reasoning(&mut session, "lib/result-status.lisp", RESULT_STATUS);

    let witness = parse_canonical_binary(RESULT_STATUS_D1_WITNESS)
        .expect("binary SENS witness must have canonical D2 framing");
    eval_parsed_expressions(&witness, &mut session)
        .expect("SENS-owned result-status self-verdict rejected");
}


const X86_ENCODING_DIRECT_D4_LAW: &str =
    include_str!("../../../tests/semantic/x86-encoder-let-d4-law.bits");
const X86_ENCODING_DIRECT_D4_MUTANT: &str =
    include_str!("../../../tests/semantic/x86-encoder-let-d4-mutant.bits");

/// Лише механічний транспорт: усі закони й вердикти закодовано самою
/// двійковою мовою SENS, а не таблицею очікувань у Rust або Python.
#[test]
fn x86_encoding_let_to_exact_d4_binary_sens_verdict() {
    for source in [X86_ENCODING_DIRECT_D4_LAW, X86_ENCODING_DIRECT_D4_MUTANT] {
        assert!(source.bytes().all(|byte|
            matches!(byte, b'0' | b'1' | b' ' | b'\n' | b'\r' | b'\t')
        ), "SENS source must consist only of bits and separators");
    }

    let forms = parse_canonical_binary(X86_ENCODING_DIRECT_D4_LAW)
        .expect("binary SENS must retain exact D1/D2/D3/D4/D7 widths");
    assert_eq!(forms.len(), 4, "four independent binary self-verdicts");
    for form in forms.iter() {
        let outcome = eval_parsed_expressions(
            std::slice::from_ref(form), &mut Session::default(),
        ).expect("binary SENS self-verdict must execute").value;
        assert_eq!(
            outcome.as_predicate_bit(), Some(true),
            "SENS verdict was not exact D1 YES: {outcome}",
        );
    }

    // Mutation is a transport assertion, not a second host-side logical law:
    // same complete binary program, one exact D1 data bit changed 1→0.
    let good: Vec<_> = X86_ENCODING_DIRECT_D4_LAW.lines().next()
        .expect("first binary verdict").split_whitespace().collect();
    let bad: Vec<_> = X86_ENCODING_DIRECT_D4_MUTANT.split_whitespace().collect();
    assert_eq!(good.len(), bad.len(), "a mutation cannot change source framing");
    let differences: Vec<_> = good.iter().zip(bad.iter())
        .filter(|(a, b)| a != b).collect();
    assert_eq!(differences, vec![(&"1", &"0")], "mutate one exact D1 bit");

    let mutant = parse_canonical_binary(X86_ENCODING_DIRECT_D4_MUTANT)
        .expect("one-bit mutant must remain a valid SENS expression");
    assert_eq!(mutant.len(), 1);
    let outcome = eval_parsed_expressions(&mutant, &mut Session::default())
        .expect("mutant must still execute through SENS").value;
    assert_eq!(
        outcome.as_predicate_bit(), Some(false),
        "one-bit SENS mutant must report exact D1 NO: {outcome}",
    );
}

const META_EVAL_MUTUAL_D4_LAW: &str =
    include_str!("../../../tests/semantic/meta-eval-mutual-d4-law.bits");

/// Механічний транспорт: зміст перевірок і їхній очікуваний D1=1
/// належать виключно виконуваним бітовим формам SENS.
#[test]
fn meta_eval_mutual_d4_exact_sens_self_verdict() {
    assert!(
        META_EVAL_MUTUAL_D4_LAW
            .bytes()
            .all(|byte| matches!(byte, b'0' | b'1' | b' ' | b'\n' | b'\r' | b'\t')),
        "SENS must own all semantic assertions in exact binary source"
    );
    let forms = parse_canonical_binary(META_EVAL_MUTUAL_D4_LAW)
        .expect("canonical D2 framing and exact D1/D3/D4/D7 words");
    assert_eq!(forms.len(), 4, "one executable binary SENS self-proof per line");

    for (index, form) in forms.iter().enumerate() {
        let result = eval_parsed_expressions(
            std::slice::from_ref(form), &mut Session::default(),
        )
        .unwrap_or_else(|error| panic!("binary SENS self-proof {} failed to execute: {error}", index + 1))
        .value;
        assert_eq!(
            result.as_predicate_bit(), Some(true),
            "binary SENS self-proof {} did not produce exact D1 YES: {result}",
            index + 1
        );
    }
}


const WORLD_LIBRARY: &str = include_str!("../../../lib/world.lisp");
const WORLD_EXACT_ARITY_BINARY: &str =
    include_str!("../../../tests/semantic/world-exact-arity-structure.bits");
const WORLD_EXACT_ARITY_WITNESS: &str =
    include_str!("../../../tests/semantic/world-exact-arity-witness.lisp");

/// Semantic answers live in executable SENS witnesses; Rust only loads the
/// library and accepts exact D1 YES from each self-verdict.
#[test]
fn world_exact_snapshot_shape_binary_self_verdict() {
    assert!(
        WORLD_EXACT_ARITY_BINARY.bytes().all(|byte|
            matches!(byte, b'0' | b'1' | b' ' | b'\n' | b'\r' | b'\t')
        ),
        "structural arity law must be written as canonical binary SENS"
    );

    let binary_forms = parse_canonical_binary(WORLD_EXACT_ARITY_BINARY)
        .expect("exact D1/D3/D4 binary world-shape witness");
    assert_eq!(binary_forms.len(), 3, "three binary arity self-verdicts");

    let mut session = Session::default();
    eval_pinned_legacy_core_source(
        "lib/core.lisp",
        include_str!("../../../lib/core.lisp"),
        &mut session,
    )
    .expect("Core library must load");
    load_reasoning(&mut session, "lib/world.lisp", WORLD_LIBRARY);

    for (index, form) in binary_forms.iter().enumerate() {
        let outcome = eval_parsed_expressions(
            std::slice::from_ref(form),
            &mut session,
        )
        .unwrap_or_else(|error| panic!(
            "binary world arity witness {} failed to execute: {error:?}",
            index + 1
        ))
        .value;
        assert_eq!(
            outcome.as_predicate_bit(),
            Some(true),
            "binary world arity witness {} must return exact D1 YES: {outcome}",
            index + 1
        );
    }

    // world? is a source-local Lisp binding, not a ratified callable D10
    // identity. Exercise it by its language binding rather than forging a
    // wider identity; built-in primitive heads remain exact D3/D1 coordinates.
    // Each row compares actual and expected D1 answers inside SENS, so the
    // host only transports the final YES verdict.
    let direct_forms = sens::parse_mixed_exact_domain(WORLD_EXACT_ARITY_WITNESS)
        .expect("SENS-owned world? exact-arity witness must parse");
    assert_eq!(direct_forms.len(), 7, "seven SENS-owned world shape cases");
    for (index, form) in direct_forms.iter().enumerate() {
        let outcome = eval_parsed_expressions(
            std::slice::from_ref(form),
            &mut session,
        )
        .unwrap_or_else(|error| panic!(
            "SENS world? self-verdict {} failed to execute: {error:?}",
            index + 1
        ))
        .value;
        assert_eq!(
            outcome.as_predicate_bit(),
            Some(true),
            "SENS world? self-verdict {} must return exact D1 YES: {outcome}",
            index + 1
        );
    }
}
