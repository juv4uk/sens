//! B4 external translation boundary.
//! The translator may propose versioned Lisp data; only Lisp validation and
//! the existing advice boundary decide whether knowledge is admissible.

use sens::{eval_parsed_expressions, parse, parse_mixed_exact_domain, Session};

fn eval_translation(source: &str) -> String {
    let mut session = Session::default();
    // Штатний Core4 уже завантажує lib/core.lisp разом з D3/D4/D6.
    // Так/ні тепер прямі незмінні D1, без повторного DEFINE чи другого
    // виконання тієї самої бібліотеки в різних режимах reader.
    sens::load_core_library(&mut session)
        .expect("штатний Core4 SENS потрібний бібліотеці перекладу");
    for (path, library) in [
        (
            "lib/persistent-map.lisp",
            include_str!("../../../lib/persistent-map.lisp"),
        ),
        ("lib/unify.lisp", include_str!("../../../lib/unify.lisp")),
        ("lib/reason.lisp", include_str!("../../../lib/reason.lisp")),
        (
            "lib/forward.lisp",
            include_str!("../../../lib/forward.lisp"),
        ),
        (
            "lib/knowledge.lisp",
            include_str!("../../../lib/knowledge.lisp"),
        ),
        ("lib/world.lisp", include_str!("../../../lib/world.lisp")),
        (
            "lib/result-status.lisp",
            include_str!("../../../lib/result-status.lisp"),
        ),
        (
            "lib/translation.lisp",
            include_str!("../../../lib/translation.lisp"),
        ),
    ] {
        // Production loads every reasoning library through its path-pinned
        // exact-domain reader. Use the same route here: generic source parsing
        // loses contextual D4/D7 bindings inside quoted macro templates.
        sens::eval_pinned_reasoning_source(path, library, &mut session)
            .expect("чинна reasoning-бібліотека має завантажуватися через точний pinned reader");
    }
    // Вираз іде ТИМ САМИМ reader-ом, що й бібліотеки: reasoning-шлях ліфтить
    // D9-голови (порада-рішення-у-світ тощо), загальний — ні. Раніше тут була
    // асиметрія: world.lisp завантажувався з ліфтингом, а вираз без нього,
    // і D9-голова лишалась Text7-послідовністю → unknown Text7 binding.
    eval_parsed_expressions(
        &sens::parse_mixed_exact_domain_reasoning_source("lib/world.lisp", source)
            .unwrap_or_else(|error| panic!("чинний D1–D10 reader: {error}; source: {source}")),
        &mut session,
    )
    .unwrap_or_else(|e| panic!("translation evaluation failed: {e}\nsource: {source}"))
    .value
    .to_string()
}

#[test]
fn reasoning_index_predicate_returns_d1_no_instead_of_cond_nil() {
    // Раніше обидві кінцеві гілки (ні ні) повертали () при промаху:
    // D3:110 COND потребує точні D1:1 або D1:0.
    let source = r#"
      (список
        (індекс-міркування? (як-є ()))
        (індекс-міркування? (як-є ((human socrates))))
        (індекс-міркування? (список схема-індексу-міркування
                                       (як-є linear) (як-є ()) (як-є ()))))
    "#;
    assert_eq!(
        eval_translation(source),
        "(0 0 1)",
        "реальний SENS D1-предикат на відсутньому та дійсному індексі"
    );
}

#[test]
fn translation_reads_current_knowledge_journal_in_real_sens() {
    // Доказова різниця: до повідомлення журнал порожній, після нього
    // український reader бачить поточну версію; протилежна клауза
    // відхиляється справжнім SENS, а не лексичною перевіркою Python.
    // Макрос приймає список клауз: (((хибне? мета))), а не одну ((хибне? мета)).
    let source = r#"
        (визначити літерал
          (список (текст-у-символ "human") (текст-у-символ "socrates")))
        (визначити протилежний-літерал (список (як-є хибне?) літерал))
        (визначити протилежна-клауза (список протилежний-літерал))
        (визначити журнал-до (поточний-журнал-знань))
        (повідомити-знання (як-є corpus) (список протилежна-клауза))
        (список
          (порожній? журнал-до)
          (хибне? (порожній? (поточний-журнал-знань)))
          (однакові? (поточний-журнал-знань) журнал-знань)
          (перше (отримати-рішення-за-порадою (як-є corpus)
                    (список літерал))))
    "#;
    assert_eq!(
        eval_translation(source),
        "(1 1 1 conflict)",
        "SENS має використовувати оновлений журнал і відхиляти суперечність"
    );
}

