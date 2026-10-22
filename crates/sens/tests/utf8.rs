use sens::{
    eval_parsed_expressions, load_core_library, load_fs_library, load_process_library,
    load_utf8_library, parse_mixed_exact_domain_utf8_source, Session,
};

fn utf8_session() -> Session {
    let mut session = Session::default();
    load_core_library(&mut session).expect("core library");
    // Один і той самий код D10 — першокласний, але незмінний.
    // Після нативного Zig/T5M bootstrap не виконувати ті самі DEFINE вдруге.
    load_utf8_library(&mut session).expect("canonical Zig/T5M UTF-8 library and runtime bridge");
    session
}

#[test]
fn utf8_domain_functions_survive_repeated_loader_and_fs_without_redefinition() {
    let mut session = utf8_session();
    let law = "(кодова-одиниця-кодування-юнікод-8-у-допустимому-діапазоні? 128 128 191)";
    let original = eval_in_utf8_context(law, &mut session);
    assert_eq!(original.as_predicate_bit(), Some(true), "test_id=UTF8-D10-FIRST-LOAD");

    load_utf8_library(&mut session)
        .expect("повторний запит не може перевизначати мовний D10 код");
    load_fs_library(&mut session)
        .expect("FS має використовувати ту саму UTF-8 бібліотеку без другого DEFINE");

    let after = eval_in_utf8_context(law, &mut session);
    assert_eq!(after, original, "test_id=UTF8-D10-SHARED-SENS-CALL");
}

fn eval(source: &str) -> String {
    let mut session = utf8_session();
    eval_in_utf8_context(source, &mut session).to_string()
}

fn eval_in_utf8_context(source: &str, session: &mut Session) -> sens::Value {
    let parsed = parse_mixed_exact_domain_utf8_source("lib/utf8.lisp", source)
        .unwrap_or_else(|error| panic!("UTF-8 test source must lower through its pinned domain reader: {error}"));
    eval_parsed_expressions(&parsed, session)
        .unwrap_or_else(|error| panic!("UTF-8 test source must evaluate: {error}"))
        .value
}

#[test]
fn utf8_pinned_reader_explicitly_admits_decimal_constants_as_d24() {
    let parsed = parse_mixed_exact_domain_utf8_source("lib/utf8.lisp", "255")
        .expect("the pinned UTF-8 numerical boundary accepts its decimal source value");
    assert!(
        matches!(
            parsed[0].kind,
            sens::ExprKind::BinaryNumber(ref value) if value.numeric_domain_width() == Some(24)
        ),
        "the pinned source boundary must preserve the exact D24+ domain"
    );

    let ordinary = sens::parse_mixed_exact_domain("255").expect("ordinary source parses");
    assert!(
        matches!(
            ordinary[0].kind,
            sens::ExprKind::BinaryNumber(ref value) if value.numeric_domain_width() == Some(24)
        ),
        "the ordinary reader must follow the same D24+ decimal contract"
    );

    let alias = parse_mixed_exact_domain_utf8_source(
        "lib/utf8.lisp",
        "(нехай-послідовно ((значення 255)) значення)",
    )
    .expect("full Ukrainian projection is admitted on this pinned source path");
    let sens::ExprKind::List(items) = &alias[0].kind else {
        panic!("expected expanded lambda application");
    };
    assert!(
        matches!(&items[0].kind, sens::ExprKind::List(_)),
        "LET* lowers to a lambda application"
    );
    let compact =
        parse_mixed_exact_domain_utf8_source("lib/utf8.lisp", "(нехай* ((значення 255)) значення)")
            .expect("compact Ukrainian projection parses");
    let sens::ExprKind::List(compact_items) = &compact[0].kind else {
        panic!("expected compact call")
    };
    assert!(
        matches!(&compact_items[0].kind, sens::ExprKind::DomainIdentity(_)),
        "compact head must project"
    );
    let mut session = utf8_session();
    assert_eq!(
        eval_parsed_expressions(&alias, &mut session)
            .expect("expanded D4 LET* call")
            .value
            .to_string(),
        "255",
    );
}

