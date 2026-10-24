//! Path-pinned witness for Lisp-owned filesystem adapter semantics.
//! This narrows full store failures to package lookup or lambda binding.
use sens::{eval_core_library_source, eval_pinned_reasoning_source, eval_program, Session};

fn session() -> Session {
    let mut s = Session::default();
    eval_core_library_source(include_str!("../../../lib/core.lisp"), &mut s).unwrap();
    for (path, source) in [
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
        (
            "lib/persistent-map.lisp",
            include_str!("../../../lib/persistent-map.lisp"),
        ),
        ("lib/world.lisp", include_str!("../../../lib/world.lisp")),
        (
            "lib/content-store.lisp",
            include_str!("../../../lib/content-store.lisp"),
        ),
        (
            "lib/lisp-fs.lisp",
            include_str!("../../../lib/lisp-fs.lisp"),
        ),
    ] {
        eval_pinned_reasoning_source(path, source, &mut s)
            .unwrap_or_else(|e| panic!("bootstrap {path}: {e:?}"));
    }
    s
}

fn observe(s: &mut Session, source: &str) -> String {
    eval_program(source, s)
        .unwrap_or_else(|e| panic!("filesystem witness {source}: {e:?}"))
        .value
        .to_string()
}

#[test]
fn filesystem_commit_stage_has_executable_d1_and_rejects_unknown_stage() {
    let mut s = session();
    for (stage, expected) in [
        ("objects", true),
        ("journal", true),
        ("root-pointer", true),
        ("unknown", false),
    ] {
        let source = format!("(фс-етап-коміту? (як-є {stage}))");
        let result = eval_program(&source, &mut s)
            .unwrap_or_else(|e| panic!("SENS D1 етап коміту {stage}: {e:?}"))
            .value;
        assert_eq!(
            result.as_predicate_bit(), Some(expected),
            "test_id=fs-commit-stage layer=SENS input={source} expected=D1:{expected} actual={result}"
        );
    }
    // Відновлення після коміту: перевіряємо саме обчислений D1-контроль
    // у Lisp, не голий символ так і не правдоподібність хоста.
    for (stage, expected) in [
        ("objects", "(recovered before)"),
        ("journal", "(recovered before)"),
        ("root-pointer", "(recovered after)"),
        ("unknown", "(rejected unknown-commit-stage)"),
        ("(root-pointer)", "(rejected unknown-commit-stage)"),
    ] {
        let source = format!(
            "(відновити-завершену-фіксацію-файлової-системи (як-є before) (як-є after) (як-є {stage}))"
        );
        let result = eval_program(&source, &mut s).unwrap_or_else(|e| {
            panic!("test_id=fs-commit-recovery layer=SENS input={source} error={e:?}")
        });
        assert_eq!(
            result.value.to_string(),
            expected,
            "test_id=fs-commit-recovery layer=SENS input={source} expected={expected} actual={}",
            result.value
        );
    }
    // Реальний SENS зобов'язаний повернути D1:0 ще до D3 EQ над парою.
    // Вкладена та крапкова форма не є атомарним маркером F4.
    for invalid in ["(objects)", "(journal root-pointer)", "(objects . journal)"] {
        let source = format!("(фс-етап-коміту? (як-є {invalid}))");
        let result = eval_program(&source, &mut s)
            .unwrap_or_else(|e| panic!("SENS негативний структурний етап {invalid}: {e:?}"))
            .value;
        assert_eq!(
            result.as_predicate_bit(),
            Some(false),
            "test_id=fs-stage-invalid layer=SENS input={source} expected=D1:0 actual={result}"
        );
    }
}

#[test]
fn filesystem_root_recovery_rejects_compound_stage_before_d3_eq() {
    let mut s = session();
    // Справжній SENS evaluator, не статична перевірка тексту.
    // Навіть root-pointer усередині пари не стає атомарним етапом.
    for invalid in [
        "(root-pointer)",
        "(root-pointer journal)",
        "(root-pointer . journal)",
    ] {
        let source = format!(
            "(відновити-кореневий-пакет-файлової-системи (як-є previous) (як-є candidate) (як-є {invalid}))"
        );
        let result = eval_program(&source, &mut s)
            .unwrap_or_else(|e| panic!(
                "test_id=fs-root-stage layer=SENS input={source} expected=(recovered previous) error={e:?}"
            ));
        assert_eq!(
            result.value.to_string(),
            "(recovered previous)",
            "test_id=fs-root-stage layer=SENS input={source} expected=(recovered previous) actual={}",
            result.value
        );
    }
}

