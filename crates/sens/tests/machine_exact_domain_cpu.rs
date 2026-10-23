use sens::{
    eval_parsed_expressions, eval_program, load_core_library, lower_program, parse,
    parse_mixed_exact_domain_machine_source, ExprKind, Session,
};
use std::fs;
use std::path::PathBuf;

fn repo_root() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../..")
}

fn load_lisp_file(path: &str, session: &mut Session) {
    assert!(
        path.starts_with("lib/machine/"),
        "machine-source reader is restricted to lib/machine/** fixtures: {path}"
    );
    let source = {
        let file_path = repo_root().join(path);
        fs::read_to_string(&file_path)
            .unwrap_or_else(|error| panic!("{} must exist: {error}", file_path.display()))
    };
    let expressions =
        parse_mixed_exact_domain_machine_source(path, &source).unwrap_or_else(|error| {
            panic!("{path} must parse as exact-domain machine source: {error}")
        });
    eval_parsed_expressions(&expressions, session).unwrap_or_else(|error| {
        panic!("{path} must load through the machine-source reader: {error}")
    });
}

#[test]
fn current_d5_plus_selects_x86_add_without_legacy_sid_join() {
    let parsed = parse("(додати 2 3)").expect("current Ukrainian PLUS surface parses");
    let lowered = lower_program(&parsed);
    assert_eq!(lowered.len(), 1);

    let identity = match &lowered[0].kind {
        ExprKind::DomainCall(identity, args) => {
            assert_eq!(identity.width(), 5);
            assert_eq!(identity.packed_bits(), 0b01010);
            assert_eq!(args.len(), 2);
            *identity
        }
        other => panic!("current PLUS must lower to exact DomainCall, got {other:?}"),
    };

    let mut session = Session::default();
    load_core_library(&mut session).expect("core");
    load_lisp_file("lib/machine/encoding/x86-64.lisp", &mut session);
    load_lisp_file("lib/machine/admission/x86-64.lisp", &mut session);
    load_lisp_file("lib/machine/capability-axis.lisp", &mut session);
    load_lisp_file("lib/machine/lowering/semantic-x86-64.lisp", &mut session);

    // Результат машинних предикатів — саме D1 так/ні, не старе D3 ().
    // W8:00001100 ніколи не стає D5:01010 за збігом payload.
    for (program, expected) in [
        ("(машинний-ключ-поточного-домену? 5 10 5 10)", "1"),
        ("(машинний-ключ-поточного-домену? 8 10 5 10)", "0"),
        ("(машинний-ключ-поточного-домену? 8 12 5 10)", "0"),
        ("(машина-поточний-д5-допустимі-входи-32? 2 3)", "1"),
        ("(машина-поточний-д5-допустимі-входи-32? -1 3)", "0"),
        ("(машина-поточний-д6-безпечний-наступник-64? 0)", "1"),
        ("(машина-поточний-д6-безпечний-наступник-64? -1)", "0"),
    ] {
        let actual = eval_program(program, &mut session)
            .unwrap_or_else(|error| panic!("D1 machine predicate {program}: {error}"))
            .value
            .to_string();
        assert_eq!(actual, expected, "D1 machine predicate: {program}");
    }

    let width = identity.width();
    let packed_bits = identity.packed_bits();
    assert_eq!((width, packed_bits), (5, 10));

    let capabilities = eval_program(
        &format!("(спроможності-для-домену {width} {packed_bits})"),
        &mut session,
    )
    .expect("exact-domain machine capability lookup")
    .value
    .to_string();
    assert_eq!(
        capabilities,
        "((integer-add bounded-u32-inputs u64-result))"
    );

    let bytes = eval_program(
        &format!("(машина-кодувати-поточну-двомісну-дію-64 {width} {packed_bits} 2 3)"),
        &mut session,
    )
    .expect("exact D5 PLUS must reach admitted x86 bytes")
    .value
    .to_string();

    assert_eq!(
        bytes,
        "(72 184 2 0 0 0 0 0 0 0 72 185 3 0 0 0 0 0 0 0 72 1 200 195)"
    );

    let unsupported = eval_program(
        "(машина-кодувати-поточну-двомісну-дію-64 3 5 2 3)",
        &mut session,
    )
    .expect("unsupported current identity fails closed as named data")
    .value
    .to_string();
    assert_eq!(unsupported, "unsupported-current-domain-binary-u64");
}

#[test]
fn current_d3_machine_capabilities_are_keyed_by_exact_domain_identity() {
    let mut session = Session::default();
    load_core_library(&mut session).expect("core");
    load_lisp_file("lib/machine/capability-axis.lisp", &mut session);

    for (packed_bits, expected) in [
        (5, "((identity-compare bounded-u64))"),
        (6, "((conditional-branch bounded-u64))"),
        (
            7,
            "((pair-field-store head bounded-u64) (pair-field-store tail bounded-u64))",
        ),
        (4, "((pair-field-load head bounded-u64))"),
        (3, "((pair-field-load tail bounded-u64))"),
    ] {
        let actual = eval_program(
            &format!("(спроможності-для-домену 3 {packed_bits})"),
            &mut session,
        )
        .unwrap_or_else(|error| panic!("D3 packed={packed_bits} capability lookup failed: {error}"))
        .value
        .to_string();
        assert_eq!(actual, expected, "D3 packed={packed_bits}");
    }
}

#[test]
fn current_machine_axis_and_profile_do_not_claim_sid8_as_authority() {
    let axis = fs::read_to_string(repo_root().join("lib/machine/capability-axis.lisp"))
        .expect("capability axis");
    assert!(axis.contains("вісь-спроможностей-машини-версія-3"));
    assert!(axis.contains("спроможності-для-домену"));
    assert!(axis.contains("вісь-спроможностей-машини-версія-3"));
    assert!(axis.contains("свідки-цілей-спроможності-машини-версія-2"));
    assert!(axis.contains("статуси-свідків-цілей-машини-версія-1"));
    assert!(!axis.contains("machine-capability-legacy-sid-axis"));
    assert!(!axis.contains("machine-capabilities-for-sid"));
    assert!(!axis.contains("00001100"));

    let profile =
        fs::read_to_string(repo_root().join("lib/machine/profile/current-domain-x86-64.lisp"))
            .expect("current exact-domain x86 profile");
    for (domain, resident) in [
        ("домен-п'ятий", "додати"),
        ("домен-третій", "тотожне?"),
        ("домен-третій", "за-умовою"),
        ("домен-третій", "сполучити"),
        ("домен-третій", "перше"),
        ("домен-третій", "решта"),
    ] {
        assert!(
            profile.contains(&format!("({domain} {resident} ")),
            "current profile missing exact named key ({domain},{resident})"
        );
    }
    assert!(!profile.contains("semantic-registry"));
    assert!(
        !profile.contains("00001100"),
        "current exact-domain profile must not key PLUS by the historical SID8 byte"
    );

    let boundary = fs::read_to_string(repo_root().join("lib/machine/authority-boundary.lisp"))
        .expect("machine authority boundary");
    assert!(boundary.contains("(semantic-authority language-contract.lisp+ratified-domain-laws)"));
    assert!(!boundary.contains("(semantic-authority lib/surface/semantic-registry.lisp)"));
}
