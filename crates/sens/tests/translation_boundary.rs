//! B4 external translation boundary.
//! The translator may propose versioned Lisp data; only Lisp validation and
//! the existing advice boundary decide whether knowledge is admissible.

use sens::{eval_parsed_expressions, parse, parse_mixed_exact_domain, Session};

fn eval_translation(source: &str) -> String {
    let mut session = Session::default();
    // Повна бібліотека D1–D10 має штатний Core4 bootstrap для D8
    // текст-у-символ; повторне ручне читання лише core.lisp його не встановлює.
    sens::load_core_library(&mut session)
        .expect("штатний Core4 SENS потрібний бібліотеці перекладу");
    for library in [
        include_str!("../../../lib/unify.lisp"),
        include_str!("../../../lib/reason.lisp"),
        include_str!("../../../lib/forward.lisp"),
        include_str!("../../../lib/knowledge.lisp"),
        include_str!("../../../lib/result-status.lisp"),
        include_str!("../../../lib/translation.lisp"),
    ] {
        let forms = parse_mixed_exact_domain(library)
            .expect("чинний доменний SENS reader");
        eval_parsed_expressions(&forms, &mut session)
            .expect("чинна бібліотека виконується SENS");
    }
    eval_parsed_expressions(
        &parse_mixed_exact_domain(source)
            .unwrap_or_else(|error| panic!("чинний D1–D10 reader: {error}; source: {source}")),
        &mut session,
    )
        .unwrap_or_else(|e| panic!("translation evaluation failed: {e}\nsource: {source}"))
        .value
        .to_string()
}

#[test]
fn accepted_translation_review_is_pure_and_only_exposes_an_admission_payload() {
    let source = r#"
        (визначити before *knowledge-journal*)
        (визначити proposal
          (як-є (translation/1 candidate clause
                   "Socrates is human."
                   ((human socrates)))))
        (визначити review (переклад-перевірка (як-є corpus) proposal))
        (список
          (переклад-перевірка-стан review)
          (переклад-перевірка-код review)
          (однакові? before *knowledge-journal*)
          (однакові? (переклад-допуск-вміст review)
                  (як-є ((human socrates)))))
    "#;
    assert_eq!(
        eval_translation(source),
        "(accepted knowledge-accepted (1) (1))"
    );
}

#[test]
fn accepted_candidate_becomes_knowledge_only_after_explicit_advise() {
    let source = r#"
        (визначити proposal
          (як-є (translation/1 candidate clause
                   "Socrates is human."
                   ((human socrates)))))
        (визначити review (переклад-перевірка (як-є corpus) proposal))
        (визначити before-known (модуль-відомий? (як-є corpus)))
        (повідомити-знання corpus (переклад-допуск-вміст review))
        (список
          before-known
          (модуль-відомий? (як-є corpus))
          (результат-стан
            (міркувати-у-спостерігати (як-є corpus) (як-є (human socrates)))))
    "#;
    assert_eq!(eval_translation(source), "(() (1) proved)");
}

#[test]
fn ambiguous_translation_is_evidence_not_knowledge() {
    let source = r#"
        (визначити before *knowledge-journal*)
        (визначити proposal
          (як-є (translation/1 ambiguous clause
                   "Mercury is hot."
                   (((hot mercury-planet))
                    ((hot mercury-element))))))
        (визначити review (переклад-перевірка (як-є corpus) proposal))
        (визначити evidence (переклад-доказ-наступний review (як-є ())))
        (список
          (переклад-перевірка-стан review)
          (переклад-перевірка-код review)
          (довжина evidence)
          (однакові? before *knowledge-journal*)
          (переклад-допустимий? review))
    "#;
    assert_eq!(
        eval_translation(source),
        "(ambiguous translator-ambiguous 1 (1) ())"
    );
}

#[test]
fn malformed_semantic_candidate_is_rejected_and_cannot_reach_advice() {
    let source = r#"
        (визначити before *knowledge-journal*)
        (визначити proposal
          (як-є (translation/1 candidate clause
                   "Socrates is human."
                   ((human (var))))))
        (визначити review (переклад-перевірка (як-є corpus) proposal))
        (визначити evidence (переклад-доказ-наступний review (як-є ())))
        (список
          (переклад-перевірка-стан review)
          (переклад-перевірка-код review)
          (довжина evidence)
          (однакові? before *knowledge-journal*)
          (переклад-допуск-вміст review))
    "#;
    assert_eq!(
        eval_translation(source),
        "(rejected invalid-candidate 1 (1) ())"
    );
}

