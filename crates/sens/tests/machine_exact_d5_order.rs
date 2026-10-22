use sens::{eval_program, load_core_library, lower_program, parse, ExprKind, Session};
use std::fs;
use std::path::PathBuf;

fn repo_root() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../..")
}

fn load_lisp_file(path: &str, session: &mut Session) {
    let path = repo_root().join(path);
    let source = fs::read_to_string(&path)
        .unwrap_or_else(|error| panic!("{} must exist: {error}", path.display()));
    eval_program(&source, session)
        .unwrap_or_else(|error| panic!("{} must load as ordinary sens: {error}", path.display()));
}

fn machine_session() -> Session {
    let mut session = Session::default();
    load_core_library(&mut session).expect("core");
    load_lisp_file("lib/machine/encoding/x86-64.lisp", &mut session);
    load_lisp_file("lib/machine/admission/x86-64.lisp", &mut session);
    load_lisp_file("lib/machine/capability-axis.lisp", &mut session);
    load_lisp_file("lib/machine/lowering/semantic-x86-64.lisp", &mut session);
    session
}

fn parse_bytes(rendered: &str) -> Vec<u8> {
    rendered
        .trim_start_matches('(')
        .trim_end_matches(')')
        .split_whitespace()
        .map(|token| token.parse::<u8>().expect("machine byte"))
        .collect()
}

#[derive(Debug, PartialEq, Eq)]
struct OrderTail {
    condition_code: u8,
    set_register: u8,
    result_register: u8,
}

fn decode_order_tail(bytes: &[u8]) -> Option<OrderTail> {
    // Two MOV r64,imm64 instructions = 20 bytes.
    let tail = bytes.get(20..)?;
    let [cmp_rex, cmp_opcode, cmp_modrm, set_prefix, set_opcode, set_modrm, movzx_rex, movzx_prefix, movzx_opcode, movzx_modrm, ret] =
        tail
    else {
        return None;
    };

    // CMP rax, rcx.
    if (*cmp_rex, *cmp_opcode, *cmp_modrm) != (0x48, 0x39, 0xC8) {
        return None;
    }
    if *set_prefix != 0x0F || !matches!(*set_opcode, 0x9C | 0x9F) {
        return None;
    }
    if (*set_modrm >> 6) != 0b11 {
        return None;
    }
    let condition_code = set_opcode - 0x90;
    let set_register = set_modrm & 0b111;

    // MOVZX rax, al.
    if (*movzx_rex, *movzx_prefix, *movzx_opcode) != (0x48, 0x0F, 0xB6)
        || (*movzx_modrm >> 6) != 0b11
    {
        return None;
    }
    let result_register = (movzx_modrm >> 3) & 0b111;
    if (movzx_modrm & 0b111) != set_register || *ret != 0xC3 {
        return None;
    }

    Some(OrderTail {
        condition_code,
        set_register,
        result_register,
    })
}

fn x86_register_field_bits_use_real_d5_numeric_comparison() {
    // Виконуємо чинні Lisp-визначення через SENS; Rust тут лише runner.
    // D3 EQ залишається для атомів ISA, але не для чисел D24+.
    let source = fs::read_to_string(repo_root().join("lib/machine/encoding/x86-64.lisp"))
        .expect("актуальний український машинний кодер");
    let marker = "(визначити машина-числа-рівні?";
    let start = source.find(marker).expect("чинна D5 числова рівність");
    let end = source[start..]
        .find("\n; REX —")
        .map(|offset| start + offset)
        .expect("кінець лише двох числових селекторів");
    let definitions = &source[start..end];
    assert!(
        !definitions.contains("(тотожне? код "),
        "D3 EQ не може порівнювати математичне D24+"
    );
    assert_eq!(definitions.matches("(машина-числа-рівні? код ").count(), 32);

    let mut session = Session::default();
    load_core_library(&mut session).expect("живий SENS Core4");
    let parsed = parse(definitions).expect("дійсний Lisp");
    let exact = sens::source_projection::project_ukr_decimal_integer_literals(&parsed, definitions)
        .expect("точний D24+ з людських десяткових чисел");
    sens::eval_parsed_expressions(&exact, &mut session)
        .expect("справжній SENS визначає три функції");

    for (input, low, high) in [
        ("0", "0", "0"),
        ("1", "1", "0"),
        ("7", "7", "0"),
        ("8", "0", "1"),
        ("15", "7", "1"),
        ("-1", "()", "()"),
        ("16", "()", "()"),
    ] {
        for (function, expected) in [
            ("машина-молодші-три-біти", low),
            ("машина-старший-біт", high),
        ] {
            let expression = format!("({function} {input})");
            let parsed = parse(&expression).expect("український виклик SENS");
            let exact =
                sens::source_projection::project_ukr_decimal_integer_literals(&parsed, &expression)
                    .expect("точний D24+ аргумент");
            let actual = sens::eval_parsed_expressions(&exact, &mut session)
                .unwrap_or_else(|error| panic!("реальний SENS {expression}: {error}"))
                .value
                .to_string();
            assert_eq!(actual, expected, "{expression}");
        }
    }
}