#[test]
fn world_direct_opposite_only_facts_not_unproved_rules() {
    // Перевіряється справжній SENS reader/eval, а не текстовий сканер:
    // факт протилежності відхиляється; голова правила з недоведеною
    // передумовою не стає доказом самої себе.
    let cases = [
        (
            r#"(визначити літерал (список (текст-у-символ "human") (текст-у-символ "socrates")))
               (визначити протилежний-літерал (список (як-є хибне?) літерал))
               (визначити клауза (список протилежний-літерал))
               (визначити світ-для-перевірки (світ-повідомити-всі (порожній-світ) (як-є corpus) (список клауза)))
               (перше (перше (порадити-світ світ-для-перевірки (як-є corpus) (список протилежний-літерал))))"#,
            "conflict",
        ),
        (
            r#"(визначити літерал (список (текст-у-символ "human") (текст-у-символ "socrates")))
               (визначити протилежний-літерал (список (як-є хибне?) літерал))
               (визначити невідома-передумова (список (текст-у-символ "unknown-premise") (текст-у-символ "socrates")))
               (визначити клауза (список протилежний-літерал невідома-передумова))
               (визначити світ-для-перевірки (світ-повідомити-всі (порожній-світ) (як-є corpus) (список клауза)))
               (перше (перше (порадити-світ світ-для-перевірки (як-є corpus) (список протилежний-літерал))))"#,
            "accepted",
        ),
    ];
    for (source, expected) in cases {
        assert_eq!(eval_translation(source), expected, "SENS world advice");
    }
}

#[test]
fn d10_advice_decisions_are_pure_world_derived_sens_functions() {
    // Відсутню раніше викличність двох ратифікованих D10 функцій
    // доводить тільки їхнє реальне виконання у SENS.
    let source = r#"
        (визначити журнал-до журнал-знань)
        (визначити одиночне-рішення
          (отримати-рішення-за-порадою (як-є corpus)
            (як-є ((human socrates)))))
        (визначити пакетне-рішення
          (узагальнене-рішення-за-всіма-порадами (як-є corpus)
            (як-є (((human socrates))))))
        (список
          (перше одиночне-рішення)
          (перше пакетне-рішення)
          (однакові? журнал-до журнал-знань))
    "#;
    assert_eq!(
        eval_translation(source),
        "(accepted accepted 1)",
        "обидва D10 рішення лише читають immutable World"
    );
}

#[test]
fn translation_content_validity_is_exact_d1_in_real_sens() {
    // Кожна гілка валідатора повертає D1:1/0, а не D3 NIL;
    // перевіряється реальним SENS eval з чинними бібліотеками.
    for (source, expected) in [
        (
            "(вміст-кандидата-перекладу-коректний? (як-є clause) (як-є ((human socrates))))",
            "1",
        ),
        (
            "(вміст-кандидата-перекладу-коректний? (як-є clause) (як-є ((human (var)))))",
            "0",
        ),
        (
            "(вміст-кандидата-перекладу-коректний? (як-є batch) (як-є ()))",
            "0",
        ),
        (
            "(вміст-кандидата-перекладу-коректний? (як-є невідомий-вид) (як-є ((human socrates))))",
            "0",
        ),
    ] {
        assert_eq!(eval_translation(source), expected, "D1 валідатор: {source}");
    }
}

#[test]
fn accepted_translation_review_is_pure_and_only_exposes_an_admission_payload() {
    let source = r#"
        (визначити журнал-до журнал-знань)
        ; Payload будується як D3-клауза з явно створеним SENS-символом.
        (визначити літерал
          (список (текст-у-символ "human") (текст-у-символ "socrates")))
        (визначити клауза (список літерал))
        (визначити пропозиція
          (список схема-перекладу (як-є candidate) (як-є clause)
                 "Socrates is human." клауза))
        (визначити огляд (переклад-перевірка (як-є corpus) пропозиція))
        (список
          (переклад-перевірка-стан огляд)
          (переклад-перевірка-код огляд)
          (однакові? журнал-до журнал-знань)
          (однакові? (переклад-допуск-вміст огляд) клауза))
    "#;
    assert_eq!(
        eval_translation(source),
        "(accepted knowledge-accepted 1 1)"
    );
}