#[test]
fn filesystem_alists_and_journal_version_evaluate_real_d1_without_unbound_truth_names() {
    // Перевіряємо саме виконання Lisp через SENS: поле з NIL як значенням
    // присутнє, порожній ключ — не поле, обидві версії — точні D1.
    let mut s = session();
    for (source, expected) in [
        (
            "(фс-пакет-має-поле? (як-є format) (як-є ((format . ()))) )",
            true,
        ),
        (
            "(фс-пакет-має-поле? (як-є missing) (як-є ((format . ()))))",
            false,
        ),
        ("(фс-пакет-має-поле? (як-є format) (як-є ()))", false),
        ("(фс-журнал-список-пар? (як-є ()))", true),
        ("(фс-журнал-список-пар? (як-є ((name . value))))", true),
        ("(фс-журнал-список-пар? (як-є ((() . value))))", false),
        ("(фс-версія-журналу-чинна? (як-є (0 1)))", true),
        ("(фс-версія-журналу-чинна? (як-є (0 1 2)))", false),
        ("(фс-версія-журналу-чинна? (як-є ()))", false),
    ] {
        let value = eval_program(source, &mut s)
            .unwrap_or_else(|e| {
                panic!(
                "test_id=fs-journal-d1 layer=SENS input={source} expected={expected} error={e:?}"
            )
            })
            .value;
        assert_eq!(
            value.as_predicate_bit(),
            Some(expected),
            "test_id=fs-journal-d1 layer=SENS input={source} expected=D1:{expected} actual={value}"
        );
    }
    // Джерельні мітки (ні 1) — дані протоколу, не D1:NO у COND.
    assert_eq!(observe(&mut s, "*версія-журналу-фс*"), "(ні 1)");
}

#[test]
fn journal_event_fields_are_retrieved_from_a_real_alist() {
    let mut s = session();
    for (field, expected) in [("format", "wsm-fs-event"), ("op", "future-op")] {
        let source = format!(
            "(фс-пакет-поле (quote {field}) (фс-журнал-подія (quote future-op) (quote ())))"
        );
        assert_eq!(observe(&mut s, &source), expected, "assoc field {field}");
    }
    assert_eq!(
        observe(
            &mut s,
            "(фс-пакет-поле (quote missing) (фс-журнал-подія (quote future-op) (quote ())))"
        ),
        "()",
        "unknown envelope keys remain absent, never synthesized"
    );
}

#[test]
fn object_package_and_nonempty_map_addresses_are_structurally_consistent() {
    let mut session = session();
    assert_eq!(
        observe(
            &mut session,
            "(car (рішення-щодо-пакета-об'єкта-файлової-системи (фс-об'єкт-пакет (quote hello))))"
        ),
        "accepted",
        "a canonical object envelope must be valid without foreign EQUAL semantics"
    );
    assert_eq!(
        observe(&mut session, "(фс-об'єкт-адреси (внутрішня-мапа-список (внутрішня-мапа-вставити \"one\" (quote payload) map-empty)))"),
        "(\"one\")",
        "AVL dotted entries must project a proper key list"
    );
}

#[test]
fn content_store_membership_is_an_exact_d1_bit_not_structural_one() {
    let mut session = session();
    for (source, expected) in [
        ("(вміст-сховище-містить? (вміст-сховище-покласти (порожній-вміст-сховище) (знання-вміст-адреса (quote star)) (quote star)) (знання-вміст-адреса (quote star)))", true),
        ("(вміст-сховище-містить? (порожній-вміст-сховище) (знання-вміст-адреса (quote star)))", false),
        ("(фс-містить? (car (фс-записати (фс-порожній) \"x\" (quote star))) \"x\")", true),
        ("(фс-містить? (фс-порожній) \"x\")", false),
    ] {
        let output = eval_program(source, &mut session)
            .unwrap_or_else(|e| panic!("store D1 witness {source}: {e:?}"))
            .value;
        assert_eq!(output.as_predicate_bit(), Some(expected),
            "one-bit predicate must never be returned as structural (1)");
    }
}