#[test]
fn translator_refusal_is_recordable_evidence_and_never_knowledge() {
    let source = r#"
        (визначити before *knowledge-journal*)
        (визначити proposal
          (як-є (translation/1 rejected clause
                   "Colorless green ideas sleep furiously."
                   unsupported-translation)))
        (визначити review (переклад-перевірка (як-є corpus) proposal))
        (визначити evidence (переклад-доказ-наступний review (як-є ())))
        (список
          (переклад-перевірка-стан review)
          (переклад-перевірка-код review)
          (довжина evidence)
          (однакові? before *knowledge-journal*)
          (переклад-допуск-вміст review))
    "#;
    assert_eq!(
        eval_translation(source),
        "(rejected translator-rejected 1 (1) ())"
    );
}

#[test]
fn existing_explicit_opposite_overrules_an_external_candidate() {
    let source = r#"
        (повідомити-знання corpus (як-є ((not? (human socrates)))))
        (визначити before *knowledge-journal*)
        (визначити proposal
          (як-є (translation/1 candidate clause
                   "Socrates is human."
                   ((human socrates)))))
        (визначити review (переклад-перевірка (як-є corpus) proposal))
        (список
          (переклад-перевірка-стан review)
          (переклад-перевірка-код review)
          (однакові? before *knowledge-journal*)
          (переклад-допуск-вміст review))
    "#;
    assert_eq!(
        eval_translation(source),
        "(rejected knowledge-conflict (1) ())"
    );
}

#[test]
fn accepted_query_is_a_question_not_a_knowledge_write() {
    let source = r#"
        (визначити before *knowledge-journal*)
        (визначити proposal
          (як-є (translation/1 candidate query
                   "Is Plato metallic?"
                   (metallic plato))))
        (визначити review (переклад-перевірка (як-є corpus) proposal))
        (список
          (переклад-перевірка-стан review)
          (переклад-перевірка-код review)
          (переклад-допуск-вміст review)
          (однакові? before *knowledge-journal*)
          (результат-стан
            (міркувати-у-спостерігати (як-є corpus) (переклад-вміст proposal))))
    "#;
    assert_eq!(eval_translation(source), "(accepted query () (1) blocked)");
}

#[test]
fn translation_alternatives_reject_improper_d3_tail_in_live_sens() {
    // Справжній SENS eval; не плутати атомарний хвіст і канонічний NIL.
    for (alternatives, expected) in [
        ("(((hot mercury-planet)) ((hot mercury-element)))", "1"),
        ("(((hot mercury-planet)) . зіпсований-хвіст)", "()"),
    ] {
        let expression = format!(
            "(альтернативні-варіанти-перекладу-коректні? (як-є clause) (як-є {alternatives}))"
        );
        assert_eq!(eval_translation(&expression), expected,
                   "SENS неправильно прийняв хвіст: {expression}");
    }
}

#[test]
fn one_alternative_is_not_allowed_to_masquerade_as_ambiguity() {
    let source = r#"
        (визначити proposal
          (як-є (translation/1 ambiguous clause
                   "Mercury is hot."
                   (((hot mercury))))))
        (визначити review (переклад-перевірка (як-є corpus) proposal))
        (список
          (переклад-перевірка-стан review)
          (переклад-перевірка-код review)
          (переклад-допуск-вміст review))
    "#;
    assert_eq!(
        eval_translation(source),
        "(rejected invalid-ambiguity ())"
    );
}

#[test]
fn malformed_protocol_envelope_is_named_before_semantic_admission() {
    let source = r#"
        (визначити review
          (переклад-перевірка
            (як-є corpus)
            (як-є (translation/2 candidate clause "text" ((human socrates))))))
        (список
          (переклад-перевірка-стан review)
          (переклад-перевірка-код review))
    "#;
    assert_eq!(eval_translation(source), "(rejected invalid-translation)");
}

#[test]
fn translation_source_classification_requires_d1_member() {
    // Класифікатор повертає (class-membership string member/nonmember):
    // це дані, а D3 COND має отримати тільки точний D1 предикат.
    let valid = r#"
        (структура-обгортки-перекладу-коректна?
          (як-є (translation/1 candidate query "текст" (metallic plato))))
    "#;
    let invalid = r#"
        (структура-обгортки-перекладу-коректна?
          (як-є (translation/1 candidate query (не-текст) (metallic plato))))
    "#;
    assert_eq!(eval_translation(valid), "1", "SENS: рядкове джерело");
    assert_eq!(eval_translation(invalid), "()", "SENS: нестрокове джерело");
}