#[test]
fn utf8_d1_predicates_run_in_sens_without_unbound_truth_symbols() {
    // Positive and negative witnesses execute through the current SENS
    // runtime. Rust observes typed results; it does not implement UTF-8 laws.
    let source = include_str!("../../../lib/utf8.lisp");
    for line in source
        .lines()
        .filter(|line| !line.trim_start().starts_with(';'))
    {
        assert!(
            !line.trim_end().ends_with(" так)"),
            "bare truth in executable Lisp: {line}"
        );
        assert!(
            !line.trim_end().ends_with(" ні)"),
            "bare false in executable Lisp: {line}"
        );
    }
    for (program, expected) in [
        (
            "(кодова-одиниця-кодування-юнікод-8-у-допустимому-діапазоні? 128 128 191)",
            "1",
        ),
        (
            "(кодова-одиниця-кодування-юнікод-8-у-допустимому-діапазоні? 192 128 191)",
            "0",
        ),
        ("(це-байт-продовження-кодування-юнікод-8? 128)", "1"),
        ("(це-байт-продовження-кодування-юнікод-8? 127)", "0"),
        ("(це-допустимий-байт-кодування-юнікод-8? 255)", "1"),
        ("(це-допустимий-байт-кодування-юнікод-8? 256)", "0"),
        (
            "(усі-елементи-є-байтами-кодування-юнікод-8? (як-є ()))",
            "1",
        ),
        (
            "(усі-елементи-є-байтами-кодування-юнікод-8? (як-є (65 256)))",
            "0",
        ),
        (
            "(наявні-два-байти-продовження-кодування-юнікод-8? 128 191)",
            "1",
        ),
        (
            "(наявні-два-байти-продовження-кодування-юнікод-8? 128 65)",
            "0",
        ),
    ] {
        let actual = eval(program);
        assert_eq!(
            actual, expected,
            "test_id=utf8-d1 layer=SENS input={program} expected={expected} actual={actual}"
        );
    }
}

/// Ділення D24+ у самій SENS: вирішальна гілка COND мусить мати D1:1,
/// а остача повинна залишатися цілою, не дробовою часткою D5.
#[test]
fn utf8_integer_quotient_and_remainder_execute_in_sens_with_d1_branch() {
    let source = include_str!("../../../lib/utf8.lisp");
    assert!(
        !source.contains("      (так\\n"),
        "неприпустимий невизначений предикат у мовному COND"
    );
    for (program, expected) in [
        ("(кодування-юнікод-8-ціла-частка 0 64)", "0"),
        ("(кодування-юнікод-8-ціла-частка 63 64)", "0"),
        ("(кодування-юнікод-8-ціла-частка 64 64)", "1"),
        ("(кодування-юнікод-8-ціла-частка 65 64)", "1"),
        ("(кодування-юнікод-8-ціла-частка 255 64)", "3"),
        ("(кодування-юнікод-8-ціла-частка 256 64)", "4"),
        ("(кодування-юнікод-8-ціла-остача 255 64)", "63"),
        ("(кодування-юнікод-8-ціла-остача 256 64)", "0"),
    ] {
        let actual = eval(program);
        assert_eq!(actual, expected,
            "test_id=utf8-d24-integer-quotient layer=SENS input={program} expected={expected} actual={actual}");
    }
}

#[test]
fn utf8_decodes_ascii_exactly() {
    assert_eq!(
        eval("(кодування-юнікод-8-декодувати (як-є (65 66 67)))"),
        "(decoded (65 66 67))"
    );
}

#[test]
fn utf8_decodes_multibyte_scalars_exactly() {
    // U+00A2 CENT SIGN, U+20AC EURO SIGN, U+1F600 GRINNING FACE.
    assert_eq!(
        eval("(кодування-юнікод-8-декодувати (як-є (194 162 226 130 172 240 159 152 128)))"),
        "(decoded (162 8364 128512))"
    );
}

#[test]
fn utf8_decodes_valid_bytes_to_a_runtime_string_without_lossy_host_policy() {
    assert_eq!(
        eval("(юнікод-скаляри-рядок (як-є (65 162 8364 128512)))"),
        "\"A¢€😀\""
    );
    assert_eq!(
        eval("(кодування-юнікод-8-декодувати-рядок (як-є (65 194 162 226 130 172 240 159 152 128)))"),
        "(decoded \"A¢€😀\")"
    );
}