#[test]
fn world_fourth_field_uses_d3_projection_not_unadmitted_d6_cadddr() {
    let mut session = session();
    for (source, expected) in [
        ("(світ-метадані (порожній-світ))", "()"),
        ("(світ-метадані (створити-світ (quote ()) (quote ()) (quote (marker))))", "(marker)"),
        ("(світ-метадані (світ-повідомити (створити-світ (quote ()) (quote ()) (quote (marker))) (quote zoo) (quote ((has-fur cat)))))", "(marker)"),
    ] {
        assert_eq!(observe(&mut session, source), expected,
            "World metadata is the fourth cons field, derived from D3");
    }
}

#[test]
fn world_dedup_source_can_export_its_own_knowledge_envelope() {
    let mut session = session();
    let src = "(let ((source (світ-повідомити (порожній-світ) (quote zoo) (quote ((has-fur cat)))))) (car (створити-світ-знання-пакет source (quote zoo))))";
    assert_eq!(observe(&mut session, src), "(format . my-lisp-knowledge)");
}

#[test]
fn world_dedup_can_import_its_exported_knowledge_package() {
    let mut session = session();
    // The import returns (receipt world); the receipt is itself a tagged
    // record (accepted (module ...) (knowledge ...)), not a bare symbol.
    // Probe only its D3 CAR tag, retaining the richer language-owned receipt.
    let src = "(let ((source (світ-повідомити (порожній-світ) (quote zoo) (quote ((has-fur cat)))))) (car (car (імпорт-знання-пакет-світ (порожній-світ) (створити-світ-знання-пакет source (quote zoo))))))";
    assert_eq!(
        observe(&mut session, src),
        "accepted",
        "an exported immutable world package must be reimportable"
    );
}

#[test]
fn world_dedup_two_equal_world_contents_share_one_key() {
    let mut session = session();
    let src = "(let ((source (світ-повідомити (порожній-світ) (quote zoo) (quote ((has-fur cat)))))) (let ((copy (second (імпорт-знання-пакет-світ (порожній-світ) (створити-світ-знання-пакет source (quote zoo)))))) (вміст-сховище-розмір (вміст-сховище-покласти-світ (вміст-сховище-покласти-світ (порожній-вміст-сховище) source) copy))))";
    assert_eq!(observe(&mut session, src), "1");
}

#[test]
fn object_package_fold_consumes_every_valid_package() {
    let mut session = session();
    let source = "(let ((decision (фс-побудувати-об'єкт-сховище (list (фс-об'єкт-пакет (quote first)) (фс-об'єкт-пакет (quote second))) (порожній-вміст-сховище)))) (list (car decision) (вміст-сховище-розмір (second decision))))";
    assert_eq!(
        observe(&mut session, source),
        "(accepted 2)",
        "nonempty packages may not be accepted without insertion"
    );
}

#[test]
fn object_package_fold_rejects_invalid_second_package_without_partial_success() {
    let mut session = session();
    let source = "(фс-побудувати-об'єкт-сховище (list (фс-об'єкт-пакет (quote first)) (list (cons (quote format) (quote wsm-fs-object)) (cons (quote version) (quote (0 1))) (cons (quote address) \"incorrect\") (cons (quote value) (quote second)))) (порожній-вміст-сховище))";
    assert_eq!(observe(&mut session, source), "(rejected address-mismatch)");
}

#[test]
fn object_package_fold_rejects_an_improper_tail() {
    let mut session = session();
    let source = "(фс-побудувати-об'єкт-сховище (cons (фс-об'єкт-пакет (quote first)) (quote broken-tail)) (порожній-вміст-сховище))";
    assert_eq!(
        observe(&mut session, source),
        "(rejected invalid-object-packages)"
    );
}

#[test]
fn referenced_root_can_project_its_real_object_and_binding_lists() {
    let mut session = session();
    let prefix = "(let* ((value (quote (hello world))) (written (фс-записати (фс-порожній) \"notes/today\" value)) (fs (car written)) (root (фс-корінь-пакет fs)))";
    let source = format!("{prefix} (list (фс-пакет-поле (quote objects) root) (фс-пакет-поле (quote bindings) root)))");
    assert_eq!(
        observe(&mut session, &source),
        "((\"(hello world)\") ((\"notes/today\" . \"(hello world)\")))"
    );
}