#[test]
fn accepted_candidate_becomes_knowledge_only_after_explicit_advise() {
    // Admission повертає одну клаузу; до журналу передаємо список клауз.
    // Початкове значення «невідомий модуль» — D1 0, не D3 NIL.
    let source = r#"
        (визначити літерал
          (список (текст-у-символ "human") (текст-у-символ "socrates")))
        (визначити клауза (список літерал))
        (визначити пропозиція
          (список схема-перекладу (як-є candidate) (як-є clause)
                 "Socrates is human." клауза))
        (визначити огляд (переклад-перевірка (як-є corpus) пропозиція))
        (визначити модуль-до (модуль-відомий? (як-є corpus)))
        (повідомити-знання (як-є corpus) (список (переклад-допуск-вміст огляд)))
        (список
          модуль-до
          (модуль-відомий? (як-є corpus))
          (результат-стан
            (міркувати-у-спостерігати (як-є corpus) літерал)))
    "#;
    assert_eq!(eval_translation(source), "(0 1 proved)");
}

#[test]
fn ambiguous_translation_is_evidence_not_knowledge() {
    let source = r#"
        (визначити журнал-до журнал-знань)
        (визначити пропозиція
          (як-є (translation-1 ambiguous clause
                   "Mercury is hot."
                   (((hot mercury-planet))
                    ((hot mercury-element))))))
        (визначити огляд (переклад-перевірка (як-є corpus) пропозиція))
        (визначити докази (переклад-доказ-наступний огляд (як-є ())))
        (список
          (переклад-перевірка-стан огляд)
          (переклад-перевірка-код огляд)
          (довжина докази)
          (однакові? журнал-до журнал-знань)
          (переклад-допустимий? огляд))
    "#;
    assert_eq!(
        eval_translation(source),
        "(ambiguous translator-ambiguous 1 1 0)"
    );
}

#[test]
fn malformed_semantic_candidate_is_rejected_and_cannot_reach_advice() {
    let source = r#"
        (визначити журнал-до журнал-знань)
        (визначити пропозиція
          (як-є (translation-1 candidate clause
                   "Socrates is human."
                   ((human (var))))))
        (визначити огляд (переклад-перевірка (як-є corpus) пропозиція))
        (визначити докази (переклад-доказ-наступний огляд (як-є ())))
        (список
          (переклад-перевірка-стан огляд)
          (переклад-перевірка-код огляд)
          (довжина докази)
          (однакові? журнал-до журнал-знань)
          (переклад-допуск-вміст огляд))
    "#;
    assert_eq!(
        eval_translation(source),
        "(rejected invalid-candidate 1 1 ())"
    );
}

#[test]
fn translator_refusal_is_recordable_evidence_and_never_knowledge() {
    let source = r#"
        (визначити журнал-до журнал-знань)
        (визначити пропозиція
          (як-є (translation-1 rejected clause
                   "Colorless green ideas sleep furiously."
                   unsupported-translation)))
        (визначити огляд (переклад-перевірка (як-є corpus) пропозиція))
        (визначити докази (переклад-доказ-наступний огляд (як-є ())))
        (список
          (переклад-перевірка-стан огляд)
          (переклад-перевірка-код огляд)
          (довжина докази)
          (однакові? журнал-до журнал-знань)
          (переклад-допуск-вміст огляд))
    "#;
    assert_eq!(
        eval_translation(source),
        "(rejected translator-rejected 1 1 ())"
    );
}

#[test]
fn existing_explicit_opposite_overrules_an_external_candidate() {
    // Canonical D4 хибне? inside quoted knowledge data must retain D4 identity
    // through the mixed-source reader; it must not degrade to an unbound Text7.
    // Явний заперечний факт має правильну вкладеність списку клауз.
    let source = r#"
        (визначити літерал
          (список (текст-у-символ "human") (текст-у-символ "socrates")))
        (визначити протилежний-літерал (список (як-є хибне?) літерал))
        (визначити протилежна-клауза (список протилежний-літерал))
        (визначити журнал-до журнал-знань)
        (повідомити-знання (як-є corpus) (список протилежна-клауза))
        (визначити клауза (список літерал))
        (визначити пропозиція
          (список схема-перекладу (як-є candidate) (як-є clause)
                 "Socrates is human." клауза))
        (визначити огляд (переклад-перевірка (як-є corpus) пропозиція))
        (список
          (переклад-перевірка-стан огляд)
          (переклад-перевірка-код огляд)
          (однакові? журнал-до журнал-знань)
          (переклад-допуск-вміст огляд))
    "#;
    assert_eq!(
        eval_translation(source),
        "(rejected knowledge-conflict 1 ())"
    );
}