#[test]
fn utf8_named_boundary_helper_executes_in_sens_not_anonymous_value_call() {
    // D7 keyboard identities stay in W7. Only externally supplied UTF-8
    // byte sequences use this separate adapter, with no host-side oracle.
    let source = include_str!("../../../lib/utf8.lisp");
    assert!(source.contains("(визначити кодування-юнікод-8-результат-у-рядок"));
    assert!(!source.contains("((функція (розкодоване)"));

    for (program, expected) in [
        (
            "(кодування-юнікод-8-декодувати-рядок (як-є (65 66 67)))",
            "(decoded \"ABC\")",
        ),
        (
            "(кодування-юнікод-8-декодувати-рядок (як-є (192 128)))",
            "(rejected invalid-utf8)",
        ),
        (
            "(кодування-юнікод-8-декодувати-рядок (як-є (65 256)))",
            "(rejected invalid-byte)",
        ),
    ] {
        let actual = eval(program);
        assert_eq!(
            actual, expected,
            "test_id=utf8-external-boundary layer=SENS input={program} expected={expected} actual={actual}"
        );
    }
}

#[test]
fn utf8_encodes_runtime_strings_to_exact_wire_bytes() {
    assert_eq!(eval("(кодування-юнікод-8-кодувати-рядок \"ABC\")"), "(65 66 67)");
    assert_eq!(
        eval("(кодування-юнікод-8-кодувати-рядок \"A¢€😀\")"),
        "(65 194 162 226 130 172 240 159 152 128)"
    );
}

#[test]
fn utf8_encode_decode_round_trip_is_language_owned() {
    assert_eq!(
        eval("(кодування-юнікод-8-декодувати-рядок (кодування-юнікод-8-кодувати-рядок \"Привіт 😀\"))"),
        "(decoded \"Привіт 😀\")"
    );
}

#[test]
fn utf8_rejects_overlong_surrogate_and_out_of_range_sequences() {
    for bytes in [
        "(192 128)",         // overlong 2-byte form
        "(224 128 128)",     // overlong 3-byte form
        "(237 160 128)",     // UTF-16 surrogate U+D800
        "(244 144 128 128)", // above U+10FFFF
    ] {
        assert_eq!(
            eval(&format!("(кодування-юнікод-8-декодувати (як-є {bytes}))")),
            "(rejected invalid-utf8)"
        );
    }
}

#[test]
fn utf8_rejects_truncation_and_bad_continuation() {
    for bytes in ["(226 130)", "(240 159 152)", "(226 65 172)"] {
        assert_eq!(
            eval(&format!("(кодування-юнікод-8-декодувати (як-є {bytes}))")),
            "(rejected invalid-utf8)"
        );
    }
}

#[test]
fn utf8_rejects_non_bytes_before_protocol_interpretation() {
    assert_eq!(
        eval("(кодування-юнікод-8-декодувати (як-є (65 256 66)))"),
        "(rejected invalid-byte)"
    );
    assert_eq!(
        eval("(кодування-юнікод-8-декодувати (як-є (65 -1 66)))"),
        "(rejected invalid-byte)"
    );
}

fn explicitly_typed_d8_equal_call(d3: &[sens::Expr]) -> Vec<sens::Expr> {
    let sens::ExprKind::List(items) = &d3[0].kind else {
        panic!("потрібна форма-виклик")
    };
    let mut parts = items.to_vec();
    parts[0] = sens::Expr {
        kind: sens::ExprKind::DomainIdentity(sens::DomainIdentity::D8(sens::CoreD8::from_word(
            sens::Bit8::new(0b11110111).expect("ратифікована D8-координата"),
        ))),
        span: parts[0].span,
    };
    vec![sens::Expr {
        kind: sens::ExprKind::List(std::rc::Rc::from(parts.into_boxed_slice())),
        span: d3[0].span,
    }]
}