#[test]
fn referenced_root_has_both_address_lists_in_its_supplied_store() {
    let mut session = session();
    let prefix = "(let* ((value (quote (hello world))) (written (фс-записати (фс-порожній) \"notes/today\" value)) (fs (car written)) (root (фс-корінь-пакет fs)))";
    let source = format!("{prefix} (list (усі-адреси-об'єктів-файлової-системи-наявні? (фс-пакет-поле (quote objects) root) (фс-об'єкти fs)) (усі-адреси-зв'язувань-у-файловій-системі-наявні? (фс-пакет-поле (quote bindings) root) (фс-об'єкти fs))))");
    let result = eval_program(&source, &mut session)
        .unwrap_or_else(|e| panic!("referenced root D1 validators {source}: {e:?}"))
        .value
        .to_string();
    assert_eq!(result, "(1 1)");
}

#[test]
fn referenced_root_rebuilds_its_binding_map_without_nil_tail_access() {
    let mut session = session();
    let source = "(let* ((value (quote (hello world))) (written (фс-записати (фс-порожній) \"notes/today\" value)) (root (фс-корінь-пакет (car written)))) (внутрішня-мапа-отримати \"notes/today\" (фс-зв'язки-з-список (фс-пакет-поле (quote bindings) root) map-empty)))";
    assert_eq!(observe(&mut session, source), "(\"(hello world)\")");
}

#[test]
fn referenced_root_decisions_isolate_the_rejected_stage() {
    let mut session = session();
    let prefix = "(let* ((value (quote (hello world))) (written (фс-записати (фс-порожній) \"notes/today\" value)) (fs (car written)) (root (фс-корінь-пакет fs)) (object (фс-об'єкт-пакет value)))";
    let cases = [
        (
            "(рішення-щодо-кореневого-пакета-файлової-системи root)",
            "accepted",
        ),
        (
            "(рішення-щодо-пакета-об'єкта-файлової-системи object)",
            "accepted",
        ),
        (
            "(фс-побудувати-об'єкт-сховище (list object) (порожній-вміст-сховище))",
            "accepted",
        ),
        ("(фс-відновити-корінь root (list object))", "accepted"),
    ];
    for (form, expected_tag) in cases {
        let expression = format!("{prefix} (car {form}))");
        let actual = observe(&mut session, &expression);
        assert_eq!(
            actual, expected_tag,
            "decision diverged at {form}; use full envelopes to locate rejection"
        );
    }
}

#[test]
fn referenced_root_rebuild_is_a_separate_atomic_witness() {
    let mut session = session();
    let source = "(let* ((value (quote (hello world))) (written (фс-записати (фс-порожній) \"notes/today\" value)) (fs (car written)) (root (фс-корінь-пакет fs)) (object (фс-об'єкт-пакет value))) (car (фс-відновити-корінь root (list object))))";
    assert_eq!(observe(&mut session, source), "accepted");
}

#[test]
fn one_object_store_has_a_bounded_reconstruction_witness() {
    let mut session = session();
    assert_eq!(
        observe(&mut session,
            "(car (фс-побудувати-об'єкт-сховище (list (фс-об'єкт-пакет (quote hello))) (порожній-вміст-сховище)))"),
        "accepted",
        "one canonical object envelope should enter the immutable content store"
    );
    assert_eq!(
        observe(&mut session,
            "(car (фс-відновити-корінь (фс-корінь-пакет (фс-порожній)) (list (фс-об'єкт-пакет (quote hello)))))"),
        "accepted",
        "an unreferenced but valid object must not corrupt an otherwise empty root"
    );
}

#[test]
fn empty_root_can_be_reconstructed_without_object_packages() {
    let mut session = session();
    assert_eq!(
        observe(
            &mut session,
            "(car (фс-відновити-корінь (фс-корінь-пакет (фс-порожній)) (quote ())))"
        ),
        "accepted",
        "an empty root has no missing-address proof obligation"
    );
}

