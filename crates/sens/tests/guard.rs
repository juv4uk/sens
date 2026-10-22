use sens::{eval_program, parse_mixed_exact_domain, Session};

const GUARD_SOURCE: &str = include_str!("../../../lib/guard.lisp");

fn eval_guard(source: &str) -> String {
    eval_guard_with_source(source, false)
}

fn eval_guard_ukr(source: &str) -> String {
    eval_guard_with_source(source, true)
}

fn eval_guard_with_source(source: &str, exact_ukr: bool) -> String {
    let mut session = Session::default();
    sens::eval_core_library_source(include_str!("../../../lib/core.lisp"), &mut session).unwrap();
    sens::eval_pinned_reasoning_source(
        "lib/unify.lisp",
        include_str!("../../../lib/unify.lisp"),
        &mut session,
    )
    .unwrap();

    let guard_forms =
        parse_mixed_exact_domain(GUARD_SOURCE).expect("guard library exact-width source");
    sens::eval_parsed_expressions(&guard_forms, &mut session)
        .expect("guard library must load with exact D3/D4 identities");
    let reference_source = include_str!("../../../knowledge/guard-reference.lisp");
    let reference_forms = sens::parse_mixed_exact_domain_guard_reference_source(
        "knowledge/guard-reference.lisp",
        reference_source,
    )
    .expect("curated Guard directory must parse through its path-pinned data reader");
    sens::eval_parsed_expressions(&reference_forms, &mut session).expect(
        "Guard reference entries remain quoted data and executable helpers use exact heads",
    );

    if exact_ukr {
        let forms = parse_mixed_exact_domain(source).expect("exact Ukrainian Guard source");
        sens::eval_parsed_expressions(&forms, &mut session)
            .unwrap_or_else(|e| {
                panic!("exact Ukrainian Guard evaluation failed: {e}\\nsource: {source}")
            })
            .value
            .to_string()
    } else {
        eval_program(source, &mut session)
            .unwrap_or_else(|e| panic!("guard evaluation failed: {e}\\nsource: {source}"))
            .value
            .to_string()
    }
}

#[test]
fn guard_real_ukrainian_lisp_witness_requires_no_commit_freeze() {
    // Той самий SENS-свідок, що й у tests/fixtures; Rust лише спостерігає
    // точний результат Д1, не переобчислюючи закон синхронізації.
    let source = include_str!("../../../tests/fixtures/guard-exact-d3-semantic.lisp");
    let observed = eval_guard_ukr(source);
    assert_eq!(
        observed, "1",
        "Український свідок має довести всі перевірки Guard; фактично: {observed}"
    );
}

#[test]
fn guard_keeps_decision_and_evidence_status_separate() {
    let value = eval_guard(
        r#"(створити-захист-висновок
              (quote warn) (quote confirmed) (quote swarm/tasks)
              (quote auto-sync-disabled) (quote tasks-materialized)
              (quote tasks-not-materialized) (quote stale-projection)
              (quote sync-tasks) (quote (systemd tasks.lisp journal)))"#,
    );
    assert!(value.contains("(decision warn)"));
    assert!(value.contains("(evidence-status confirmed)"));
    assert!(value.contains("(schema guard-1)"));
}

#[test]
fn guard_verifies_sync_and_drift_without_freezing_commits() {
    let ready = eval_guard(
        r#"(захист-синхронізувати-вікно (quote open) (quote completed) (quote recorded)
             (quote (git sync drift-log)))"#,
    );
    assert!(ready.contains("(decision allow)"), "{ready}");
    assert!(ready.contains("continue-independent-commits"), "{ready}");

    let incomplete = eval_guard(
        r#"(захист-синхронізувати-вікно (quote open) (quote pending) (quote recorded)
             (quote (git sync)))"#,
    );
    assert!(incomplete.contains("(decision warn)"), "{incomplete}");
    assert!(
        incomplete.contains("complete-sync-and-preserve-logs"),
        "{incomplete}"
    );

    let missing_drift = eval_guard(
        r#"(захист-синхронізувати-вікно (quote open) (quote completed) (quote missing)
             (quote (git sync)))"#,
    );
    assert!(missing_drift.contains("(decision warn)"), "{missing_drift}");
    assert!(
        missing_drift.contains("record-drift-and-continue"),
        "{missing_drift}"
    );
}