#[test]
fn machine_u3_projection_executes_d24_law_without_encoded_literals() {
    let source = fs::read_to_string(repo_root().join("lib/machine/encoding/x86-64.lisp"))
        .expect("чинний український кодер x86");
    let marker = "(визначити машина-проєктувати-три-біти-до-механізму";
    let start = source.find(marker).expect("закон u3");
    let end = source[start + 1..]
        .find("\n(визначити ")
        .map(|offset| start + 1 + offset)
        .expect("наступний SENS закон");
    let definition = &source[start..end];
    assert!(
        !definition.contains("#b1") && !definition.contains("#d0"),
        "машинна програма не повинна залежати від source-era літералів"
    );
    let parsed = parse(definition).expect("SENS читає український DEFINE");
    let exact = sens::source_projection::project_ukr_decimal_integer_literals(&parsed, definition)
        .expect("математичні операнди точно належать D24+");
    let mut session = Session::default();
    load_core_library(&mut session).expect("справжній Core4");
    sens::eval_parsed_expressions(&exact, &mut session).expect("справжнє SENS DEFINE");
    for (input, expected) in [
        ("-1", "()"),
        ("0", "0"),
        ("1", "1"),
        ("6", "6"),
        ("7", "7"),
        ("8", "()"),
    ] {
        let call = format!("(машина-проєктувати-три-біти-до-механізму {input})");
        let parsed = parse(&call).expect("SENS виклик u3");
        let exact = sens::source_projection::project_ukr_decimal_integer_literals(&parsed, &call)
            .expect("точна D24+ проєкція");
        let actual = sens::eval_parsed_expressions(&exact, &mut session)
            .unwrap_or_else(|error| panic!("SENS {call}: {error}"))
            .value
            .to_string();
        assert_eq!(actual, expected, "{call}");
    }
}

