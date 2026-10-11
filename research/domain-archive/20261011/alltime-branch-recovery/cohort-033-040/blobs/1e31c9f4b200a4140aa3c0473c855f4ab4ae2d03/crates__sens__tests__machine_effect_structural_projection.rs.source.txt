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
    load_lisp_file("lib/machine/effects/structural.lisp", &mut session);
    load_lisp_file("lib/machine/layout/pair-x86-64.lisp", &mut session);
    load_lisp_file("lib/machine/encoding/x86-64.lisp", &mut session);
    load_lisp_file("lib/machine/operands/x86-64.lisp", &mut session);
    load_lisp_file("lib/machine/admission/x86-64.lisp", &mut session);
    load_lisp_file("lib/machine/atoms/x86-64.lisp", &mut session);
    load_lisp_file("lib/machine/projection/x86-64.lisp", &mut session);
    load_lisp_file("lib/machine/lowering/semantic-x86-64.lisp", &mut session);
    session
}

#[test]
fn current_car_cons_witness_stays_exact_d3_before_machine_effects() {
    let parsed = parse("(перше (сполучити 2 3))").expect("current Ukrainian structural source");
    let lowered = lower_program(&parsed);

    let ExprKind::DomainCall(car, car_args) = &lowered[0].kind else {
        panic!("CAR must lower to exact DomainCall");
    };
    assert_eq!((car.width(), car.packed_bits()), (3, 0b100));

    let ExprKind::DomainCall(cons, cons_args) = &car_args[0].kind else {
        panic!("CONS must lower to exact DomainCall");
    };
    assert_eq!((cons.width(), cons.packed_bits()), (3, 0b111));
    assert_eq!(cons_args.len(), 2);
}

#[test]
fn structural_effect_sequence_is_target_neutral_and_projects_with_donor_parity() {
    let source =
        fs::read_to_string(repo_root().join("lib/machine/effects/structural.lisp"))
            .expect("structural effect source");
    let lower = source.to_ascii_lowercase();
    for forbidden in [
        "x86",
        "rax",
        "rdi",
        "mov-r64",
        "mov-mem",
        "opcode",
        "modrm",
        "vex",
        " car ",
        " cons ",
    ] {
        assert!(
            !lower.contains(forbidden),
            "target-neutral structural effect leaked forbidden identity token {forbidden}"
        );
    }

    let mut session = machine_session();
    let effects = eval_value(
        "(machine-effect-bounded-two-field-store-load 2 3 x86-pair-car-offset x86-pair-cdr-offset x86-pair-car-offset)",
        &mut session,
    );
    assert_eq!(
        effects,
        "((materialize-u64 work 2) (store-u64 arena 0 work) (materialize-u64 work 3) (store-u64 arena 8 work) (load-u64 result arena 0) (return-u64 result))"
    );

    let projected = eval_value(
        &format!("(x86-project-machine-effects (quote {effects}))"),
        &mut session,
    );
    let donor = eval_value("(x86-lower-cons-car-u64-forms 2 3)", &mut session);
    assert_eq!(projected, donor, "effect projection must equal current donor forms");

    let projected_bytes = eval_value(
        &format!("(x86-encode-machine-effects (quote {effects}))"),
        &mut session,
    );
    let donor_bytes = eval_value(
        &format!("(x86-encode-admitted-program-or-reject (quote {donor}))"),
        &mut session,
    );
    assert_eq!(
        projected_bytes, donor_bytes,
        "effect projection must preserve current admitted bytes"
    );

    let bytes = parse_bytes(&projected_bytes);
    let decoded = x86_64_block_decoder::decode_machine_block(&bytes)
        .unwrap_or_else(|error| panic!("independent decoder rejected {bytes:?}: {error}"));
    assert_eq!(render_decoded(&decoded), projected);
}

#[test]
fn structural_effect_and_target_projection_reject_at_different_boundaries() {
    let mut session = machine_session();

    for source in [
        "(machine-effect-bounded-two-field-store-load -1 3 0 8 0)",
        "(machine-effect-bounded-two-field-store-load 2 -1 0 8 0)",
        "(machine-effect-bounded-two-field-store-load 18446744073709551616 3 0 8 0)",
        "(machine-effect-bounded-two-field-store-load 2 3 -1 8 0)",
    ] {
        assert_eq!(eval_value(source, &mut session), "machine-effect-rejected");
    }

    let too_wide_target_offset = eval_value(
        "(machine-effect-bounded-two-field-store-load 2 3 0 128 0)",
        &mut session,
    );
    assert!(
        too_wide_target_offset.starts_with("(("),
        "target-neutral layer must allow a non-negative offset without assuming x86 disp8"
    );
    assert_eq!(
        eval_value(
            &format!("(x86-project-machine-effects (quote {too_wide_target_offset}))"),
            &mut session,
        ),
        "x86-projection-rejected",
        "target projection owns disp8 rejection"
    );
}