#[test]
fn referenced_address_checks_are_d1_and_fail_closed() {
    let mut session = session();
    for (source, expected) in [
        ("(усі-адреси-об'єктів-файлової-системи-наявні? (quote ()) (порожній-вміст-сховище))", true),
        ("(усі-адреси-об'єктів-файлової-системи-наявні? (quote missing) (порожній-вміст-сховище))", false),
        ("(усі-адреси-об'єктів-файлової-системи-наявні? (quote (missing)) (порожній-вміст-сховище))", false),
        ("(усі-адреси-зв'язувань-у-файловій-системі-наявні? (quote ()) (порожній-вміст-сховище))", true),
        ("(усі-адреси-зв'язувань-у-файловій-системі-наявні? (quote ((a . missing))) (порожній-вміст-сховище))", false),
    ] {
        let actual = eval_program(source, &mut session)
            .unwrap_or_else(|e| panic!("D1 address validation {source}: {e:?}"))
            .value;
        assert_eq!(actual.as_predicate_bit(), Some(expected),
            "the filesystem must never use host T/NIL as a D1 result");
    }
}

#[test]
fn root_proper_list_validation_is_exact_d1_and_rejects_dotted_tails() {
    let mut session = session();
    for (value, expected) in [
        ("()", true),
        ("(a b)", true),
        ("(a . b)", false),
        ("a", false),
    ] {
        let expr = format!("(внутрішній-правильний-список? (quote {value}))");
        let actual = eval_program(&expr, &mut session)
            .unwrap_or_else(|e| panic!("D1 proper list predicate {expr}: {e:?}"))
            .value;
        assert_eq!(
            actual.as_predicate_bit(),
            Some(expected),
            "proper list checks must never consume host T/NIL or force empty tails"
        );
    }
}

#[test]
fn world_module_membership_is_d1_and_not_unary_cons() {
    let mut session = session();
    for (src, expected) in [
        ("(внутрішній-світ-модуль-відсутній? (порожній-світ) (як-є zoo))", true),
        ("(світ-модуль-відомий? (порожній-світ) (як-є zoo))", false),
        ("(світ-модуль-відомий? (світ-повідомити (порожній-світ) (як-є zoo) (як-є ((has-fur cat)))) (як-є zoo))", true),
    ] {
        let result = eval_program(src, &mut session)
            .unwrap_or_else(|e| panic!("world module membership {src}: {e:?}")).value;
        assert_eq!(result.as_predicate_bit(), Some(expected), "{src}");
    }
}

#[test]
fn world_module_name_symbol_law_is_d1_and_rejects_non_symbols() {
    let mut session = session();
    for (value, expected) in [
        ("(quote zoo)", true),
        ("\"zoo\"", false),
        ("7", false),
        ("(quote (zoo))", false),
        ("(quote ())", false),
        // D1:1/D1:0 є атомами, але не текстовими символами.
        // Без явного D1 guard D8 WRITE повертає runtime-помилку.
        ("(атом? (як-є ()))", false),
        ("(хибне? (атом? (як-є ())))", false),
    ] {
        let code = format!("(внутрішній-символ? {value})");
        let observed = eval_program(&code, &mut session)
            .unwrap_or_else(|e| panic!("world module name {code}: {e:?}"))
            .value;
        assert_eq!(observed.as_predicate_bit(), Some(expected), "{code}");
    }
}

#[test]
fn world_d1_symbol_guard_must_precede_d8_write() {
    // Негативний SENS-свідок: голий D8 WRITE не приймає D1,
    // тому світ мусить відхилити предикат ще до цього механізму.
    let mut s = session();
    let bare = "(значення-у-текст (атом? (як-є ())))";
    assert!(
        eval_program(bare, &mut s).is_err(),
        "test_id=world-d1-d8-bare expected=TYPE_ERROR input={bare}"
    );
    for value in ["(атом? (як-є ()))", "(хибне? (атом? (як-є ())))"] {
        let source = format!("(внутрішній-символ? {value})");
        let actual = eval_program(&source, &mut s)
            .unwrap_or_else(|e| panic!("test_id=world-d1-d8-guard input={source} error={e:?}"))
            .value;
        assert_eq!(
            actual.as_predicate_bit(),
            Some(false),
            "test_id=world-d1-d8-guard input={source} expected=D1:0 actual={actual}"
        );
    }
}

