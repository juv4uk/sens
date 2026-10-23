use sens::{
    eval_core_library_source, eval_parsed_expressions, eval_program,
    parse_mixed_exact_domain_reasoning_source, Session, Value,
};

const FORWARD: &str = include_str!("../../../lib/forward.lisp");

const MIGRATED_MACROS: &[&str] = &[
    "ствердити-факт!",
    "ствердити-факти!",
    "відкликати-факт!",
    "ствердити-факт-система-істини!",
    "запустити-система-істини!",
    "відкликати-факт-система-істини!",
    "ствердити-факт-система-обґрунтувань!",
    "запустити-система-обґрунтувань!",
    "запустити-система-обґрунтувань-мульти!",
    "відкликати-факт-система-обґрунтувань!",
];

fn load_reasoning(session: &mut Session, path: &str, source: &str) {
    let parsed = parse_mixed_exact_domain_reasoning_source(path, source)
        .unwrap_or_else(|error| panic!("pinned reasoning parse failed for {path}: {error}"));
    eval_parsed_expressions(&parsed, session)
        .unwrap_or_else(|error| panic!("pinned reasoning load failed for {path}: {error}"));
}

fn session() -> Session {
    let mut session = Session::default();
    eval_core_library_source(include_str!("../../../lib/core.lisp"), &mut session)
        .expect("exact-domain core bootstrap");

    load_reasoning(
        &mut session,
        "lib/unify.lisp",
        include_str!("../../../lib/unify.lisp"),
    );
    load_reasoning(
        &mut session,
        "lib/reason.lisp",
        include_str!("../../../lib/reason.lisp"),
    );
    load_reasoning(&mut session, "lib/forward.lisp", FORWARD);
    session
}

fn eval(session: &mut Session, source: &str) -> String {
    eval_program(source, session)
        .unwrap_or_else(|error| panic!("evaluation failed: {error}\nsource: {source}"))
        .value
        .to_string()
}

fn eight_bit_heads(source: &str) -> Vec<String> {
    let bytes = source.as_bytes();
    let mut result = Vec::new();
    let mut i = 0;
    let mut in_string = false;
    let mut escaped = false;
    let mut in_comment = false;

    while i < bytes.len() {
        let byte = bytes[i];
        if in_comment {
            if byte == b'\n' {
                in_comment = false;
            }
            i += 1;
            continue;
        }
        if in_string {
            if escaped {
                escaped = false;
            } else if byte == b'\\' {
                escaped = true;
            } else if byte == b'"' {
                in_string = false;
            }
            i += 1;
            continue;
        }
        if byte == b';' {
            in_comment = true;
            i += 1;
            continue;
        }
        if byte == b'"' {
            in_string = true;
            i += 1;
            continue;
        }

        if byte == b'(' && i + 9 < bytes.len() {
            let bits = &bytes[i + 1..i + 9];
            let delimiter = bytes[i + 9];
            if bits.iter().all(|bit| matches!(bit, b'0' | b'1'))
                && (delimiter.is_ascii_whitespace() || delimiter == b')')
            {
                result.push(String::from_utf8(bits.to_vec()).expect("binary head is ASCII"));
            }
        }
        i += 1;
    }
    result
}

#[test]
fn forward_macro_cutover_uses_native_d5() {
    let heads = eight_bit_heads(FORWARD);
    assert!(
        heads.is_empty(),
        "forward.lisp must have no executable eight-bit compatibility heads: {heads:?}"
    );

    assert_eq!(
        FORWARD.matches("(як-є визначити)").count(),
        MIGRATED_MACROS.len()
    );
    assert!(
        !FORWARD.contains("(як-є def)"),
        "legacy def macro expansion forbidden"
    );
    assert!(
        !FORWARD.contains("(make-macro"),
        "старий макроконструктор відсутній"
    );
    for name in MIGRATED_MACROS {
        let define = format!("(визначити {name}\n  (макрос\n    (функція ");
        assert!(
            FORWARD.contains(&define),
            "{name} must be D4 DEFINE -> D5 МАКРОС -> D4 ФУНКЦІЯ"
        );
    }
}

#[test]
fn all_ten_forward_macros_are_real_macro_values() {
    let session = session();
    for name in MIGRATED_MACROS {
        assert!(
            matches!(session.environment.get(name), Some(Value::Macro(_))),
            "{name} must load as a real Macro value"
        );
    }
}

#[test]
fn migrated_macros_drive_plain_tms_and_jtms_state_transitions() {
    let mut session = session();
    // Реальний SENS-виклик: стан змінюється D4 DEFINE, потім відкликається.
    eval(&mut session, "(ствердити-факт! (як-є альфа))");
    assert_eq!(eval(&mut session, "робоча-пам'ять"), "(альфа)");
    eval(&mut session, "(відкликати-факт! (як-є альфа))");
    assert_eq!(eval(&mut session, "робоча-пам'ять"), "()");

    for source in [
        "(ствердити-факт! (як-є альфа))",
        "(ствердити-факти! (як-є (бета гамма)))",
        "(відкликати-факт! (як-є альфа))",
        "(відкликати-факт! (як-є бета))",
        "(відкликати-факт! (як-є гамма))",
        "(ствердити-факт-система-істини! (як-є delta))",
        "(запустити-система-істини! (як-є ()))",
        "(відкликати-факт-система-істини! (як-є delta))",
        "(ствердити-факт-система-обґрунтувань! (як-є epsilon))",
        "(запустити-система-обґрунтувань! (як-є ()))",
        "(запустити-система-обґрунтувань-мульти! (як-є ()))",
        "(відкликати-факт-система-обґрунтувань! (як-є epsilon))",
    ] {
        let _ = eval(&mut session, source);
    }

    assert_eq!(
        eval(
            &mut session,
            "(список робоча-пам'ять обґрунтована-пам'ять пам'ять-обґрунтувань)",
        ),
        "(() () ())",
        "all three mutable reasoning memories must return to empty after bounded assert/run/retract"
    );
}

