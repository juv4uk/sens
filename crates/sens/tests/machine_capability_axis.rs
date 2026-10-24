use std::fs;
use std::path::PathBuf;

use sens::semantic_registry_export::semantic_id_for_admitted_surface;
use sens::{load_core_library, lower_program, parse, ExprKind, Session};

fn repo_root() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .parent()
        .and_then(|p| p.parent())
        .expect("repo root")
        .to_path_buf()
}

/// Джерельні десяткові числа — лише людська проєкція точних D24+ слів.
/// Виконує справжній SENS; цитовані протокольні дані лишаються недоторканими.
fn eval_axis_program(
    source: &str,
    session: &mut Session,
) -> Result<sens::EvalResult, sens::LanguageError> {
    let parsed = parse(source)?;
    let exact = sens::source_projection::project_ukr_decimal_integer_literals(&parsed, source)?;
    sens::eval_parsed_expressions(&exact, session)
}

fn session() -> Session {
    let mut session = Session::default();
    load_core_library(&mut session).expect("core must load");
    let source = fs::read_to_string(repo_root().join("lib/machine/capability-axis.lisp"))
        .expect("capability axis source");
    eval_axis_program(&source, &mut session).expect("capability axis must load");
    session
}

#[test]
fn current_exact_domain_identities_project_to_target_neutral_capabilities() {
    let lowered = lower_program(&parse("(додати 2 3)").expect("PLUS source"));
    let ExprKind::DomainCall(add_identity, _) = lowered[0].kind else {
        panic!("current PLUS surface must lower to DomainCall");
    };
    assert_eq!(
        (add_identity.width(), add_identity.packed_bits()),
        (5, 0b01010)
    );

    let lowered = lower_program(&parse("(перше '(a b))").expect("CAR source"));
    let ExprKind::DomainCall(car_identity, _) = lowered[0].kind else {
        panic!("current CAR surface must lower to DomainCall");
    };
    assert_eq!(
        (car_identity.width(), car_identity.packed_bits()),
        (3, 0b100)
    );

    let mut s = session();
    let add = eval_axis_program(
        &format!(
            "(спроможності-для-домену {} {})",
            add_identity.width(),
            add_identity.packed_bits()
        ),
        &mut s,
    )
    .expect("D5 PLUS capability lookup")
    .value
    .to_string();
    assert_eq!(add, "((integer-add bounded-u32-inputs u64-result))");

    let car = eval_axis_program(
        &format!(
            "(спроможності-для-домену {} {})",
            car_identity.width(),
            car_identity.packed_bits()
        ),
        &mut s,
    )
    .expect("D3 CAR capability lookup")
    .value
    .to_string();
    assert_eq!(car, "((pair-field-load head bounded-u64))");

    // Текст «01010» не можна маскувати під D12+ число. Чинний SENS
    // відхиляє несумісний тип; ERROR не тотожне семантичному NO/().
    let quoted_shadow = eval_axis_program(r#"(спроможності-для-домену 5 "01010")"#, &mut s)
        .expect_err("text data cannot impersonate a D12+ numerical domain coordinate");
    assert_eq!(quoted_shadow.kind, sens::ErrorKind::Type);
    assert!(
        quoted_shadow.message.contains("D12+"),
        "SENS must report the exact numeric domain boundary: {quoted_shadow}"
    );
}

#[test]
fn numeric_coordinates_match_the_current_quoted_d24_source_in_real_sens() {
    // Пряма перевірка кожного шару, щоб відрізнити збій декодування даних
    // від числового порівняння і рекурсивного пошуку у виконуваному Lisp.
    let mut s = session();
    for (source, expected) in [
        ("(можливість-правильний-рядок-домену? (друге вісь-спроможностей-машини-версія-3))", "1"),
        ("(можливість-числові-координати-рівні? 5 (перше (друге вісь-спроможностей-машини-версія-3)))", "1"),
        ("(можливість-числові-координати-рівні? 10 (друге (друге вісь-спроможностей-машини-версія-3)))", "1"),
        ("(можливість-числові-координати-рівні? 8 (друге (перше вісь-спроможностей-машини-версія-3)))", "1"),
        ("(можливість-числові-координати-рівні? 4 (перше (друге вісь-спроможностей-машини-версія-3)))", "0"),
        ("(можливість-числові-координати-рівні? 6 (перше (друге вісь-спроможностей-машини-версія-3)))", "0"),
        ("(можливість-числові-координати-рівні? 5 (друге (друге вісь-спроможностей-машини-версія-3)))", "0"),
        ("(можливість-знайти-рядок-домену 5 10 вісь-спроможностей-машини-версія-3)",
            "(5 10 ((integer-add bounded-u32-inputs u64-result)))"),
    ] {
        let actual = eval_axis_program(source, &mut s)
            .unwrap_or_else(|error| panic!("SENS numeric coordinate source={source} error={error}"))
            .value.to_string();
        assert_eq!(actual, expected, "SENS numeric coordinate source={source}");
    }
}

#[test]
fn packed_bits_do_not_cross_domain_widths() {
    let mut s = session();

    assert_eq!(
        eval_axis_program("(спроможності-для-домену 5 10)", &mut s)
            .expect("D5:01010 PLUS")
            .value
            .to_string(),
        "((integer-add bounded-u32-inputs u64-result))"
    );
    assert_eq!(
        eval_axis_program("(спроможності-для-домену 4 10)", &mut s)
            .expect("D4:1010 LOOKUP must not inherit PLUS")
            .value
            .to_string(),
        "()"
    );

    assert_eq!(
        eval_axis_program("(спроможності-для-домену 5 11)", &mut s)
            .expect("D5:01011 DIFFERENCE")
            .value
            .to_string(),
        "((integer-subtract bounded-u64 no-underflow))"
    );
    assert_eq!(
        eval_axis_program("(спроможності-для-домену 4 11)", &mut s)
            .expect("D4:1011 BIND must not inherit DIFFERENCE")
            .value
            .to_string(),
        "()"
    );

    assert_eq!(
        eval_axis_program("(спроможності-для-домену 5 8)", &mut s)
            .expect("D5:01000 ZEROP")
            .value
            .to_string(),
        "((integer-zero-test bounded-nonnegative-u64 internal-bit-d1-boundary))"
    );
    assert_eq!(
        eval_axis_program("(спроможності-для-домену 4 8)", &mut s)
            .expect("D4:1000 CAAR must not inherit ZEROP")
            .value
            .to_string(),
        "()"
    );

    assert_eq!(
        eval_axis_program("(спроможності-для-домену 6 14)", &mut s)
            .expect("D6:001110 ADD1")
            .value
            .to_string(),
        "((integer-increment bounded-u64 no-overflow))"
    );
    assert_eq!(
        eval_axis_program("(спроможності-для-домену 5 14)", &mut s)
            .expect("D5:01110 selector must not inherit D6 ADD1")
            .value
            .to_string(),
        "()"
    );
    assert_eq!(
        eval_axis_program("(спроможності-для-домену 6 15)", &mut s)
            .expect("D6:001111 SUB1")
            .value
            .to_string(),
        "((integer-decrement bounded-u64 no-underflow))"
    );
    assert_eq!(
        eval_axis_program("(спроможності-для-домену 5 15)", &mut s)
            .expect("D5:01111 selector must not inherit D6 SUB1")
            .value
            .to_string(),
        "()"
    );
}

#[test]
fn machine_capability_shapes_use_real_sens_d1_truth_and_falsehood() {
    let mut s = session();
    // Позитивні й негативні форми перевіряє поточний виконавець SENS,
    // не Python-симуляція й не порівняння вихідних рядків.
    let cases = [
        ("(можливість-правильний-рядок-домену? (як-є (5 10 ((integer-add bounded-u32-inputs u64-result)))))", "допустимо"),
        ("(можливість-правильний-рядок-домену? (як-є (5 10 ())))", "допустимо"),
        ("(можливість-правильний-рядок-домену? (як-є (5 10)))", "відхилено"),
        ("(можливість-правильний-рядок-домену? (як-є (5 10 хибне-поле)))", "відхилено"),
        ("(можливість-правильний-рядок-цілі? (як-є (x86-64 witnessed)))", "допустимо"),
        ("(можливість-правильний-рядок-цілі? (як-є (fpga absent)))", "допустимо"),
        ("(можливість-правильний-рядок-цілі? (як-є (fpga unknown)))", "відхилено"),
        ("(можливість-правильний-рядок-цілі? (як-є (x86-64 witnessed зайве)))", "відхилено"),
    ];
    for (predicate, expected) in cases {
        let code = format!(
            "(за-умовою ({predicate} (як-є допустимо)) \
             ((атом? (як-є ())) (як-є відхилено)))"
        );
        let actual = eval_axis_program(&code, &mut s)
            .unwrap_or_else(|e| panic!("SENS не виконав {predicate}: {e}"))
            .value
            .to_string();
        assert_eq!(actual, expected, "неправильний D1 вердикт: {predicate}");
    }
}

#[test]
fn active_machine_capability_axis_has_no_sid8_lookup() {
    let source = fs::read_to_string(repo_root().join("lib/machine/capability-axis.lisp"))
        .expect("capability axis source");

    assert!(source.contains("вісь-спроможностей-машини-версія-3"));
    assert!(source.contains("спроможності-для-домену"));
    assert!(source.contains("вісь-спроможностей-машини-версія-3"));
    assert!(source.contains("свідки-цілей-спроможності-машини-версія-2"));
    assert!(source.contains("статуси-свідків-цілей-машини-версія-1"));
    assert!(!source.contains("machine-capability-legacy-sid-axis"));
    assert!(!source.contains("machine-capabilities-for-sid"));
    assert!(!source.contains("00001100"));
}

#[test]
fn capability_names_do_not_mint_semantic_identities() {
    for capability in [
        "integer-zero-test",
        "integer-add",
        "integer-subtract",
        "integer-multiply",
        "integer-quotient",
        "integer-order-less",
        "integer-order-greater",
        "integer-increment",
        "integer-decrement",
        "identity-compare",
        "conditional-branch",
        "pair-field-store",
        "pair-field-load",
        "bounded-u64",
    ] {
        assert_eq!(
            semantic_id_for_admitted_surface(capability),
            None,
            "{capability} is machine-description data, not a language identity"
        );
    }
}

#[test]
fn unsupported_targets_are_explicitly_unwitnessed() {
    let mut s = session();

    for target in ["arm64", "risc-v", "fpga"] {
        let expression = format!("(статус-свідка-цілі-машини (як-є {target}))");
        let value = eval_axis_program(&expression, &mut s)
            .expect("target status lookup")
            .value
            .to_string();
        assert_eq!(value, "absent");
    }

    let x86 = eval_axis_program("(статус-свідка-цілі-машини (як-є x86-64))", &mut s)
        .expect("x86 witness status")
        .value
        .to_string();
    assert_eq!(x86, "witnessed");
}

#[test]
fn x86_target_witnesses_reference_existing_lowering_names_without_owning_meaning() {
    let source = fs::read_to_string(repo_root().join("lib/machine/capability-axis.lisp"))
        .expect("capability axis");
    let lowering =
        fs::read_to_string(repo_root().join("lib/machine/lowering/semantic-x86-64.lisp"))
            .expect("x86 semantic lowering");

    for name in [
        "машина-знизити-перевірку-нуля-64",
        "машина-знизити-додавання-беззнакових-64-до-форм",
        "машина-знизити-віднімання-беззнакових-64-до-форм",
        "машина-знизити-множення-беззнакових-64-до-форм",
        "машина-знизити-частку-знакових-64-до-форм",
        "машина-знизити-порівняння-порядку-64",
        "машина-знизити-рівність-та-умову-64",
        "машина-знизити-запис-пари-64",
        "знизити-складену-пару-до-машинних-форм",
        "машина-знизити-решту-пари-64",
    ] {
        assert!(source.contains(name), "axis references {name}");
        assert!(
            lowering.contains(&format!("(визначити {name}")),
            "referenced x86 witness {name} must exist"
        );
    }
}
