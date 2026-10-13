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


/// Тільки фізична/лексична доставка. Правило розгалуження і однобітний
/// мутант належать виконуваним 0/1 формам SENS, не Rust.
#[test]
fn native_first_parity_cond_guard_is_decided_by_binary_sens() {
    const LAW: &str =
        include_str!("../../../tests/semantic/native-first-parity-cond-law.bits");
    const MUTANT: &str =
        include_str!("../../../tests/semantic/native-first-parity-cond-mutant.bits");

    for source in [LAW, MUTANT] {
        assert!(
            source.bytes().all(|b| matches!(b, b'0' | b'1' | b' ' | b'\n' | b'\t' | b'\r')),
            "семантичний тест має містити лише двійкові слова SENS"
        );
    }

    // Лише транспорт: порядок і ширини слів незмінні, мутує рівно один D1-біт.
    let law_words: Vec<_> = LAW.split_whitespace().collect();
    let mutant_words: Vec<_> = MUTANT.split_whitespace().collect();
    assert_eq!(law_words.len(), 61);
    assert_eq!(law_words.len(), mutant_words.len());
    assert_eq!(law_words.iter().map(|s| s.len()).sum::<usize>(), 115);
    let delta: Vec<_> = law_words.iter().zip(&mutant_words)
        .filter(|(a, b)| a != b).collect();
    assert_eq!(delta, vec![(&"1", &"0")]);

    // Визначення двох результатів і всіх умов — всередині двійкового SENS.
    // Host лише спостерігає кінцевий типізований D1-біт, без свого COND/EQ.
    for (program, d1_yes) in [(LAW, true), (MUTANT, false)] {
        let forms = parse_canonical_binary(program)
            .expect("чинний canonical D2/domain reader має прийняти SENS");
        assert_eq!(forms.len(), 1);
        let verdict = eval_parsed_expressions(&forms, &mut Session::default())
            .expect("бінарний SENS має сам обчислити результат").value;
        assert_eq!(verdict.as_predicate_bit(), Some(d1_yes),
            "виконуваний SENS повернув неправильний D1-вердикт");
    }
}
