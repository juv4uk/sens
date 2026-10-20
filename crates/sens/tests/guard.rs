use sens::{eval_program, parse_mixed_exact_domain, Expr, ExprKind, Session};

const GUARD_SOURCE: &str = include_str!("../../../lib/guard.lisp");

fn eval_guard(source: &str) -> String {
    eval_guard_with_source(source, false)
}

fn eval_guard_ukr(source: &str) -> String {
    eval_guard_with_source(source, true)
}

fn eval_guard_with_source(source: &str, exact_ukr: bool) -> String {
    let mut session = Session::default();
    sens::eval_core_library_source(include_str!("../../../lib/core.lisp"),
        &mut session,
    )
    .unwrap();
    sens::eval_pinned_reasoning_source(
        "lib/unify.lisp",
        include_str!("../../../lib/unify.lisp"),
        &mut session,
    )
    .unwrap();

    let guard_forms = parse_mixed_exact_domain(GUARD_SOURCE)
        .expect("guard library exact-width source");
    sens::eval_parsed_expressions(&guard_forms, &mut session)
        .expect("guard library must load with exact D3/D4 identities");
    let reference_source = include_str!("../../../knowledge/guard-reference.lisp");
    let reference_forms = sens::parse_mixed_exact_domain_guard_reference_source(
        "knowledge/guard-reference.lisp",
        reference_source,
    )
    .expect("curated Guard directory must parse through its path-pinned data reader");
    sens::eval_parsed_expressions(&reference_forms, &mut session)
        .expect("Guard reference entries remain quoted data and executable helpers use exact heads");

    if exact_ukr {
        let forms = parse_mixed_exact_domain(source)
            .expect("exact Ukrainian Guard source");
        sens::eval_parsed_expressions(&forms, &mut session)
            .unwrap_or_else(|e| panic!("exact Ukrainian Guard evaluation failed: {e}\\nsource: {source}"))
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
        r#"(make-guard-finding
              (quote warn) (quote confirmed) (quote swarm/tasks)
              (quote auto-sync-disabled) (quote tasks-materialized)
              (quote tasks-not-materialized) (quote stale-projection)
              (quote sync-tasks) (quote (systemd tasks.lisp journal)))"#,
    );
    assert!(value.contains("(decision warn)"));
    assert!(value.contains("(evidence-status confirmed)"));
    assert!(value.contains("(schema guard/1)"));
}

#[test]
fn guard_verifies_sync_and_drift_without_freezing_commits() {
    let ready = eval_guard(
        r#"(guard-sync-window (quote open) (quote completed) (quote recorded)
             (quote (git sync drift-log)))"#,
    );
    assert!(ready.contains("(decision allow)"), "{ready}");
    assert!(ready.contains("continue-independent-commits"), "{ready}");

    let incomplete = eval_guard(
        r#"(guard-sync-window (quote open) (quote pending) (quote recorded)
             (quote (git sync)))"#,
    );
    assert!(incomplete.contains("(decision warn)"), "{incomplete}");
    assert!(incomplete.contains("complete-sync-and-preserve-logs"), "{incomplete}");

    let missing_drift = eval_guard(
        r#"(guard-sync-window (quote open) (quote completed) (quote missing)
             (quote (git sync)))"#,
    );
    assert!(missing_drift.contains("(decision warn)"), "{missing_drift}");
    assert!(missing_drift.contains("record-drift-and-continue"), "{missing_drift}");
}

#[test]
fn missing_evidence_is_unknown_not_reject() {
    let value = eval_guard(
        r#"(guard-unknown (quote swarm/peer) (quote peer-journal-unreadable) (quote inspect-peer))"#,
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
        r#"(guard-compare (quote arithmetic) (quote 3/10) (quote 3/10) (quote (oracle runtime)))"#,
    );
    assert!(value.contains("(decision allow)"));
    assert!(value.contains("(evidence-status confirmed)"));
}

#[test]
fn disagreement_warns_and_preserves_both_values() {
    let value = eval_guard(
        r#"(guard-compare (quote task-state) (quote ready) (quote missing) (quote (tasks.lisp journal)))"#,
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
          ((однакові?
             (guard-reference-all (як-є demo) (список слабке сильне))
             (список слабке сильне))
           (список
             (guard-reference-field (як-є summary) (guard-reference-find (як-є demo) (список слабке сильне)))
             (guard-reference-field (як-є summary) (guard-reference-find (як-є demo) (список сильне слабке)))))
          (так (як-є ())))
    "#;
    let value = eval_guard_ukr(source);
    assert!(
        value.contains("\"measured and tested\" \"measured and tested\""),
        "the confirmed entry must win regardless of file order, while both entries remain: {value}"
    );
}