#[test]
fn native_d24_numeric_equality_runs_current_x86_lisp_in_sens() {
    // Генератор покриття вже виведено з ужитку. Читаємо діючий закон
    // безпосередньо з українського x86-кодувальника й виконуємо його в SENS.
    let source = fs::read_to_string(repo_root().join("lib/machine/encoding/x86-64.lisp"))
        .expect("чинне українське джерело кодера x86");
    let marker = "(визначити машина-числа-рівні?";
    let start = source.find(marker).expect("чинне D5 визначення числової рівності");
    let end = source[start..]
        .find("\n(визначити машина-молодші-три-біти")
        .map(|offset| start + offset)
        .expect("межа визначення числової рівності");
    let definition = &source[start..end];
    assert!(!definition.contains("(тотожне?"),
            "D3 EQ не є математичною рівністю D24+");
    assert!(definition.contains("(менше? ліве праве)")
            && definition.contains("(менше? праве ліве"),
            "живий D5 закон має перевіряти обидва строгі порядки");

    let mut session = Session::default();
    load_core_library(&mut session).expect("чинний SENS Core4");
    let parsed = parse(definition).expect("український Lisp визначає D5 закон");
    let exact = sens::source_projection::project_ukr_decimal_integer_literals(
        &parsed, definition
    ).expect("точні D24+ числові операнди");
    sens::eval_parsed_expressions(&exact, &mut session)
        .expect("справжній SENS визначає числову рівність");
    for (left, right, expected) in [
        ("0", "0", true),
        ("1", "1", true),
        ("7", "7", true),
        ("0", "1", false),
        ("2", "1", false),
        ("-3", "-3", true),
        ("-3", "2", false),
        ("2", "-3", false),
    ] {
        let call = format!("(машина-числа-рівні? {left} {right})");
        let parsed = parse(&call).expect("український виклик SENS");
        let exact = sens::source_projection::project_ukr_decimal_integer_literals(
            &parsed, &call
        ).expect("точна числова проєкція D24+");
        let actual = sens::eval_parsed_expressions(&exact, &mut session)
            .unwrap_or_else(|error| panic!("SENS D24+ {call}: {error}"))
            .value;
        assert_eq!(
            actual.as_predicate_bit(), Some(expected),
            "SENS D1 predicate: {call}"
        );
    }
    // Уже чинний CI виконує цей тест: разом з D5 законом перевіряємо
    // реальне застосування до байтових регістрових полів x86.
    x86_register_field_bits_use_real_d5_numeric_comparison();

    // Справжнє SENS-обчислення одного D24+ закону замість
    // 256 числових D3 EQ. Rust лише запускає чинний Lisp.
    let encoder = fs::read_to_string(repo_root().join("lib/machine/encoding/x86-64.lisp"))
        .expect("поточний кодер зміщення x86");
    let start = encoder
        .find("(визначити машина-байт-восьмибітного-зсуву")
        .expect("дійсний закон signed disp8");
    let end = encoder[start + 1..]
        .find("\n(визначити ")
        .map(|offset| start + 1 + offset)
        .expect("межа закону disp8");
    let definition = &encoder[start..end];
    for required in [
        "(менше? зміщення -128)",
        "(більше? зміщення 127)",
        "(менше? зміщення 0)",
        "(додати зміщення 256)",
    ] {
        assert!(
            definition.contains(required),
            "мовний закон SENS: {required}"
        );
    }
    assert!(
        !definition.contains("(ціле? зміщення)"),
        "D5:01001 NUMBERP не має викличного механізму; D24+ операнди типізовано reader-ом"
    );
    assert!(
        !definition.contains("(тотожне? зміщення "),
        "D3 EQ не є математичною D24+ рівністю"
    );

    let parsed = parse(definition).expect("українська SENS функція");
    let exact = sens::source_projection::project_ukr_decimal_integer_literals(&parsed, definition)
        .expect("точна D24+ проєкція");
    let mut session = Session::default();
    load_core_library(&mut session).expect("канонічний Core4");
    sens::eval_parsed_expressions(&exact, &mut session).expect("визначити SENS функцію disp8");
    for (input, expected) in [
        ("-129", "()"),
        ("-128", "128"),
        ("-1", "255"),
        ("0", "0"),
        ("1", "1"),
        ("127", "127"),
        ("128", "()"),
    ] {
        let call = format!("(машина-байт-восьмибітного-зсуву {input})");
        let parsed = parse(&call).expect("український виклик");
        let exact = sens::source_projection::project_ukr_decimal_integer_literals(&parsed, &call)
            .expect("точний математичний операнд");
        let actual = sens::eval_parsed_expressions(&exact, &mut session)
            .unwrap_or_else(|error| panic!("SENS {call}: {error}"))
            .value
            .to_string();
        assert_eq!(actual, expected, "байт зміщення: {call}");
    }
    let rejection = eval_program("(машина-байт-восьмибітного-зсуву (як-є ()))", &mut session)
        .expect_err("нечисловий () має викликати точну помилку D24+");
    assert!(
        rejection
            .message
            .contains("math requires explicit D24+ operands"),
        "структура () не є неявним математичним числом: {rejection}"
    );
}

#[test]
fn current_order_surfaces_lower_to_exact_d5_identities() {
    for (source, expected_bits) in [("(менше? 2 3)", 0b11010), ("(більше? 3 2)", 0b11011)]
    {
        let lowered = lower_program(&parse(source).expect("current D5 order source"));
        let ExprKind::DomainCall(identity, args) = &lowered[0].kind else {
            panic!("{source} must lower to exact DomainCall");
        };
        assert_eq!(identity.width(), 5);
        assert_eq!(identity.packed_bits(), expected_bits);
        assert_eq!(args.len(), 2);
    }
}

