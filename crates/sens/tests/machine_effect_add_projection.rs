use sens::{eval_program, load_core_library, lower_program, parse, ExprKind, Session};
use std::fs;
use std::path::PathBuf;

#[path = "support/x86_64_block_decoder.rs"]
mod x86_64_block_decoder;

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

fn eval_value(source: &str, session: &mut Session) -> String {
    eval_program(source, session)
        .unwrap_or_else(|error| panic!("{source}: {error}"))
        .value
        .to_string()
}

fn parse_bytes(rendered: &str) -> Vec<u8> {
    rendered
        .trim_start_matches('(')
        .trim_end_matches(')')
        .split_whitespace()
        .filter(|token| !token.is_empty())
        .map(|token| token.parse::<u8>().expect("machine byte"))
        .collect()
}

fn render_decoded(forms: &[String]) -> String {
    format!("({})", forms.join(" "))
}

fn machine_session() -> Session {
    let mut session = Session::default();
    load_core_library(&mut session).expect("core");
    load_lisp_file("lib/machine/effects/u64.lisp", &mut session);
    load_lisp_file("lib/machine/encoding/x86-64.lisp", &mut session);
    load_lisp_file("lib/machine/operands/x86-64.lisp", &mut session);
    load_lisp_file("lib/machine/admission/x86-64.lisp", &mut session);
    load_lisp_file("lib/machine/atoms/x86-64.lisp", &mut session);
    load_lisp_file("lib/machine/projection/x86-64.lisp", &mut session);
    load_lisp_file("lib/machine/lowering/semantic-x86-64.lisp", &mut session);
    session
}

#[test]
fn current_d5_plus_builds_target_neutral_bounded_add_effect() {
    let parsed = parse("(додати 2 3)").expect("current PLUS source");
    let lowered = lower_program(&parsed);
    let ExprKind::DomainCall(identity, args) = &lowered[0].kind else {
        panic!("PLUS must lower to exact DomainCall");
    };
    assert_eq!((identity.width(), identity.packed_bits()), (5, 10));
    assert_eq!(args.len(), 2);

    let effect_source =
        fs::read_to_string(repo_root().join("lib/machine/effects/u64.lisp")).expect("effect");
    let lower = effect_source.to_ascii_lowercase();
    for forbidden in [
        "x86", "rax", "rcx", "mov-r64", "add-r64", "0x01", "modrm", "vex",
    ] {
        assert!(
            !lower.contains(forbidden),
            "target-neutral effect leaked target identity token {forbidden}"
        );
    }

    let mut session = machine_session();
    assert_eq!(
        eval_value("(машинний-ефект-додавання-64 2 3)", &mut session),
        "(bounded-u64-add 2 3)"
    );
}

#[test]
fn bounded_add_effect_projects_to_same_forms_and_bytes_as_current_donor() {
    let mut session = machine_session();

    for (left, right) in [
        (2u64, 3u64),
        (0, u32::MAX as u64),
        (u32::MAX as u64, u32::MAX as u64),
    ] {
        let effect = eval_value(
            &format!("(машинний-ефект-додавання-64 {left} {right})"),
            &mut session,
        );
        assert_eq!(effect, format!("(bounded-u64-add {left} {right})"));

        let projected = eval_value(
            &format!("(проєктувати-машинний-ефект-на-х86 (quote {effect}))"),
            &mut session,
        );
        let donor = eval_value(
            &format!("(машина-знизити-додавання-беззнакових-64-до-форм {left} {right})"),
            &mut session,
        );
        assert_eq!(projected, donor, "projected forms must equal donor forms");

        let projected_bytes = eval_value(
            &format!("(закодувати-машинний-ефект-на-х86 (quote {effect}))"),
            &mut session,
        );
        let donor_bytes = eval_value(
            &format!("(x86-encode-admitted-program (quote {donor}))"),
            &mut session,
        );
        assert_eq!(
            projected_bytes, donor_bytes,
            "effect projection must preserve current admitted bytes"
        );

        let bytes = parse_bytes(&projected_bytes);
        let decoded = x86_64_block_decoder::decode_machine_block(&bytes)
            .unwrap_or_else(|error| panic!("independent decoder rejected {bytes:?}: {error}"));
        assert_eq!(
            render_decoded(&decoded),
            projected,
            "independent decode must reconstruct the projected forms"
        );
    }
}