#[test]
fn utf8_atomic_d3_eq_exhaustive_256_bytes_at_five_boundaries() {
    // Збіг восьми бітів із ратифікованим D8 не дає права auto-lift.
    let opaque = parse_mixed_exact_domain_utf8_source("lib/utf8.lisp", "(11110111 0 0)")
        .expect("історичні слова залишаються неявно невикличними");
    let sens::ExprKind::List(opaque_items) = &opaque[0].kind else {
        panic!("потрібна форма-виклик")
    };
    assert!(
        !matches!(&opaque_items[0].kind, sens::ExprKind::DomainIdentity(_)),
        "W8-переносник не надає чинної D8-тотожності"
    );

    // Контракт D3:101 EQ на атомах: однакова числова величина => D1:YES.
    // Вичерпні 256 байтів × 5 включених Unicode UTF8 меж = 1280 запусків.
    let mut session = Session::default();
    let mut checked = 0_usize;
    for byte in 0_u16..=255 {
        for boundary in [0_u16, 224, 237, 240, 244] {
            let source = format!("(101 {byte} {boundary})");
            let parsed = parse_mixed_exact_domain_utf8_source("lib/utf8.lisp", &source)
                .expect("точний виклик D3 EQ");
            let sens::ExprKind::List(items) = &parsed[0].kind else {
                panic!("потрібна форма-виклик")
            };
            assert!(
                matches!(
                    &items[0].kind,
                    sens::ExprKind::DomainIdentity(identity) if identity.width() == 3
                ),
                "{source}: ширина EQ мусить дорівнювати рівно трьом бітам"
            );
            let result = eval_parsed_expressions(&parsed, &mut session)
                .unwrap_or_else(|error| panic!("{source}: {error}"));
            assert_eq!(
                result.value.as_predicate_bit(),
                Some(byte == boundary),
                "{source}: лише точний D1 результат, не Number і не Nil"
            );
            checked += 1;
        }
    }
    assert_eq!(checked, 256 * 5);
}

#[test]
fn utf8_d3_eq_rejects_nonatoms_and_d8_equal_remains_unadmitted() {
    let mut session = Session::default();
    let d3 = parse_mixed_exact_domain_utf8_source("lib/utf8.lisp", "(101 (001 (a b)) (001 (a b)))")
        .expect("синтаксис допустимий");
    let error = eval_parsed_expressions(&d3, &mut session)
        .expect_err("D3 EQ є функцією лише атомарної рівності");
    assert_eq!(error.kind, sens::ErrorKind::Type);

    // D8:EQUAL має окрему ратифіковану тотожність, але сьогодні
    // її виклик у цьому середовищі НЕ допущений. Не відкривати його тестом.
    let d8 = explicitly_typed_d8_equal_call(&d3);
    let sens::ExprKind::List(parts) = &d8[0].kind else {
        panic!("потрібна форма-виклик")
    };
    assert!(matches!(
        &parts[0].kind,
        sens::ExprKind::DomainIdentity(identity) if identity.width() == 8
    ));
    let blocked = eval_parsed_expressions(&d8, &mut session)
        .expect_err("існування D8:11110111 не є дозволом виконання");
    assert_eq!(blocked.kind, sens::ErrorKind::Type);
    assert!(
        blocked.message.contains("D8 11110111"),
        "{}",
        blocked.message
    );
}

#[test]
fn utf8_layer_keeps_process_library_as_a_separate_top_level_load() {
    let mut session = Session::default();
    load_core_library(&mut session).expect("core library");
    load_process_library(&mut session)
        .expect("UTF-8, process and TCP language layers must load sequentially");
}

#[test]
fn utf8_library_loads_from_zig_t5m_words_without_process_host_capabilities() {
    let mut session = Session::default();
    load_core_library(&mut session).expect("core library");
    load_utf8_library(&mut session).expect("UTF-8 library arrives through the Zig T5M bootstrap");
    let name = sens::encode_text7(
        "кодування-юнікод-8-знайти-блок",
        sens::Text7Layout::Uk,
    )
    .expect("current D7 Ukrainian projection");
    let key = name.to_canonical_wire_token();
    assert!(
        matches!(session.environment.get(&key), Some(sens::Value::Closure(_))),
        "the SENS definition is bound under its canonical D7 identity"
    );
    for capability in [
        "process-run-raw",
        "tcp-read-raw",
        "read-file-bytes",
        "записати-байти-файла",
    ] {
        assert!(
            session.environment.get(capability).is_none(),
            "loading UTF-8 semantics alone must not install host capability {capability}"
        );
    }
}