#[test]
fn accepted_query_is_a_question_not_a_knowledge_write() {
    let source = r#"
        (визначити журнал-до журнал-знань)
        (визначити пропозиція
          (як-є (translation-1 candidate query
                   "Is Plato metallic?"
                   (metallic plato))))
        (визначити огляд (переклад-перевірка (як-є corpus) пропозиція))
        (список
          (переклад-перевірка-стан огляд)
          (переклад-перевірка-код огляд)
          (переклад-допуск-вміст огляд)
          (однакові? журнал-до журнал-знань)
          (результат-стан
            (міркувати-у-спостерігати (як-є corpus) (переклад-вміст пропозиція))))
    "#;
    assert_eq!(eval_translation(source), "(accepted query () 1 blocked)");
}

#[test]
fn translation_alternatives_reject_improper_d3_tail_in_live_sens() {
    // Справжній SENS eval; не плутати атомарний хвіст і канонічний NIL.
    for (alternatives, expected) in [
        ("(((hot mercury-planet)) ((hot mercury-element)))", "1"),
        ("(((hot mercury-planet)) . зіпсований-хвіст)", "0"),
    ] {
        let expression = format!(
            "(альтернативні-варіанти-перекладу-коректні? (як-є clause) (як-є {alternatives}))"
        );
        assert_eq!(
            eval_translation(&expression),
            expected,
            "SENS неправильно прийняв хвіст: {expression}"
        );
    }
}

#[test]
fn one_alternative_is_not_allowed_to_masquerade_as_ambiguity() {
    let source = r#"
        (визначити пропозиція
          (як-є (translation-1 ambiguous clause
                   "Mercury is hot."
                   (((hot mercury))))))
        (визначити огляд (переклад-перевірка (як-є corpus) пропозиція))
        (список
          (переклад-перевірка-стан огляд)
          (переклад-перевірка-код огляд)
          (переклад-допуск-вміст огляд))
    "#;
    assert_eq!(eval_translation(source), "(rejected invalid-ambiguity ())");
}

#[test]
fn malformed_protocol_envelope_is_named_before_semantic_admission() {
    let source = r#"
        (визначити огляд
          (переклад-перевірка
            (як-є corpus)
            (як-є (translation-2 candidate clause "text" ((human socrates))))))
        (список
          (переклад-перевірка-стан огляд)
          (переклад-перевірка-код огляд))
    "#;
    assert_eq!(eval_translation(source), "(rejected invalid-translation)");
}

#[test]
fn translation_source_requires_exact_d1_string_predicate() {
    // D9 рядок? безпосередньо засвідчує тип джерела точним D1-бітом.
    let valid = r#"
        (структура-обгортки-перекладу-коректна?
          (як-є (translation-1 candidate query "текст" (metallic plato))))
    "#;
    let invalid = r#"
        (структура-обгортки-перекладу-коректна?
          (як-є (translation-1 candidate query (не-текст) (metallic plato))))
    "#;
    assert_eq!(eval_translation(valid), "1", "SENS: рядкове джерело");
    assert_eq!(eval_translation(invalid), "0", "SENS: D1:ні для нестрокового джерела");
}

#[test]
fn translation_symbol_law_rejects_non_symbols_in_live_sens() {
    // Чинний D8 текстовий шлях визначає символ, не ширший D3 ATOM.
    let mut session = Session::default();
    // Символьний закон використовує чинний D8 текст-у-символ із Core4.
    // Завантаження лише core.lisp помилково створює RED до перевірки D1.
    sens::load_core_library(&mut session)
        .expect("повний SENS Core4 має визначати чинний текст-у-символ");
    for (path, library) in [
        ("lib/persistent-map.lisp", include_str!("../../../lib/persistent-map.lisp")),
        ("lib/unify.lisp", include_str!("../../../lib/unify.lisp")),
        ("lib/reason.lisp", include_str!("../../../lib/reason.lisp")),
        ("lib/forward.lisp", include_str!("../../../lib/forward.lisp")),
        ("lib/knowledge.lisp", include_str!("../../../lib/knowledge.lisp")),
        ("lib/world.lisp", include_str!("../../../lib/world.lisp")),
        ("lib/result-status.lisp", include_str!("../../../lib/result-status.lisp")),
        ("lib/translation.lisp", include_str!("../../../lib/translation.lisp")),
    ] {
        sens::eval_pinned_reasoning_source(path, library, &mut session)
            .unwrap_or_else(|error| panic!("чинна reasoning-бібліотека {path}: {error}"));
    }
    for (expression, expected) in [
        // Compound values are rejected before D9 SYMBOL?; D1 bits are rejected
        // by exact equality; only remaining atomic values reach the symbol law.
        ("(як-є candidate)", true),
        ("\"candidate\"", false),
        ("7", false),
        ("так", false),
        ("ні", false),
        ("(як-є ())", false),
        ("(як-є (candidate))", false),
        ("(сполучити (як-є candidate) ні)", false),
    ] {
        let source = format!("(переклад-внутрішній-символ? {expression})");
        let actual = eval_parsed_expressions(
            &sens::parse_mixed_exact_domain_reasoning_source("lib/world.lisp", &source)
                .unwrap_or_else(|error| panic!("чинний D1–D10 reader: {error}; source: {source}")),
            &mut session,
        )
        .unwrap_or_else(|error| panic!("{source}: {error}"))
        .value;
        assert_eq!(actual.as_predicate_bit(), Some(expected), "{source}");
    }
}