#[test]
fn missing_evidence_is_unknown_not_reject() {
    let value = eval_guard(
        r#"(захист-невідоме (quote swarm/peer) (quote peer-journal-unreadable) (quote inspect-peer))"#,
    );
    assert!(value.contains("(decision unknown)"));
    assert!(value.contains("(evidence-status unresolved)"));
    assert!(value.contains("(route ask-agent)"));
    assert!(value.contains("(route ask-owner)"));
    assert!(value.contains("(route research-web)"));
}

#[test]
fn oracle_and_observation_agreement_allows() {
    let value = eval_guard(
        r#"(захист-порівняти (quote arithmetic) (quote 3/10) (quote 3/10) (quote (oracle runtime)))"#,
    );
    assert!(value.contains("(decision allow)"));
    assert!(value.contains("(evidence-status confirmed)"));
}

#[test]
fn disagreement_warns_and_preserves_both_values() {
    let value = eval_guard(
        r#"(захист-порівняти (quote task-state) (quote ready) (quote missing) (quote (tasks.lisp journal)))"#,
    );
    assert!(value.contains("(decision warn)"));
    assert!(value.contains("(expected ready observed missing)"));
}

#[test]
fn reference_bureau_points_to_authority_workflow_and_evidence() {
    assert_eq!(
        eval_guard(r#"(guard-authority (quote semantic-oracle))"#),
        "(language-contract.lisp crates/sens-cli/src/swarm.rs docs/guard-oracle-node-plan.md)"
    );
    assert_eq!(
        eval_guard(r#"(guard-how-to (quote task-materialization))"#),
        "(edit-tasks.lisp auto-sync-or-sync-tasks verify-projection verify-peer-convergence)"
    );
    assert_eq!(
        eval_guard(r#"(guard-verify (quote agent-messaging))"#),
        "(durable-inbox-entry wakeup-result session-id-not-unknown commit-sha)"
    );
}

#[test]
fn unknown_topic_is_an_honest_unresolved_reference() {
    let value = eval_guard(r#"(guard-reference (quote no-such-topic))"#);
    assert!(value.contains("reference-missing"));
    assert!(value.contains("(decision unknown)"));
    assert!(value.contains("(evidence-status unresolved)"));
    assert!(value.contains("(guidance choose-unknown-route)"));
    assert!(value.contains("(route ask-agent)"));
    assert!(value.contains("(route ask-owner)"));
    assert!(value.contains("(route research-web)"));
}

#[test]
fn agents_can_enumerate_the_reference_desk() {
    let topics = eval_guard(r#"(guard-topics *guard-reference-directory*)"#);
    assert!(topics.contains("language-semantics"));
    assert!(topics.contains("swarm-coordination"));
    assert!(topics.contains("swarm-node-startup"));
    assert!(topics.contains("guix"));
    assert!(topics.contains("documentation-map"));
    assert!(topics.contains("reference-learning"));
    assert!(topics.contains("licenses"));
    assert!(topics.contains("owner-context"));
    assert!(topics.contains("wsm-lisp-filesystem"));
}

#[test]
fn spawn_node_reference_requires_exclusive_state_ownership() {
    assert_eq!(
        eval_guard(r#"(guard-verify (quote swarm-node-startup))"#),
        "(exclusive-data-dir-lock unchanged-identity-on-failed-spawn explicit-task-sync-choice metrics)"
    );
}

#[test]
fn reference_learning_writes_directly_and_lets_evidence_status_rank_entries() {
    assert_eq!(
        eval_guard(r#"(guard-how-to (quote reference-learning))"#),
        "(search-directory-and-guard-reference-all-for-existing-entries state-evidence-status-honestly-confirmed-only-with-real-tests-or-benchmarks write-reference-directly-into-guard-reference-directory never-delete-or-edit-a-superseded-entry-just-let-evidence-status-outrank-it use-propose-inbox-only-for-provisional-notes-not-yet-full-entries)"
    );
    assert_eq!(
        eval_guard(r#"(guard-verify (quote reference-learning))"#),
        "(guard-reference-returns-highest-evidence-status-for-a-topic guard-reference-all-still-lists-outranked-entries evidence-status-defaults-to-unresolved-never-to-confirmed)"
    );
    assert_eq!(
        eval_guard(r#"(guard-authority (quote guix))"#),
        "(../ecosystem/docs/sessions/VIVEKA-FINDINGS-2026-08-24.md manifest.scm channels.scm guix.scm evidence/GUIX-WITNESS-01)"
    );
}

#[test]
fn a_stronger_evidence_status_outranks_an_older_entry_without_deleting_it() {
    // Two competing entries for the same topic, neither in the real
    // *guard-reference-directory* -- proves the ranking mechanism itself,
    // independent of any real content.
    // Exact Ukrainian domain heads only; no unqualified arithmetic count.
    // Structural equality gates output on both original records still present.
    let source = r#"
        (визначити слабке
          (список (як-є reference) (список (як-є topic) (як-є demo))
            (список (як-є evidence-status) (як-є unresolved))
            (список (як-є summary) "old guess")))
        (визначити сильне
          (список (як-є reference) (список (як-є topic) (як-є demo))
            (список (як-є evidence-status) (як-є confirmed))
            (список (як-є summary) "measured and tested")))
        (за-умовою
          ((сторожа--рівні?
             (guard-reference-all (як-є demo) (список слабке сильне))
             (список слабке сильне))
           (список
             (захист-еталон-поле (як-є summary) (guard-reference-find (як-є demo) (список слабке сильне)))
             (захист-еталон-поле (як-є summary) (guard-reference-find (як-є demo) (список сильне слабке)))))
          ((атом? (як-є ())) (як-є ())))
    "#;
    let value = eval_guard_ukr(source);
    assert!(
        value.contains("\"measured and tested\" \"measured and tested\""),
        "the confirmed entry must win regardless of file order, while both entries remain: {value}"
    );
}

#[test]
fn evidence_status_defaults_to_unresolved_not_confirmed_when_absent() {
    let value = eval_guard_ukr(
        "(гвардія-довідка-стан-доказу (список (як-є reference) (список (як-є topic) (як-є demo))))",
    );
    assert_eq!(value, "unresolved");
}

#[test]
fn agents_can_list_curated_frequently_used_tools() {
    let tools = eval_guard(r#"(guard-scripts *guard-script-directory*)"#);
    assert!(tools.contains("oracle-check"));
    assert!(tools.contains("agent-send"));
    assert!(tools.contains("resource-preflight"));
    assert!(tools.contains("bilingual-docs-check"));
    assert!(tools.contains("conformance-check"));
    assert!(!tools.contains("registry-audit"));
}

#[test]
fn script_reference_contains_path_invocation_risk_and_evidence() {
    let tool = eval_guard(r#"(guard-script (quote agent-send))"#);
    assert!(tool.contains("../ecosystem/scripts/agent-send"));
    assert!(tool.contains("/home/agents/ecosystem/scripts/agent-send send"));
    assert!(tool.contains("(risk writes-coordination-log)"));
    assert!(tool.contains("(verify (admitted inbox-id wakeup-result))"));
}

#[test]
fn unknown_script_routes_instead_of_guessing() {
    let tool = eval_guard(r#"(guard-script (quote no-such-tool))"#);
    assert!(tool.contains("tool-missing"));
    assert!(tool.contains("(decision unknown)"));
    assert!(tool.contains("(route ask-agent)"));
    assert!(tool.contains("(route ask-owner)"));
    assert!(tool.contains("(route research-web)"));
}

#[test]
fn guard_compare_reuses_exact_structural_equality_for_nested_states() {
    let same = eval_guard(
        r#"(захист-порівняти
              (quote build)
              (quote ((revision abc123) (status ready)))
              (quote ((revision abc123) (status ready)))
              (quote (oracle observation)))"#,
    );
    assert!(
        same.contains("(decision allow)"),
        "structurally equal records must preserve the invariant: {same}"
    );

    let drift = eval_guard(
        r#"(захист-порівняти
              (quote build)
              (quote ((revision abc123) (status ready)))
              (quote ((revision abc123) (status blocked)))
              (quote (oracle observation)))"#,
    );
    assert!(
        drift.contains("(decision warn)"),
        "nested structural drift must not be treated as equality: {drift}"
    );
    assert!(
        drift.contains("(expected ((revision abc123) (status ready)) observed ((revision abc123) (status blocked)))"),
        "the finding must preserve both structures, not just a rendered verdict: {drift}"
    );
}

#[test]
fn guard_compare_uses_current_ukrainian_d1_d3_d4_and_executes_in_sens() {
    // Перевіряємо поточний український DEFINE, а не старе англійське ім'я.
    let start = GUARD_SOURCE
        .find("(визначити захист-порівняти\n")
        .expect("чинний Lisp має визначати захист-порівняти");
    let end = GUARD_SOURCE[start..]
        .find("\n(визначити захист-синхронізувати-вікно")
        .map(|offset| start + offset)
        .expect("замкнена межа одного DEFINE");
    let definition = &GUARD_SOURCE[start..end];
    assert_eq!(
        parse_mixed_exact_domain(definition)
            .expect("точний читач")
            .len(),
        1
    );
    assert!(definition.contains("(сторожа--рівні? очікуване спостережене)"));
    assert!(!definition.contains("(11110111 "));
    assert!(!definition.contains("(визначити guard-compare"));
    for (observed, verdict) in [
        ("(як-є ((status ready)))", "(decision allow)"),
        ("(як-є ((status broken)))", "(decision warn)"),
    ] {
        let program =
            format!("(захист-порівняти (як-є build) (як-є ((status ready))) {observed} (як-є ()))");
        let actual = eval_guard_ukr(&program);
        assert!(
            actual.contains(verdict),
            "test_id=guard-compare layer=SENS input={program} expected={verdict} actual={actual}"
        );
    }
}

#[test]
fn guard_reference_field_uses_current_ukrainian_lisp_and_executes_in_sens() {
    let start = GUARD_SOURCE
        .find("(визначити захист-еталон-поле\n")
        .expect("чинний український захист-еталон-поле");
    let end = GUARD_SOURCE[start..]
        .find("\n(визначити ")
        .map(|offset| start + offset)
        .expect("завершення визначення");
    let definition = &GUARD_SOURCE[start..end];
    assert_eq!(
        parse_mixed_exact_domain(definition)
            .expect("точний SENS-читач")
            .len(),
        1
    );
    assert!(definition.contains("(функція (поле посилання)"));
    assert!(definition.contains("(захист-еталон-поле-із-запису"));
    assert!(
        !definition.contains("((функція"),
        "виклик D5 FUNCTION як значення заборонено"
    );
    assert!(GUARD_SOURCE.contains("(визначити захист-знайти-запис-у-рядку\n"));
    assert!(GUARD_SOURCE.contains("(визначити захист-еталон-поле-із-запису\n"));
    assert!(definition.contains("(захист-знайти-запис поле (решта посилання))"));
    for forbidden in ["(знайти-за-ключем ", "(001000 ", "(11110111 ", "(assoc "] {
        assert!(
            !definition.contains(forbidden),
            "застаріла викличність: {forbidden}"
        );
    }
    let found = eval_guard_ukr(
        "(захист-еталон-поле (як-є decision) (як-є (guard-finding (decision allow))))",
    );
    assert_eq!(found, "allow", "дійсне SENS-поле: {found}");
    let absent = eval_guard_ukr(
        "(захист-еталон-поле (як-є missing) (як-є (guard-finding (decision allow))))",
    );
    assert_eq!(absent, "()", "відсутнє поле не вигадує значення: {absent}");
}

#[test]
fn guard_field_requires_exact_two_cell_record_in_real_sens() {
    // Читає і виконує саме SENS; Rust тільки звіряє готовий результат.
    // Старе CAR/CDR на атомі та мовчазне відкидання третього поля
    // не можуть давати удаваний доказ.
    for (record, expected) in [
        ("(як-є (decision allow))", "allow"),
        ("(як-є ())", "()"),
        ("(як-є decision)", "()"),
        ("(як-є (decision))", "()"),
        ("(як-є (decision allow extra))", "()"),
        ("(як-є (decision . allow))", "()"),
    ] {
        let source = format!("(захист-еталон-поле-із-запису {record})");
        let actual = eval_guard_ukr(&source);
        assert_eq!(actual, expected,
            "test_id=guard-exact-record layer=SENS input={source} expected={expected} actual={actual}");
    }
}

#[test]
fn guard_reference_data_reader_is_path_pinned_and_keeps_the_directory_as_data() {
    let source = include_str!("../../../knowledge/guard-reference.lisp");
    let parsed = sens::parse_mixed_exact_domain_guard_reference_source(
        "knowledge/guard-reference.lisp",
        source,
    )
    .expect("Guard reference data-only entrypoint");
    assert!(
        parsed.len() > 1,
        "the directory and its callable lookup definitions remain distinct top-level forms"
    );
    assert!(
        sens::parse_mixed_exact_domain_guard_reference_source("lib/guard.lisp", source).is_err(),
        "the legacy W8 data wrapper must not become a general reader"
    );
    let rendered = format!("{:?}", parsed[0].kind);
    assert!(rendered.contains("довідник-гвардії"));
}

#[test]
fn mechanism_selector_named_d4_helpers_execute_real_sens_positive_and_negative() {
    // Не імітуємо SENS у Rust. Перевіряємо саме DEFINE із чинного Lisp.
    // Зовнішній читач каталогу D9 перевіряється окремо: тут D4 ядро
    // мусить виконати обидва нові іменовані замикання.
    let source = include_str!("../../../lib/mechanism-selector.lisp");
    // Завантажуємо повний чинний SENS-модуль, а не вирізаний
    // підрядок helper-ів: точне резидентне оточення та взаємні
    // DEFINE-зв'язування має визначати сама мова, не тестовий зріз.
    // Той самий паспорт та ті самі D3/D7 закони використовує runtime.
    let mut session = Session::default();
    sens::eval_core_library_source(include_str!("../../../lib/core.lisp"), &mut session)
        .expect("SENS D3–D5 core для виконуваних українських імен");
    let definitions = parse_mixed_exact_domain(source).expect("парсер SENS: повний чинний модуль D3–D5");
    sens::eval_parsed_expressions(&definitions, &mut session)
        .expect("усі чинні DEFINE-маршрути реально завантажуються в SENS");

    for (input, expected) in [
        ("(механізм-знайти-маршрут (як-є target) (як-є runner) (як-є ((other runner x) (target runner chosen))))",
         "(target runner chosen)"),
        ("(механізм-знайти-маршрут (як-є target) (як-є absent) (як-є ((other runner x) (target runner chosen))))",
         "()"),
        ("(механізм-оформити-вибір (як-є ()) (як-є target) (як-є runner))",
         "(mechanism-unavailable target runner)"),
        ("(механізм-оформити-вибір (як-є (target runner chosen)) (як-є target) (як-є runner))",
         "(mechanism-selected target runner chosen)"),
    ] {
        let forms = parse_mixed_exact_domain(input)
            .expect("читач SENS не підміняється тестовим парсером");
        let actual = sens::eval_parsed_expressions(&forms, &mut session)
            .unwrap_or_else(|e| panic!("SENS D4 mechanism selector input={input}: {e}"))
            .value.to_string();
        assert_eq!(actual, expected,
            "test_id=mechanism-d4 layer=SENS input={input} expected={expected} actual={actual}");
    }
}


#[test]
fn mechanism_selector_d3_d5_is_executable_without_sid8_or_host_file_reader() {
    // Обчислює справжній SENS. Ніяких Python, JSON, старих SID8-значень
    // або статичних перевірок замість виконання.
    let source = include_str!("../../../lib/mechanism-selector.lisp");
    assert!(!source.contains("(читати-всі"), "host reader недопущений для T5M");
    assert!(!source.contains("(читати-файл"), "host file I/O недопущений для T5M");
    let mut session = Session::default();
    sens::eval_core_library_source(include_str!("../../../lib/core.lisp"), &mut session)
        .expect("чинне українське ядро D3-D5");
    let parsed = parse_mixed_exact_domain(source).expect("точний читач SENS");
    sens::eval_parsed_expressions(&parsed, &mut session)
        .expect("паспорт і маршрути мусять реально визначатися мовою SENS");
    for (input, expected) in [
        ("(реєстр-містить-ідентичність? (як-є атом?) рядки-реєстру-механізму)", true),
        ("(реєстр-містить-ідентичність? (як-є додати) рядки-реєстру-механізму)", true),
        ("(реєстр-містить-ідентичність? 12 рядки-реєстру-механізму)", false),
        ("(тотожне? (перше (вибрати-механізм (як-є атом?) (як-є evaluator))) (як-є mechanism-selected))", true),
        ("(тотожне? (перше (вибрати-механізм (як-є додати) (як-є prolog))) (як-є mechanism-selected))", true),
        ("(тотожне? (перше (вибрати-механізм (як-є атом?) (як-є prolog))) (як-є mechanism-unavailable))", true),
        ("(тотожне? (перше (вибрати-механізм 12 (як-є prolog))) (як-є mechanism-selection-failure))", true),
    ] {
        let forms = parse_mixed_exact_domain(input)
            .expect("доменний читач SENS не замінюється тестовим симулятором");
        let actual = sens::eval_parsed_expressions(&forms, &mut session)
            .unwrap_or_else(|error| panic!("SENS selector input={input}: {error}"))
            .value.as_predicate_bit();
        assert_eq!(actual, Some(expected),
            "test_id=mechanism-native-d3d5 layer=SENS input={input} expected={expected} actual={actual:?}");
    }
}


#[test]
fn function_table_native_d3_d5_routes_and_fail_closed() {
    // Виконуються справжні DEFINE, закони й запити української SENS.
    // Rust — лише тестовий процес; не виконавець чи оракул семантики.
    let source = include_str!("../../../lib/function-table-mechanisms.lisp");
    let mut session = Session::default();
    sens::eval_core_library_source(include_str!("../../../lib/core.lisp"), &mut session)
        .expect("українські домени D3–D5");
    let forms = parse_mixed_exact_domain(source)
        .expect("ратифікований SENS reader читає паспорт");
    sens::eval_parsed_expressions(&forms, &mut session)
        .expect("п'ять законів і весь паспорт повинні виконатися у SENS");
    for (input, expected) in [
        ("(хибне? (порожній? (механізми-функції (як-є додати))))", true),
        ("(хибне? (порожній? (решта (решта (решта (механізми-функції (як-є додати)))))))", true),
        ("(порожній? (решта (решта (решта (решта (механізми-функції (як-є додати)))))))", true),
        ("(порожній? (механізми-функції (як-є повернути)))", true),
        ("(порожній? (механізми-функції (список (як-є додати))))", true),
        ("(порожній? (механізми-функції (як-є додати)))", false),
    ] {
        let query = parse_mixed_exact_domain(input).expect("точна мова запиту SENS");
        let actual = sens::eval_parsed_expressions(&query, &mut session)
            .unwrap_or_else(|error| panic!("test_id=function-table-native layer=SENS input={input}: {error}"))
            .value.as_predicate_bit();
        assert_eq!(actual, Some(expected),
            "test_id=function-table-native layer=SENS input={input} expected={expected} actual={actual:?}");
    }
}
