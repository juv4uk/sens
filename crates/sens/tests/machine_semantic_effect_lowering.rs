use sens::{eval_program, load_core_library, lower_program, parse, ExprKind, Session};
use serde_json::Value;
use std::fs;
use std::path::PathBuf;

fn repo_root() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../..")
}

fn read(path: &str) -> String {
    fs::read_to_string(repo_root().join(path))
        .unwrap_or_else(|error| panic!("#4365 requires {path}: {error}"))
}

fn load_lisp_file(path: &str, session: &mut Session) {
    let source = read(path);
    eval_program(&source, session)
        .unwrap_or_else(|error| panic!("{path} must load as ordinary sens: {error}"));
}

fn eval_value(source: &str, session: &mut Session) -> String {
    eval_program(source, session)
        .unwrap_or_else(|error| panic!("{source}: {error}"))
        .value
        .to_string()
}

fn lowering_session() -> Session {
    let mut session = Session::default();
    load_core_library(&mut session).expect("core");
    load_lisp_file("lib/machine/effects/u64.lisp", &mut session);
    load_lisp_file("lib/machine/lowering/semantic-effects.lisp", &mut session);
    session
}

fn current_d5_plus_coordinate() -> (usize, u8) {
    let foundation: Value =
        serde_json::from_str(&read("knowledge/d1-d9-foundation.json")).expect("foundation JSON");

    assert_eq!(
        foundation["schema"], "d1-d9-foundation-ratification/v1",
        "#4365 must consume the current foundation schema"
    );
    assert_eq!(
        foundation["status"], "owner-ratified",
        "#4365 must not route from a research/shadow map"
    );

    let d5 = &foundation["domains"]["D5"];
    let width = d5["width"].as_u64().expect("D5 width") as usize;
    let residents = d5["residents"].as_object().expect("D5 residents");
    let (bits, _) = residents
        .iter()
        .find(|(_, role)| role.as_str() == Some("PLUS"))
        .expect("current D5 foundation must contain PLUS");

    (
        width,
        u8::from_str_radix(bits, 2).expect("current D5 PLUS bits"),
    )
}

#[test]
fn current_foundation_runtime_identity_and_effect_router_agree() {
    let expected = current_d5_plus_coordinate();

    let parsed = parse("(додати 2 3)").expect("current PLUS source");
    let lowered = lower_program(&parsed);
    let ExprKind::DomainCall(identity, args) = &lowered[0].kind else {
        panic!("current PLUS must lower to exact DomainCall");
    };

    assert_eq!(
        (identity.width(), identity.packed_bits()),
        expected,
        "runtime exact DomainIdentity and owner foundation must agree before effect selection"
    );
    assert_eq!(args.len(), 2);

    let source = read("lib/machine/lowering/semantic-effects.lisp");
    let guarded_coordinate = format!(
        "(machine-effect-current-domain-key? width bits {} {})",
        expected.0, expected.1
    );
    assert!(
        source.contains(&guarded_coordinate),
        "#4365 router drifted from current owner foundation: expected {guarded_coordinate}"
    );
}

#[test]
fn exact_d5_plus_selects_only_the_existing_target_neutral_effect() {
    let (width, bits) = current_d5_plus_coordinate();
    let mut session = lowering_session();

    assert_eq!(
        eval_value(
            &format!("(machine-lower-current-binary-effect {width} {bits} 2 3)"),
            &mut session,
        ),
        "(bounded-u64-add 2 3)"
    );

    assert_eq!(
        eval_value(
            &format!(
                "(machine-lower-current-binary-effect {width} {bits} 4294967296 3)"
            ),
            &mut session,
        ),
        "machine-effect-rejected",
        "semantic selection must preserve the already-proved bounded carrier guard"
    );
}

#[test]
fn wrong_domain_and_unmapped_current_identity_fail_closed() {
    let (_, plus_bits) = current_d5_plus_coordinate();
    let mut session = lowering_session();

    for source in [
        format!("(machine-lower-current-binary-effect 4 {plus_bits} 2 3)"),
        format!("(machine-lower-current-binary-effect 6 {plus_bits} 2 3)"),
        "(machine-lower-current-binary-effect 5 11 5 3)".to_string(),
        "(machine-lower-current-binary-effect 5 22 4 6)".to_string(),
        "(machine-lower-current-binary-effect 5 23 4 2)".to_string(),
    ] {
        assert_eq!(
            eval_value(&source, &mut session),
            "machine-effect-not-applicable",
            "{source}"
        );
    }
}

#[test]
fn semantic_to_effect_layer_contains_no_target_or_surface_authority() {
    let lowerer = read("lib/machine/lowering/semantic-effects.lisp").to_ascii_lowercase();
    let effects = read("lib/machine/effects/u64.lisp").to_ascii_lowercase();

    for forbidden in [
        "x86",
        "rax",
        "rcx",
        "modrm",
        "vex",
        "avx",
        "cuda",
        "ptx",
        "fpga",
        "pair-x86",
        "intel",
        "semantic-registry",
        "додати",
    ] {
        assert!(
            !lowerer.contains(forbidden),
            "#4365 semantic->effect seam leaked target/surface authority token {forbidden}"
        );
    }

    assert!(
        !effects.contains("machine-lower-current-binary-effect")
            && !effects.contains("machine-effect-current-domain-key?"),
        "generic effect-definition module must not own semantic coordinate routing"
    );
}
