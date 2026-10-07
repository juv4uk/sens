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

fn structural_effects(session: &mut Session) -> String {
    eval_value(
        "(machine-effect-bounded-two-field-store-load 2 3 (00000001 field0) (00000001 field1) (00000001 field0))",
        session,
    )
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
fn structural_effect_is_target_neutral_and_layout_free() {
    let source = fs::read_to_string(repo_root().join("lib/machine/effects/structural.lisp"))
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
        "disp8",
        "pair-x86",
        " car ",
        " cdr ",
        " cons ",
        "offset",
    ] {
        assert!(
            !lower.contains(forbidden),
            "target-neutral structural effect leaked forbidden token {forbidden}"
        );
    }

    let mut session = machine_session();
    let effects = structural_effects(&mut session);
    assert_eq!(
        effects,
        "((materialize-u64 work 2) (store-u64 arena field0 work) (materialize-u64 work 3) (store-u64 arena field1 work) (load-u64 result arena field0) (return-u64 result))"
    );
}

#[test]
fn x86_projection_consumes_layout_and_preserves_donor_forms_bytes_and_decode() {
    let mut session = machine_session();
    let effects = structural_effects(&mut session);

    let projected = eval_value(
        &format!("(x86-project-machine-effects (00000001 {effects}))"),
        &mut session,
    );
    let donor = eval_value("(x86-lower-cons-car-u64-forms 2 3)", &mut session);
    assert_eq!(projected, donor, "projection must equal current donor forms");

    let projected_bytes = eval_value(
        &format!("(x86-encode-machine-effects (00000001 {effects}))"),
        &mut session,
    );
    let donor_bytes = eval_value(
        &format!("(x86-encode-admitted-program-or-reject (00000001 {donor}))"),
        &mut session,
    );
    assert_eq!(projected_bytes, donor_bytes, "projected bytes must match donor");

    let bytes = parse_bytes(&projected_bytes);
    let decoded = x86_64_block_decoder::decode_machine_block(&bytes)
        .unwrap_or_else(|error| panic!("independent decoder rejected {bytes:?}: {error}"));
    assert_eq!(render_decoded(&decoded), projected);
}

#[test]
fn changing_target_layout_changes_projection_not_effect_object() {
    let mut session = machine_session();
    let effects_before = structural_effects(&mut session);

    let default_forms = eval_value(
        &format!("(x86-project-machine-effects (00000001 {effects_before}))"),
        &mut session,
    );
    let alternate_forms = eval_value(
        &format!(
            "(x86-project-machine-effects-with-layout (00000001 {effects_before}) 16 24)"
        ),
        &mut session,
    );
    assert_ne!(alternate_forms, default_forms);
    assert_eq!(
        alternate_forms,
        "((mov-r64-imm64 rax 2) (mov-mem-disp8-r64 rdi 16 rax) (mov-r64-imm64 rax 3) (mov-mem-disp8-r64 rdi 24 rax) (mov-r64-mem-disp8 rax rdi 16) (ret))"
    );

    let default_bytes = eval_value(
        &format!("(x86-encode-admitted-program-or-reject (00000001 {default_forms}))"),
        &mut session,
    );
    let alternate_bytes = eval_value(
        &format!("(x86-encode-admitted-program-or-reject (00000001 {alternate_forms}))"),
        &mut session,
    );
    assert_ne!(alternate_bytes, default_bytes);

    let effects_after = structural_effects(&mut session);
    assert_eq!(
        effects_after, effects_before,
        "target layout variation must not change canonical effect object"
    );
}

#[test]
fn effect_and_projection_rejections_stay_at_different_boundaries() {
    let mut session = machine_session();

    for source in [
        "(machine-effect-bounded-two-field-store-load -1 3 (00000001 field0) (00000001 field1) (00000001 field0))",
        "(machine-effect-bounded-two-field-store-load 2 -1 (00000001 field0) (00000001 field1) (00000001 field0))",
        "(machine-effect-bounded-two-field-store-load 18446744073709551616 3 (00000001 field0) (00000001 field1) (00000001 field0))",
        "(machine-effect-bounded-two-field-store-load 2 3 (00000001 unknown-field) (00000001 field1) (00000001 field0))",
    ] {
        assert_eq!(eval_value(source, &mut session), "machine-effect-rejected");
    }

    let effects = structural_effects(&mut session);
    assert_eq!(
        eval_value(
            &format!(
                "(x86-project-machine-effects-with-layout (00000001 {effects}) 0 128)"
            ),
            &mut session,
        ),
        "x86-projection-rejected",
        "x86 projection owns disp8 rejection; the upstream effect remains valid"
    );
}
