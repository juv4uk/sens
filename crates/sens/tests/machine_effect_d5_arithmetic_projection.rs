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

fn lowered_identity(source: &str) -> (u8, u8) {
    let parsed = parse(source).unwrap_or_else(|error| panic!("{source}: {error}"));
    let lowered = lower_program(&parsed);
    let ExprKind::DomainCall(identity, _) = &lowered[0].kind else {
        panic!("{source} must lower to exact DomainCall");
    };
    (identity.width(), identity.packed_bits())
}

#[test]
fn exact_d5_identity_selects_target_neutral_add_sub_mul_effects() {
    let cases = [
        ("(додати 2 3)", (5, 10), 2u64, 3u64, "(bounded-u64-add 2 3)"),
        ("(відняти 5 3)", (5, 11), 5u64, 3u64, "(bounded-u64-sub 5 3)"),
        ("(помножити 4 6)", (5, 22), 4u64, 6u64, "(bounded-u64-mul 4 6)"),
    ];

    let effect_source =
        fs::read_to_string(repo_root().join("lib/machine/effects/u64.lisp")).expect("effect");
    let lower = effect_source.to_ascii_lowercase();
    for forbidden in [
        "x86",
        "rax",
        "rcx",
        "mov-r64",
        "sub-r64",
        "imul-r64",
        "modrm",
        "vex",
    ] {
        assert!(
            !lower.contains(forbidden),
            "target-neutral effect leaked target identity token {forbidden}"
        );
    }

    let mut session = machine_session();
    for (source, expected_identity, left, right, expected_effect) in cases {
        let identity = lowered_identity(source);
        assert_eq!(identity, expected_identity, "{source}");

        let selected = eval_value(
            &format!(
                "(machine-effect-lower-current-binary-u64 {} {} {left} {right})",
                identity.0, identity.1
            ),
            &mut session,
        );
        assert_eq!(selected, expected_effect, "{source}");
    }

    assert_eq!(
        eval_value(
            "(machine-effect-lower-current-binary-u64 5 23 4 2)",
            &mut session,
        ),
        "machine-effect-not-applicable",
        "D5 QUOTIENT must not silently select an arithmetic effect from this slice"
    );
}

#[test]
fn bounded_sub_effect_projects_with_form_byte_and_independent_decode_parity() {
    let mut session = machine_session();

    for (left, right) in [(5u64, 3u64), (u64::MAX, 0), (u64::MAX, u64::MAX)] {
        let effect = eval_value(
            &format!("(machine-effect-bounded-u64-sub {left} {right})"),
            &mut session,
        );
        assert_eq!(effect, format!("(bounded-u64-sub {left} {right})"));

        let projected = eval_value(
            &format!("(x86-project-machine-effect (quote {effect}))"),
            &mut session,
        );
        let donor = eval_value(
            &format!("(x86-lower-difference-u64-forms {left} {right})"),
            &mut session,
        );
        assert_eq!(projected, donor, "SUB projection must preserve donor forms");

        let projected_bytes = eval_value(
            &format!("(x86-encode-machine-effect (quote {effect}))"),
            &mut session,
        );
        let donor_bytes = eval_value(
            &format!("(x86-encode-admitted-program (quote {donor}))"),
            &mut session,
        );
        assert_eq!(projected_bytes, donor_bytes, "SUB bytes must match donor");

        let bytes = parse_bytes(&projected_bytes);
        let decoded = x86_64_block_decoder::decode_machine_block(&bytes)
            .unwrap_or_else(|error| panic!("independent decoder rejected {bytes:?}: {error}"));
        assert_eq!(
            render_decoded(&decoded),
            projected,
            "existing observer must reconstruct SUB projected forms"
        );
    }
}

#[test]
fn bounded_mul_effect_projects_with_form_and_byte_parity_without_decoder_overlap() {
    let mut session = machine_session();

    for (left, right) in [
        (2u64, 3u64),
        (0, u32::MAX as u64),
        (u32::MAX as u64, u32::MAX as u64),
    ] {
        let effect = eval_value(
            &format!("(machine-effect-bounded-u64-mul {left} {right})"),
            &mut session,
        );
        assert_eq!(effect, format!("(bounded-u64-mul {left} {right})"));

        let projected = eval_value(
            &format!("(x86-project-machine-effect (quote {effect}))"),
            &mut session,
        );
        let donor = eval_value(
            &format!("(x86-lower-times-u64-forms {left} {right})"),
            &mut session,
        );
        assert_eq!(projected, donor, "IMUL projection must preserve donor forms");

        let projected_bytes = eval_value(
            &format!("(x86-encode-machine-effect (quote {effect}))"),
            &mut session,
        );
        let donor_bytes = eval_value(
            &format!("(x86-encode-admitted-program (quote {donor}))"),
            &mut session,
        );
        assert_eq!(projected_bytes, donor_bytes, "IMUL bytes must match donor");
    }

    // IMUL decode coverage is intentionally owned by #4343. This slice proves
    // target-neutral selection, projection and closed-encoder byte parity
    // without modifying the shared independent observer.
}

#[test]
fn sub_mul_effect_bounds_fail_closed_before_target_projection() {
    let mut session = machine_session();

    for source in [
        "(machine-effect-bounded-u64-sub 2 3)",
        "(machine-effect-bounded-u64-sub -1 0)",
        "(machine-effect-bounded-u64-sub 18446744073709551616 0)",
        "(machine-effect-bounded-u64-mul 4294967296 1)",
        "(machine-effect-bounded-u64-mul 1 4294967296)",
    ] {
        assert_eq!(
            eval_value(source, &mut session),
            "machine-effect-rejected",
            "{source}"
        );
    }

    assert_eq!(
        eval_value(
            "(machine-effect-lower-current-binary-u64 5 11 2 3)",
            &mut session,
        ),
        "machine-effect-rejected",
        "valid DIFFERENCE identity with unsafe bounded carrier must reject as an effect, not become another operation"
    );
}