#[test]
fn world_knowledge_package_version_is_pair_safe_and_exact_d1() {
    let mut session = session();
    for (left, right, expected) in [
        ("(0 1)", "(0 1)", true),
        ("(0 1)", "(0 2)", false),
        ("(0 1)", "(0)", false),
        ("(0 1)", "()", false),
    ] {
        let code = format!("(внутрішня-рівність-версій (quote {left}) (quote {right}))");
        let value = eval_program(&code, &mut session)
            .unwrap_or_else(|e| panic!("pair-safe package version {code}: {e:?}"))
            .value;
        assert_eq!(value.as_predicate_bit(), Some(expected), "{code}");
    }
}

#[test]
fn root_commit_equality_is_structural_and_d1_only() {
    let mut session = session();
    for (a, b, expected) in [
        ("(a (b . c))", "(a (b . c))", true),
        ("(a (b . c))", "(a (b . d))", false),
        ("()", "()", true),
        ("()", "(a)", false),
        ("(a)", "()", false),
    ] {
        let source = format!("(внутрішня-рівність-структур (quote {a}) (quote {b}))");
        let value = eval_program(&source, &mut session)
            .unwrap_or_else(|e| panic!("structural D1 comparison {source}: {e:?}"))
            .value;
        assert_eq!(
            value.as_predicate_bit(),
            Some(expected),
            "root commit must compare full data, not SHA or host truth"
        );
    }
}

#[test]
fn root_envelope_accepts_its_own_schema_without_object_only_fields() {
    let mut session = session();
    assert_eq!(
        observe(&mut session, "(car (рішення-щодо-кореневого-пакета-файлової-системи (фс-корінь-пакет (фс-порожній))))"),
        "accepted",
        "root metadata consists of format/version/revision/bindings/objects, not an address/value pair"
    );
    assert_eq!(
        observe(
            &mut session,
            "(фс-пакет-поле (quote address) (фс-корінь-пакет (фс-порожній)))"
        ),
        "()",
        "the absent object address remains absent in a root envelope"
    );
}

#[test]
fn empty_object_store_uses_an_admitted_two_argument_lisp_closure() {
    let mut s = session();
    assert_eq!(
        observe(
            &mut s,
            "(фс-побудувати-об'єкт-сховище (quote ()) (порожній-вміст-сховище))"
        ),
        "(accepted ())",
        "nested reconstruction must not shadow the two-argument closure"
    );
}

#[test]
fn derived_macro_binds_list_values_as_one_variable() {
    let mut s = session();
    assert_eq!(
        observe(&mut s, "(нехай-похідне ((x (list 4 5))) (car x))"),
        "4"
    );
    assert_eq!(
        observe(&mut s, "(нехай-похідне ((x (фс-побудувати-об'єкт-сховище (quote ()) (порожній-вміст-сховище)))) (car x))"),
        "accepted"
    );
}

#[test]
fn journal_module_probe_fail_closed_on_malformed_event() {
    // Це справжній виконавець SENS із чинним lib/knowledge.lisp.
    // Виклики використовують канонічну українську проєкцію D3 QUOTE,
    // не англомовне сумісне ім’я; результат оцінює SENS, а не Python.
    // Атом, одноелементна форма та крапковий хвіст не мають
    // другого поля: D4 «друге» у цих випадках заборонене.
    let mut s = session();
    for (journal, expected) in [
        ("()", false),
        ("(tell)", false),
        ("((tell))", false),
        ("((tell . зіпсоване))", false),
        ("(зіпсоване)", false),
        ("((tell чужий факт))", false),
        ("((tell чужий факт) (tell зоря факт))", true),
        ("((tell зоря факт))", true),
    ] {
        let code = format!("(журнал-містить-записи-модуля? (як-є зоря) (як-є {journal}))");
        let actual = eval_program(&code, &mut s)
            .unwrap_or_else(|error| panic!("SENS не виконав {code}: {error:?}"))
            .value;
        assert_eq!(
            actual.as_predicate_bit(),
            Some(expected),
            "хибне або недоведене членство модуля: {journal}"
        );
    }
}
