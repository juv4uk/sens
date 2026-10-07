use sens::{eval_program, load_core_library, lower_program, parse, ExprKind, Session};
use serde_json::Value;
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

fn eval_value(source: &str, session: &mut Session) -> String {
    eval_program(source, session)
        .unwrap_or_else(|error| panic!("{source}: {error}"))
        .value
        .to_string()
}

fn lowered_identity(source: &str) -> (usize, u8) {
    let parsed = parse(source).unwrap_or_else(|error| panic!("{source}: {error}"));
    let lowered = lower_program(&parsed);
    let ExprKind::DomainCall(identity, _) = &lowered[0].kind else {
        panic!("{source} must lower to exact DomainCall");
    };
    (identity.width(), identity.packed_bits())
}

fn session() -> Session {
    let mut session = Session::default();
    load_core_library(&mut session).expect("core");
    load_lisp_file("lib/machine/effects/u64.lisp", &mut session);
    load_lisp_file("lib/machine/lowering/semantic-effects.lisp", &mut session);
    session
}

#[test]
fn d5_arithmetic_coordinates_are_guarded_by_current_foundation() {
    let foundation: Value = serde_json::from_str(
        &fs::read_to_string(repo_root().join("knowledge/d1-d9-foundation.json"))
            .expect("current foundation"),
    )
    .expect("foundation json");
    let d5 = foundation["domains"]["D5"]["residents"]
        .as_object()
        .expect("D5 resident map");

    for (bits, expected) in [
        ("01010", "PLUS"),
        ("01011", "DIFFERENCE"),
        ("10110", "TIMES"),
    ] {
        assert_eq!(
            d5.get(bits).and_then(Value::as_str),
            Some(expected),
            "semantic->effect seam coordinate drifted from current authority: D5:{bits}"
        );
    }
}

#[test]
fn exact_domain_identity_selects_effect_kind_once() {
    let cases = [
        ("(додати 2 3)", (5usize, 10u8), "bounded-u64-add"),
        ("(відняти 5 3)", (5usize, 11u8), "bounded-u64-sub"),
        ("(помножити 4 6)", (5usize, 22u8), "bounded-u64-mul"),
    ];

    let mut session = session();
    for (source, expected_identity, expected_kind) in cases {
        let identity = lowered_identity(source);
        assert_eq!(identity, expected_identity, "{source}");
        assert_eq!(
            eval_value(
                &format!(
                    "(machine-effect-kind-for-current-binary-u64 {} {})",
                    identity.0, identity.1
                ),
                &mut session,
            ),
            expected_kind,
            "{source}",
        );
    }
}

#[test]
fn wrong_domain_and_unsupported_identity_fail_closed() {
    let mut session = session();

    for source in [
        "(machine-effect-kind-for-current-binary-u64 4 10)",
        "(machine-effect-kind-for-current-binary-u64 6 10)",
        "(machine-effect-kind-for-current-binary-u64 5 23)",
        "(machine-effect-kind-for-current-binary-u64 3 5)",
    ] {
        assert_eq!(
            eval_value(source, &mut session),
            "machine-effect-not-applicable",
            "{source}"
        );
    }

    assert_eq!(
        eval_value(
            "(machine-effect-lower-current-binary-u64 5 10 2 3)",
            &mut session,
        ),
        "(bounded-u64-add 2 3)"
    );
    assert_eq!(
        eval_value(
            "(machine-effect-lower-current-binary-u64 5 11 5 3)",
            &mut session,
        ),
        "machine-effect-not-applicable",
        "SUB kind is reserved by the seam but its constructor remains #4358-owned until replay"
    );
}

#[test]
fn semantic_effect_seam_contains_no_target_or_surface_authority() {
    let source = fs::read_to_string(
        repo_root().join("lib/machine/lowering/semantic-effects.lisp"),
    )
    .expect("semantic effect seam");
    let lower = source.to_ascii_lowercase();

    for forbidden in [
        "x86",
        "rax",
        "rcx",
        "modrm",
        "vex",
        "disp8",
        "semantic-registry",
        "додати",
        "відняти",
        "помножити",
    ] {
        assert!(
            !lower.contains(forbidden),
            "semantic->effect seam leaked forbidden authority token {forbidden}"
        );
    }

    let effect_source = fs::read_to_string(repo_root().join("lib/machine/effects/u64.lisp"))
        .expect("generic u64 effects");
    assert!(
        !effect_source.contains("machine-effect-kind-for-current-binary-u64"),
        "generic effect library must not own semantic coordinate routing"
    );
}