#[test]
fn translation_symbol_law_rejects_non_symbols_in_live_sens() {
    // Чинний D8 текстовий шлях визначає символ, не ширший D3 ATOM.
    let mut session = Session::default();
    for library in [
        include_str!("../../../lib/core.lisp"),
        include_str!("../../../lib/unify.lisp"),
        include_str!("../../../lib/reason.lisp"),
        include_str!("../../../lib/forward.lisp"),
        include_str!("../../../lib/knowledge.lisp"),
        include_str!("../../../lib/result-status.lisp"),
        include_str!("../../../lib/translation.lisp"),
    ] {
        let forms = parse_mixed_exact_domain(library)
            .expect("чинний доменний SENS reader");
        eval_parsed_expressions(&forms, &mut session)
            .expect("чинна бібліотека SENS");
    }
    for (expression, expected) in [
        ("(як-є candidate)", true),
        ("\"candidate\"", false),
        ("7", false),
        ("(як-є ())", false),
        ("(як-є (candidate))", false),
    ] {
        let source = format!("(переклад-внутрішній-символ? {expression})");
        let actual = eval_parsed_expressions(
            &parse_mixed_exact_domain(&source)
                .unwrap_or_else(|error| panic!("{source}: {error}")),
            &mut session,
        )
            .unwrap_or_else(|error| panic!("{source}: {error}")).value;
        assert_eq!(actual.as_predicate_bit(), Some(expected), "{source}");
    }
}

#[test]
fn translation_exact_five_fields_rejects_short_long_and_dotted_lists() {
    let mut session = Session::default();
    for library in [
        include_str!("../../../lib/core.lisp"),
        include_str!("../../../lib/unify.lisp"),
        include_str!("../../../lib/reason.lisp"),
        include_str!("../../../lib/forward.lisp"),
        include_str!("../../../lib/knowledge.lisp"),
        include_str!("../../../lib/result-status.lisp"),
        include_str!("../../../lib/translation.lisp"),
    ] {
        let forms = parse_mixed_exact_domain(library)
            .expect("чинний доменний SENS reader");
        eval_parsed_expressions(&forms, &mut session)
            .expect("чинна бібліотека SENS");
    }
    for (value, expected) in [
        ("(а б в г ґ)", true),
        ("(а б в г)", false),
        ("(а б в г ґ д)", false),
        ("()", false),
        ("а", false),
        ("(а б в г . ґ)", false),
    ] {
        let source = format!("(переклад-рівно-п'ять-полів? (як-є {value}))");
        let actual = eval_parsed_expressions(
            &parse_mixed_exact_domain(&source)
                .unwrap_or_else(|error| panic!("{source}: {error}")),
            &mut session,
        )
            .unwrap_or_else(|error| panic!("{source}: {error}")).value;
        assert_eq!(actual.as_predicate_bit(), Some(expected), "{source}");
    }
}

#[test]
fn translation_envelopes_reject_missing_and_excess_fields_in_live_sens() {
    // Вкладене D3 EQ повертає D1:NO, а НЕ D3:EMPTY.
    // Неправильну кількість полів має відкинути сама SENS-бібліотека.
    for proposal in [
        "(translation/1 candidate query \"текст\")",
        "(translation/1 candidate query \"текст\" (мета) зайве)",
    ] {
        let source = format!(
            "(переклад-перевірка-код (переклад-перевірка (як-є корпус) (як-є {proposal})))"
        );
        assert_eq!(
            eval_translation(&source),
            "invalid-translation",
            "SENS accepted malformed translation envelope: {proposal}"
        );
    }
}

#[test]
fn translation_review_rejects_extra_field_in_live_sens() {
    let source = r#"
        (запис-огляду-перекладу-коректний?
          (як-є (translation-review/1 accepted query (пропозиція) (деталь) зайве)))
    "#;
    assert_eq!(eval_translation(source), "()");
}

#[test]
fn versioned_translation_corpus_is_data_only_and_contains_all_b4_modes() {
    let corpus = include_str!("../../../tests/fixtures/translation-corpus-v1.lisp");
    let forms = parse(corpus).expect("translation corpus must remain parseable data");
    assert_eq!(forms.len(), 1, "corpus must be one versioned data value");

    assert!(corpus.contains("(translation-corpus/1"));
    let case_count = corpus
        .lines()
        .filter(|line| line.trim_start().starts_with("(translation-case/1"))
        .count();
    assert_eq!(case_count, 6);

    for id in [
        "direct-fact",
        "rule-batch",
        "valid-question-without-proof",
        "malformed-semantic-candidate",
        "lexical-ambiguity",
        "translator-refusal",
    ] {
        assert!(corpus.contains(id), "missing corpus case {id}");
    }

    for status in ["accepted", "rejected", "ambiguous"] {
        assert!(
            corpus.contains(status),
            "corpus must exercise review status {status}"
        );
    }
    for outcome in ["proved", "unknown", "not-run"] {
        assert!(
            corpus.contains(outcome),
            "corpus must name downstream outcome {outcome}"
        );
    }
}