#[test]
fn evidence_status_defaults_to_unresolved_not_confirmed_when_absent() {
    let value = eval_guard(
        r#"(guard-reference-evidence-status (list (quote reference) (list (quote topic) (quote demo))))"#,
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
        r#"(guard-compare
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
        r#"(guard-compare
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

fn collect_call_head_coordinates(expr: &Expr, coordinates: &mut Vec<(usize, u16)>) {
    let ExprKind::List(items) = &expr.kind else {
        return;
    };
    if let Some(Expr { kind: ExprKind::DomainIdentity(identity), .. }) = items.first() {
        coordinates.push((identity.width(), identity.packed_bits()));
    }
    for child in items.iter() {
        collect_call_head_coordinates(child, coordinates);
    }
}

#[test]
fn guard_compare_uses_only_exact_d3_d4_heads_and_no_w8_equal() {
    let start = GUARD_SOURCE
        .find("(визначити guard-compare\n")
        .expect("Lisp-owned guard-compare must exist");
    let end = GUARD_SOURCE[start..]
        .find("\n(визначити guard-sync-window")
        .map(|offset| start + offset)
        .expect("guard-compare definition must end before guard-sync-window");
    let source = &GUARD_SOURCE[start..end];

    assert!(!source.contains("(11110111 expected observed)"));
    assert!(source.contains("(сторожа--рівні? expected observed)"));

    let parsed = parse_mixed_exact_domain(source)
        .expect("guard-compare must retain exact domain identities");
    assert_eq!(parsed.len(), 1);
    let mut coordinates = Vec::new();
    collect_call_head_coordinates(&parsed[0], &mut coordinates);
    coordinates.sort_unstable();
    coordinates.dedup();

    let widths = coordinates
        .iter()
        .map(|(width, _)| *width)
        .collect::<std::collections::BTreeSet<_>>();
    assert_eq!(
        widths,
        [1usize, 3usize, 4usize].into_iter().collect(),
        "guard-compare keeps a D1 predicate and exact D3/D4 callable identities"
    );
    for required in [(1, 0b1), (3, 0b001), (3, 0b110), (4, 0b0010), (4, 0b0011), (4, 0b1110)] {
        assert!(
            coordinates.contains(&required),
            "guard-compare is missing D{}:{:0width$b}",
            required.0,
            required.1,
            width = required.0
        );
    }
}


#[test]
fn guard_reference_field_uses_exact_d1_d3_d4_ukr_surfaces() {
    let start = GUARD_SOURCE
        .find("(визначити guard-reference-field\n")
        .expect("the live Ukrainian guard accessor must exist");
    let end = GUARD_SOURCE[start..]
        .find("\n(визначити ")
        .map(|offset| start + offset)
        .expect("guard-reference-field must remain one bounded definition");
    let source = &GUARD_SOURCE[start..end];

    assert!(source.contains("(функція (поле посилання)"));
    assert!(source.contains("(функція (запис)"));
    assert!(source.contains("(захист-знайти-запис поле (решта посилання))"));
    assert!(!source.contains("(знайти-за-ключем "));
    assert!(!source.contains("(функція (field reference)"));
    assert!(!source.contains("(функція (entry)"));
    assert!(!source.contains("(друге entry)"));
    assert!(!source.contains("(assoc "));
    for old_head in ["(001000 ", "(11100 ", "(011 ", "(101 ", "(100 ", "(0101 ", "(0011 ", "(0010 ", "(010 ", "(110 ", "(111 ", "(11110111 "] {
        assert!(!source.contains(old_head), "retired numeric head remains: {old_head}");
    }

    let parsed = parse_mixed_exact_domain(source)
        .expect("full укр surfaces must lower to exact domain identities");
    let mut coordinates = Vec::new();
    collect_call_head_coordinates(&parsed[0], &mut coordinates);
    coordinates.sort_unstable();
    coordinates.dedup();
    let widths = coordinates
        .iter()
        .map(|(width, _)| *width)
        .collect::<std::collections::BTreeSet<_>>();
    assert_eq!(
        widths,
        [1usize, 3usize, 4usize].into_iter().collect(),
        "guard-reference-field keeps D1 truth, D3 structure and exact D4 lambda/selector/NULL"
    );
}


#[test]
fn guard_reference_data_reader_is_path_pinned_and_keeps_the_directory_as_data() {
    let source = include_str!("../../../knowledge/guard-reference.lisp");
    let parsed = sens::parse_mixed_exact_domain_guard_reference_source(
        "knowledge/guard-reference.lisp",
        source,
    )
    .expect("Guard reference data-only entrypoint");
    assert!(parsed.len() > 1, "the directory and its callable lookup definitions remain distinct top-level forms");
    assert!(
        sens::parse_mixed_exact_domain_guard_reference_source("lib/guard.lisp", source).is_err(),
        "the legacy W8 data wrapper must not become a general reader"
    );
    let rendered = format!("{:?}", parsed[0].kind);
    assert!(rendered.contains("guard-reference-directory"));
}