#[test]
fn ratified_d9_macro_heads_execute_the_same_sens_laws() {
    // Перевіряємо результат самого SENS evaluator, а не лексичну наявність імен.
    // Англійський запис тут — лише контроль того самого наявного Lisp-замикання.
    let mut session = session();
    for (old_name, ukr, arguments) in [
        ("axiom", "аксіома", "(як-є факт)"),
        ("run-tms", "запустити-система-істини", "(як-є ()) (як-є ())"),
        (
            "run-jtms",
            "запустити-система-обґрунтувань",
            "(як-є ()) (як-є ())",
        ),
        (
            "run-jtms-multi",
            "запустити-система-обґрунтувань-мульти",
            "(як-є ()) (як-є ())",
        ),
    ] {
        let existing_law = eval(&mut session, &format!("({old_name} {arguments})"));
        let ratified = eval(&mut session, &format!("({ukr} {arguments})"));
        assert_eq!(
            ratified, existing_law,
            "D9 українська проєкція {ukr} змінила закон"
        );
    }
}

#[test]
fn jtms_real_sens_retains_independent_proofs_and_filters_only_unsupported() {
    // СЕНС сам обчислює кожен закон. Rust тільки звіряє точний результат Д1.
    let mut session = session();
    let distinct_proofs = r#"
        (уніфікація-рівні?
          (додати-обґрунтування (як-є факт) (список (як-є друга-причина))
            (додати-обґрунтування (як-є факт) (список (як-є перша-причина)) (як-є ())))
          (список
            (список (як-є факт)
              (список (як-є друга-причина))
              (список (як-є перша-причина)))))
    "#;
    assert_eq!(
        eval(&mut session, distinct_proofs),
        "1",
        "друге незалежне обґрунтування має залишитися"
    );

    let duplicate_proof = r#"
        (уніфікація-рівні?
          (додати-обґрунтування (як-є факт) (список (як-є причина))
            (додати-обґрунтування (як-є факт) (список (як-є причина)) (як-є ())))
          (список (список (як-є факт) (список (як-є причина)))))
    "#;
    assert_eq!(
        eval(&mut session, duplicate_proof),
        "1",
        "повторний доказ не повинен створювати дубль"
    );

    let filter_proofs = r#"
        (уніфікація-рівні?
          (відкинути-непідтримані
            (список
              (сполучити (як-є без-доказу) ні)
              (сполучити (як-є з-підтвердженням) так)
              (список (як-є з-доказом) (список (як-є причина)))
              (список (як-є порожня-підстава))))
          (список
            (сполучити (як-є з-підтвердженням) так)
            (список (як-є з-доказом) (список (як-є причина)))))
    "#;
    assert_eq!(
        eval(&mut session, filter_proofs),
        "1",
        "не можна викидати підтриманий факт"
    );

    let orphaned = r#"
        (уніфікація-рівні?
          (непідтримані-факти
            (список
              (сполучити (як-є без-доказу) ні)
              (сполучити (як-є підтриманий) так)
              (список (як-є порожня-підстава))
              (список (як-є з-доказом) (список (як-є причина)))))
          (список (як-є без-доказу) (як-є порожня-підстава)))
    "#;
    assert_eq!(
        eval(&mut session, orphaned),
        "1",
        "до каскадного відкликання надходять лише факти без підстав"
    );
}

#[test]
fn exact_d9_definition_accepts_real_sens_macro_not_plain_data() {
    // Точна Д9-голова (не старий SID8) зберігає макросний D5-механізм.
    // Нативний оцінювач отримує сирий AST, а не Python/JSON-імітацію.
    let mut session = Session::default();
    eval_core_library_source(include_str!("../../../lib/core.lisp"), &mut session)
        .expect("завантажити чинний SENS Core");

    let macro_source =
        "(визначити ствердити-факт! (макрос (функція (факт) факт)))";
    let parsed = parse_mixed_exact_domain_reasoning_source("lib/forward.lisp", macro_source)
        .expect("точна Д9-голова макроса");
    let defined = eval_parsed_expressions(&parsed, &mut session)
        .expect("точна Д9-голова приймає виконуване значення D5 МАКРОС");
    assert!(matches!(defined.value, Value::Macro(_)));

    let call = parse_mixed_exact_domain_reasoning_source(
        "lib/forward.lisp",
        "(ствердити-факт! (як-є насіння))",
    )
    .expect("реальний виклик макроса");
    let actual = eval_parsed_expressions(&call, &mut session)
        .expect("виконати макрос у SENS");
    assert_eq!(actual.value.to_string(), "насіння");

    let mut negative = Session::default();
    eval_core_library_source(include_str!("../../../lib/core.lisp"), &mut negative)
        .expect("завантажити незалежне середовище SENS");
    let noncallable = parse_mixed_exact_domain_reasoning_source(
        "lib/forward.lisp",
        "(визначити ствердити-факт! (як-є ()))",
    )
    .expect("прочитати негативну форму");
    let error = eval_parsed_expressions(&noncallable, &mut negative)
        .expect_err("точний Д9-механізм не можна замінити даними");
    assert!(
        error.to_string().contains("exact DEFINE target requires a callable"),
        "неправильна відмова для даних: {error}"
    );
}