#[test]
fn effect_and_projection_rejections_are_distinct_and_fail_closed() {
    let mut session = machine_session();

    for source in [
        "(машинний-ефект-додавання-64 -1 3)",
        "(машинний-ефект-додавання-64 4294967296 3)",
        "(машинний-ефект-додавання-64 2 4294967296)",
    ] {
        assert_eq!(eval_value(source, &mut session), "machine-effect-rejected");
    }

    assert_eq!(
        eval_value(
            "(проєктувати-машинний-ефект-на-х86 (quote (unknown-effect 2 3)))",
            &mut session,
        ),
        "x86-projection-rejected"
    );
    assert_eq!(
        eval_value(
            "(закодувати-машинний-ефект-на-х86 (quote (unknown-effect 2 3)))",
            &mut session,
        ),
        "x86-projection-rejected"
    );
}

#[test]
fn ukr_machine_key_projection_preserves_width_and_legacy_calls() {
    let mut session = machine_session();
    // Порівнюємо ширину І бітове слово. Стара назва лишається тією самою функцією.
    for (width, bits, expected_width, expected_bits, matches) in [
        (5, 10, 5, 10, true),
        (5, 10, 6, 10, false),
        (5, 10, 5, 11, false),
        (3, 5, 3, 5, true),
    ] {
        let ukr = eval_value(
            &format!(
                "(машинний-ключ-поточного-домену? {width} {bits} {expected_width} {expected_bits})"
            ),
            &mut session,
        );
        let historical = eval_value(
            &format!(
                "(машинний-ключ-поточного-домену? {width} {bits} {expected_width} {expected_bits})"
            ),
            &mut session,
        );
        let expected = eval_value(if matches { "так" } else { "(як-є ())" }, &mut session);
        assert_eq!(ukr, expected, "width={width}, bits={bits}");
        assert_eq!(historical, ukr, "historical binding must preserve behavior");
    }
}

#[test]
fn ukrainian_machine_effect_and_atom_aliases_keep_execution_parity() {
    let mut session = machine_session();
    // Порівнюємо фактичне обчислення, не лише наявність рядків у файлах.
    let pairs = [
        ("x86-ret", "машинна-команда-повернення"),
        (
            "x86-add-r64-r64 (як-є rax) (як-є rcx)",
            "машинна-команда-додати-64-розрядні-регістри (як-є rax) (як-є rcx)",
        ),
        ("x86-jnz-rel8 11", "машинна-команда-перехід-якщо-не-нуль 11"),
        ("x86-gpr64 (як-є rax)", "машинний-регістр-64 (як-є rax)"),
        (
            "x86-as-gpr64 (як-є rax)",
            "типізувати-машинний-регістр-64 (як-є rax)",
        ),
        (
            "x86-gpr64-value (як-є (gpr64 rax))",
            "значення-машинного-регістра-64 (як-є (gpr64 rax))",
        ),
        ("x86-disp8 11", "машинний-зсув-8 11"),
        ("x86-disp8 256", "машинний-зсув-8 256"),
        ("x86-u64-imm 3", "машинне-безпосереднє-беззнакове-64 3"),
    ];
    for (historical, ukrainian) in pairs {
        let previous = eval_value(&format!("({historical})"), &mut session);
        let current = eval_value(&format!("({ukrainian})"), &mut session);
        assert_eq!(
            current, previous,
            "{historical} must retain its exact SENS result"
        );
    }
    assert_eq!(
        eval_value("(машинний-ефект-додавання-64 2 3)", &mut session),
        "(bounded-u64-add 2 3)"
    );
    assert_eq!(
        eval_value("(машинна-команда-повернення)", &mut session),
        "(ret)"
    );
}