#[test]
fn utf8_helper_returns_exact_d1_predicate_on_boundaries() {
    let mut session = utf8_session();
    for (source, expected) in [
        ("(кодова-одиниця-кодування-юнікод-8-у-допустимому-діапазоні? 0 0 255)", true),
        ("(кодова-одиниця-кодування-юнікод-8-у-допустимому-діапазоні? 255 0 255)", true),
        ("(кодова-одиниця-кодування-юнікод-8-у-допустимому-діапазоні? 256 0 255)", false),
        ("(кодова-одиниця-кодування-юнікод-8-у-допустимому-діапазоні? -1 0 255)", false),
        ("(це-байт-продовження-кодування-юнікод-8? 127)", false),
        ("(це-байт-продовження-кодування-юнікод-8? 128)", true),
        ("(це-байт-продовження-кодування-юнікод-8? 191)", true),
        ("(це-байт-продовження-кодування-юнікод-8? 192)", false),
        ("(це-допустимий-байт-кодування-юнікод-8? 0)", true),
        ("(це-допустимий-байт-кодування-юнікод-8? 255)", true),
        ("(це-допустимий-байт-кодування-юнікод-8? 256)", false),
        ("(усі-елементи-є-байтами-кодування-юнікод-8? (як-є ()))", true),
        ("(усі-елементи-є-байтами-кодування-юнікод-8? (як-є (0 127 255)))", true),
        ("(усі-елементи-є-байтами-кодування-юнікод-8? (як-є (0 256)))", false),
        ("(наявні-два-байти-продовження-кодування-юнікод-8? 128 191)", true),
        ("(наявні-два-байти-продовження-кодування-юнікод-8? 128 192)", false),
    ] {
        let actual = eval_in_utf8_context(source, &mut session);
        assert_eq!(
            actual.as_predicate_bit(),
            Some(expected),
            "{source}: expected an exact D1 bit, never ordinary Number 0/1"
        );
    }
}

const UTF8_D1_LAW: &str = include_str!("../../../tests/semantic/utf8-direct-d1-law.lisp");

/// The executable SENS program compares actual/expected D1 itself.
/// Rust only transports the fixture, executes it, and observes the final bit.
/// No Python or Rust function duplicates the UTF-8 predicate oracle.
#[test]
fn utf8_direct_d1_self_verdict_and_one_bit_mutant() {
    let program = sens::parse_mixed_exact_domain_utf8_source("lib/utf8.lisp", UTF8_D1_LAW)
        .expect("the current pinned UTF-8 reader must parse binary SENS law");
    assert_eq!(
        program.len(),
        2,
        "two structural SENS-owned UTF-8 verdicts; numeric D24 boundaries remain transitional"
    );

    let mut session = utf8_session();
    for (index, form) in program.iter().enumerate() {
        let result = sens::eval_parsed_expressions(std::slice::from_ref(form), &mut session)
            .unwrap_or_else(|error| {
                panic!("test_id=utf8-d1-direct layer=eval fixture=tests/semantic/utf8-direct-d1-law.lisp form={index} error={error}")
            });
        assert_eq!(
            result.value.as_predicate_bit(),
            Some(true),
            "test_id=utf8-d1-direct form={index} SENS self-verdict was not D1:YES: {}",
            result.value
        );
    }

    // Чинне укр-джерело не містить історичних #d1: літералів.
    // Міняємо один семантичний D1:YES/NO у справжній програмі SENS,
    // не порівнюємо довжину UTF-8 проєкцій із різними літерами.
    let original = "(як-є не-список)) ні) так)";
    let flipped = "(як-є не-список)) так) так)";
    assert_eq!(
        UTF8_D1_LAW.matches(original).count(),
        1,
        "має існувати рівно один чинний D1-свідок для мутації"
    );
    let mutant_source = UTF8_D1_LAW.replacen(original, flipped, 1);
    let mutant = sens::parse_mixed_exact_domain_utf8_source("lib/utf8.lisp", &mutant_source)
        .expect("one-bit mutant remains valid SENS source");
    let mut mutant_session = utf8_session();
    assert!(
        sens::eval_parsed_expressions(std::slice::from_ref(&mutant[0]), &mut mutant_session)
            .is_err(),
        "SENS itself must fail closed on the one-bit false verdict"
    );
}