#[test]
fn bounded_order_predicates_reach_admitted_internal_bit_bytes() {
    let mut session = machine_session();

    for (packed_bits, capability) in [
        (
            26,
            "((integer-order-less bounded-nonnegative-i63 internal-bit-d1-boundary))",
        ),
        (
            27,
            "((integer-order-greater bounded-nonnegative-i63 internal-bit-d1-boundary))",
        ),
    ] {
        assert_eq!(
            eval_program(
                &format!("(machine-capabilities-for-domain 5 {packed_bits})"),
                &mut session,
            )
            .expect("order capability")
            .value
            .to_string(),
            capability
        );
    }

    let less_forms = eval_program(
        "(машина-знизити-порівняння-порядку-64 5 26 2 3)",
        &mut session,
    )
    .expect("LESSP forms")
    .value
    .to_string();
    assert_eq!(
        less_forms,
        "((mov-r64-imm64 rax 2) (mov-r64-imm64 rcx 3) (cmp-r64-r64 rax rcx) (setl-r8 al) (movzx-r64-r8 rax al) (ret))"
    );

    let less_bytes = eval_program(
        "(машина-кодувати-поточний-біт-порядку 5 26 2 3)",
        &mut session,
    )
    .expect("LESSP bytes")
    .value
    .to_string();
    assert_eq!(
        decode_order_tail(&parse_bytes(&less_bytes)),
        Some(OrderTail {
            condition_code: 12,
            set_register: 0,
            result_register: 0,
        })
    );

    let greater_forms = eval_program(
        "(машина-знизити-порівняння-порядку-64 5 27 3 2)",
        &mut session,
    )
    .expect("GREATERP forms")
    .value
    .to_string();
    assert_eq!(
        greater_forms,
        "((mov-r64-imm64 rax 3) (mov-r64-imm64 rcx 2) (cmp-r64-r64 rax rcx) (setg-r8 al) (movzx-r64-r8 rax al) (ret))"
    );

    let greater_bytes = eval_program(
        "(машина-кодувати-поточний-біт-порядку 5 27 3 2)",
        &mut session,
    )
    .expect("GREATERP bytes")
    .value
    .to_string();
    assert_eq!(
        decode_order_tail(&parse_bytes(&greater_bytes)),
        Some(OrderTail {
            condition_code: 15,
            set_register: 0,
            result_register: 0,
        })
    );
}

#[test]
fn order_native_slice_fails_closed_outside_first_proved_integer_rectangle() {
    let mut session = machine_session();

    for form in [
        "(машина-кодувати-поточний-біт-порядку 5 26 -1 0)",
        "(машина-кодувати-поточний-біт-порядку 5 27 0 -1)",
        "(машина-кодувати-поточний-біт-порядку 5 26 9223372036854775808 1)",
        "(машина-кодувати-поточний-біт-порядку 5 27 1 9223372036854775808)",
    ] {
        assert_eq!(
            eval_program(form, &mut session)
                .unwrap_or_else(|error| panic!("order guard failed: {form}: {error}"))
                .value
                .to_string(),
            "exact-d5-fallback-required",
            "{form}"
        );
    }

    assert_eq!(
        eval_program(
            "(машина-кодувати-поточний-біт-порядку 3 5 2 3)",
            &mut session,
        )
        .expect("wrong exact identity fails closed")
        .value
        .to_string(),
        "unsupported-current-domain-order-i64"
    );
}

#[test]
fn order_machine_proof_does_not_publish_a_numeric_boolean_language_api() {
    let source = fs::read_to_string(repo_root().join("lib/machine/lowering/semantic-x86-64.lisp"))
        .expect("semantic x86 lowering");

    let start = source
        .find("; #4018 exact D5 order-predicate machine proof.")
        .expect("#4018 order proof block");
    let end = source[start..]
        .find("; #3996 exact-domain structural D3 dispatcher.")
        .map(|offset| start + offset)
        .unwrap_or(source.len());
    let order_block = &source[start..end];

    assert!(order_block.contains("(00001001 машина-кодувати-поточний-біт-порядку"));
    for forbidden in [
        "x86-call-current-order",
        "numeric-boolean",
        "machine-predicate-number",
    ] {
        assert!(
            !order_block.contains(forbidden),
            "machine order proof must not publish {forbidden}"
        );
    }

    let profile =
        fs::read_to_string(repo_root().join("lib/machine/profile/current-domain-x86-64.lisp"))
            .expect("current profile");
    assert!(profile.contains("(5 26 proof \"CMP+SETL+MOVZX / internal bit; D1 boundary\")"));
    assert!(profile.contains("(5 27 proof \"CMP+SETG+MOVZX / internal bit; D1 boundary\")"));
    assert!(!profile.contains("00011010 direct"));
    assert!(!profile.contains("00011011 direct"));
}