#[test]
fn translation_exact_five_fields_rejects_short_long_and_dotted_lists() {
    let mut session = Session::default();
    sens::load_core_library(&mut session)
        .expect("чинний Core4 забезпечує штатні числові зв'язування");
    for library in [
        include_str!("../../../lib/unify.lisp"),
        include_str!("../../../lib/reason.lisp"),
        include_str!("../../../lib/forward.lisp"),
        include_str!("../../../lib/knowledge.lisp"),
        include_str!("../../../lib/result-status.lisp"),
        include_str!("../../../lib/translation.lisp"),
    ] {
        let forms = parse_mixed_exact_domain(library).expect("чинний доменний SENS reader");
        eval_parsed_expressions(&forms, &mut session).expect("чинна бібліотека SENS");
    }
    for (value, expected) in [
        ("(а б в г ґ)", true),
        ("(а б в г)", false),
        ("(а б в г ґ д)", false),
        ("()", false),
        ("а", false),
        ("(а б в г . ґ)", false),
    ] {
        let source = format!("(переклад-рівно-пять-полів? (як-є {value}))");
        let actual = eval_parsed_expressions(
            &parse_mixed_exact_domain(&source).unwrap_or_else(|error| panic!("{source}: {error}")),
            &mut session,
        )
        .unwrap_or_else(|error| panic!("{source}: {error}"))
        .value;
        assert_eq!(actual.as_predicate_bit(), Some(expected), "{source}");
    }
}

#[test]
fn translation_envelopes_reject_missing_and_excess_fields_in_live_sens() {
    // Вкладене D3 EQ повертає D1:NO, а НЕ D3:EMPTY.
    // Неправильну кількість полів має відкинути сама SENS-бібліотека.
    for proposal in [
        "(translation-1 candidate query \"текст\")",
        "(translation-1 candidate query \"текст\" (мета) зайве)",
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
          (як-є (translation-огляд-1 accepted query (пропозиція) (деталь) зайве)))
    "#;
    assert_eq!(eval_translation(source), "0");
}

#[test]
fn versioned_translation_corpus_is_data_only_and_contains_all_b4_modes() {
    let corpus = include_str!("../../../tests/fixtures/translation-corpus-v1.lisp");
    let forms = parse(corpus).expect("translation corpus must remain parseable data");
    assert_eq!(forms.len(), 1, "corpus must be one versioned data value");

    assert!(corpus.contains("(translation-corpus-1"));
    let case_count = corpus
        .lines()
        .filter(|line| line.trim_start().starts_with("(translation-case-1"))
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

#[test]
fn translation_review_evidence_named_sens_functions_execute_positive_and_negative() {
    // Перевіряємо реальне виконання виправлених Lisp-функцій через SENS:
    // огляд обчислюється один раз, доказ додається лише при відхиленні.
    // Анонімний D5 value-call чи Python-підміна семантики тут не застосовуються.
    for (proposal, expected) in [
        (
            r#"(translation-1 candidate query "текст" (metallic plato))"#,
            "(query 1 0)",
        ),
        (
            r#"(translation-1 rejected clause "текст" unsupported-translation)"#,
            "(translator-rejected 0 0)",
        ),
    ] {
        // D4 DEFINE має рівно два операнди: ім'я та значення.
        // Огляд виконується окремою наступною SENS-формою — без host LET.
        let source = format!(
            r#"(визначити пара-огляду
                 (переклад-перевірка-з-доказ (як-є corpus) (як-є {proposal}) (як-є ())))
               (список
                 (переклад-перевірка-код (перше пара-огляду))
                 (порожній? (друге пара-огляду))
                 (переклад-допустимий? (перше пара-огляду)))"#
        );
        assert_eq!(
            eval_translation(&source),
            expected,
            "Реальний SENS повинен зберігати рішення і журнал для {proposal}"
        );
    }
}
