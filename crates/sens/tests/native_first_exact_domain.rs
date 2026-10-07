use sens::{
    domain_identity_shape_or_empty_mechanism, eval_program, expr_to_exact_program_data,
    load_core_library, lower_program, parse, Bit4, CoreD4, DomainIdentity, ExprKind, Session,
    Value,
};
use std::fs;
use std::path::PathBuf;
use std::rc::Rc;

fn repo_root() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../..")
}

fn load_lisp_file(path: &str, session: &mut Session) {
    let path = repo_root().join(path);
    let source = fs::read_to_string(&path)
        .unwrap_or_else(|error| panic!("{} must exist: {error}", path.display()));
    eval_program(&source, session)
        .unwrap_or_else(|error| panic!("{} must load: {error}", path.display()));
}

fn native_session() -> Session {
    let mut session = Session::default();
    load_core_library(&mut session).expect("core");
    load_lisp_file("lib/machine/layout/pair-x86-64.lisp", &mut session);
    load_lisp_file("lib/machine/operands/x86-64.lisp", &mut session);
    load_lisp_file("lib/machine/lowering/semantic-x86-64.lisp", &mut session);
    load_lisp_file("lib/machine/dispatch/native-first.lisp", &mut session);
    session
}

#[test]
fn lowered_exact_domain_data_selects_native_car_cons_without_spelling_match() {
    let parsed = parse("(перше (сполучити 2 3))").expect("current Ukrainian source");
    let lowered = lower_program(&parsed);

    let ExprKind::DomainCall(car, car_args) = &lowered[0].kind else {
        panic!("CAR must lower to exact DomainCall");
    };
    assert_eq!((car.width(), car.packed_bits()), (3, 0b100));
    let ExprKind::DomainCall(cons, _) = &car_args[0].kind else {
        panic!("CONS must lower to exact DomainCall");
    };
    assert_eq!((cons.width(), cons.packed_bits()), (3, 0b111));

    let data = expr_to_exact_program_data(&lowered[0]).expect("exact program-data");
    let mut session = native_session();
    session
        .environment
        .define("__native_first_shape", domain_identity_shape_or_empty_mechanism());
    session.environment.define("__native_first_expr", data.clone());

    let head = eval_program(
        "(00000101 __native_first_expr)",
        &mut session,
    ).expect("head witness").value;
    let shape = eval_program(
        "(__native_first_shape (00000101 __native_first_expr))",
        &mut session,
    ).expect("shape witness").value;
    let key3_direct = eval_program(
        "(native-first-domain-key3-shape? (shape-or-empty (00000101 __native_first_expr)) 1 0 0)",
        &mut session,
    ).expect("direct key3 witness").value;
    let car_pred = eval_program(
        "(native-first-domain-d3-car? __native_first_shape (00000101 __native_first_expr))",
        &mut session,
    ).expect("car predicate witness").value;
    eprintln!("native-first diagnostics: shape={shape:?} head={head:?} car_pred={car_pred:?} key3_direct={key3_direct:?}");
    let actual = eval_program(
        "(native-first-plan-domain __native_first_shape __native_first_expr)",
        &mut session,
    ).expect("exact-domain native plan").value;
    let expected = eval_program(
        "(native-first-native-plan (x86-lower-cons-car-u64-forms 2 3) x86-pair-cell-bytes)",
        &mut session,
    )
    .expect("known bounded CAR/CONS plan")
    .value;

    assert_eq!(actual, expected);
}

#[test]
fn same_packed_payload_wrong_width_falls_back() {
    let parsed = parse("(перше (сполучити 2 3))").expect("current Ukrainian source");
    let lowered = lower_program(&parsed);
    let data = expr_to_exact_program_data(&lowered[0]).expect("exact program-data");

    let wrong_identity = DomainIdentity::D4(CoreD4::from_word(
        Bit4::new(0b0100).expect("D4 word"),
    ));
    assert_eq!((wrong_identity.width(), wrong_identity.packed_bits()), (4, 4));

    let wrong = match &data {
        Value::Pair(_, tail) => Value::Pair(
            Rc::new(Value::DomainIdentity(wrong_identity)),
            Rc::clone(tail),
        ),
        other => panic!("expected application data, got {other}"),
    };

    let mut session = native_session();
    session
        .environment
        .define("__native_first_shape", domain_identity_shape_or_empty_mechanism());
    session.environment.define("__native_first_wrong", wrong.clone());

    let actual = eval_program(
        "(native-first-plan-domain __native_first_shape __native_first_wrong)",
        &mut session,
    )
    .expect("wrong-width classifier result")
    .value;
    let expected = eval_program(
        "(native-first-fallback __native_first_wrong)",
        &mut session,
    )
    .expect("fallback value")
    .value;

    assert_eq!(actual, expected);
}


#[test]
fn exact_domain_classifier_block_has_no_spelling_or_sid_match() {
    let source = fs::read_to_string(repo_root().join("lib/machine/dispatch/native-first.lisp"))
        .expect("native-first classifier source");
    let marker = "; #4081 — exact-domain native-first classifier.";
    let start = source.find(marker).expect("exact-domain classifier marker");
    let block = &source[start..];

    for forbidden in [
        "(00000001 car)",
        "(00000001 cons)",
        "machine-capabilities-for-sid",
        "semantic-registry",
    ] {
        assert!(
            !block.contains(forbidden),
            "exact-domain classifier must not regain spelling/SID authority: {forbidden}"
        );
    }

    assert!(block.contains("native-first-domain-d3-car?"));
    assert!(block.contains("native-first-domain-d3-cons?"));
    assert!(block.contains("shape-or-empty"));
}

// diagnostic trigger for #4242; no production semantics
