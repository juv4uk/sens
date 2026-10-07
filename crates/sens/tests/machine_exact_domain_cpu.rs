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

#[test]
fn current_d5_plus_selects_x86_add_with_width_safe_domain_key() {
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

    let width = identity.width();
    let packed_bits = identity.packed_bits();

    let capabilities = eval_program(
        &format!("(machine-capabilities-for-domain {width} {packed_bits})"),
        &mut session,
    )
    .expect("width-safe exact-domain machine capability lookup")
    .value
    .to_string();
    assert_eq!(capabilities, "((integer-add bounded-u32-inputs u64-result))");

    let bytes = eval_program(
        &format!("(x86-encode-current-binary-u64 {width} {packed_bits} 2 3)"),
        &mut session,
    )
    .expect("exact D5 PLUS must reach admitted x86 bytes")
    .value
    .to_string();

    assert_eq!(
        bytes,
        "(72 184 2 0 0 0 0 0 0 0 72 185 3 0 0 0 0 0 0 0 72 1 200 195)"
    );
}

#[test]
fn cross_width_payload_collisions_fail_closed() {
    let mut session = Session::default();
    load_core_library(&mut session).expect("core");
    load_lisp_file("lib/machine/encoding/x86-64.lisp", &mut session);
    load_lisp_file("lib/machine/admission/x86-64.lisp", &mut session);
    load_lisp_file("lib/machine/capability-axis.lisp", &mut session);
    load_lisp_file("lib/machine/lowering/semantic-x86-64.lisp", &mut session);

    // Same packed payload 10:
    //   D5:01010 = PLUS
    //   D4:1010  = LOOKUP
    assert_eq!(
        eval_program("(machine-capabilities-for-domain 5 10)", &mut session)
            .expect("D5 PLUS capability")
            .value
            .to_string(),
        "((integer-add bounded-u32-inputs u64-result))"
    );
    assert_eq!(
        eval_program("(machine-capabilities-for-domain 4 10)", &mut session)
            .expect("D4 LOOKUP must not inherit D5 PLUS")
            .value
            .to_string(),
        "()"
    );
    assert_eq!(
        eval_program("(x86-encode-current-binary-u64 4 10 2 3)", &mut session)
            .expect("D4 LOOKUP must fail closed at x86 D5 dispatcher")
            .value
            .to_string(),
        "unsupported-current-domain-binary-u64"
    );

    // Same packed payload 11:
    //   D5:01011 = DIFFERENCE
    //   D4:1011  = BIND
    assert_ne!(
        eval_program("(machine-capabilities-for-domain 5 11)", &mut session)
            .expect("D5 DIFFERENCE capability")
            .value
            .to_string(),
        "()"
    );
    assert_eq!(
        eval_program("(machine-capabilities-for-domain 4 11)", &mut session)
            .expect("D4 BIND must not inherit D5 DIFFERENCE")
            .value
            .to_string(),
        "()"
    );
}

#[test]
fn current_d3_machine_capabilities_use_width_and_packed_bits() {
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
            &format!("(machine-capabilities-for-domain 3 {packed_bits})"),
            &mut session,
        )
        .unwrap_or_else(|error| panic!("D3 payload {packed_bits} capability lookup failed: {error}"))
        .value
        .to_string();
        assert_eq!(actual, expected, "D3 payload {packed_bits}");
    }
}

#[test]
fn current_machine_axis_and_profile_do_not_depend_on_leading_zero_lexemes() {
    let axis = fs::read_to_string(repo_root().join("lib/machine/capability-axis.lisp"))
        .expect("capability axis");
    assert!(axis.contains("machine-capability-axis-v3"));
    assert!(axis.contains("machine-capabilities-for-domain"));
    assert!(axis.contains("domain-width + packed-bits"));
    assert!(!axis.contains("machine-capability-legacy-sid-axis"));
    assert!(!axis.contains("machine-capabilities-for-sid"));
    assert!(!axis.contains("00001100"));

    let profile =
        fs::read_to_string(repo_root().join("lib/machine/profile/current-domain-x86-64.lisp"))
            .expect("current exact-domain x86 profile");
    for exact_key in [
        "(5 10 fast-path", // D5:01010 PLUS
        "(3 5 direct",     // D3:101 EQ
        "(3 6 control",    // D3:110 COND
        "(3 7 runtime",    // D3:111 CONS
        "(3 4 direct",     // D3:100 CAR
        "(3 3 direct",     // D3:011 CDR
    ] {
        assert!(profile.contains(exact_key), "current profile missing {exact_key}");
    }
    assert!(profile.contains("(machine-domain-profile/2"));
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
