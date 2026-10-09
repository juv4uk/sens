use sens::{
    domain_identity_shape_or_empty_mechanism, eval_parsed_expressions, eval_program,
    expr_to_exact_program_data, load_core_library, lower_program, parse,
    parse_mixed_exact_domain, Bit4, CoreD4, DomainIdentity, Expr, ExprKind, Sens8, Session, Value,
};
use std::fs;
use std::path::PathBuf;
use std::rc::Rc;

fn repo_root() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../..")
}

fn load_mixed_lisp_file(path: &str, session: &mut Session) {
    let path = repo_root().join(path);
    let source = fs::read_to_string(&path)
        .unwrap_or_else(|error| panic!("{} must exist: {error}", path.display()));
    let expressions = parse_mixed_exact_domain(&source)
        .unwrap_or_else(|error| panic!("{} must parse as mixed exact source: {error}", path.display()));
    eval_parsed_expressions(&expressions, session)
        .unwrap_or_else(|error| panic!("{} must load through mixed exact source: {error}", path.display()));
}

fn load_lisp_file(path: &str, session: &mut Session) {
    let path = repo_root().join(path);
    let source = fs::read_to_string(&path)
        .unwrap_or_else(|error| panic!("{} must exist: {error}", path.display()));
    eval_program(&source, session)
        .unwrap_or_else(|error| panic!("{} must load: {error}", path.display()));
}


fn collect_sid_call_heads(expression: &Expr, out: &mut Vec<Sens8>) {
    match &expression.kind {
        ExprKind::List(items) => {
            if let Some(first) = items.first() {
                if let ExprKind::Sid(identity) = &first.kind {
                    out.push(*identity);
                }
            }
            for item in items.iter() {
                collect_sid_call_heads(item, out);
            }
        }
        ExprKind::Pair(head, tail) => {
            collect_sid_call_heads(head, out);
            collect_sid_call_heads(tail, out);
        }
        _ => {}
    }
}

fn native_session() -> Session {
    let mut session = Session::default();
    load_core_library(&mut session).expect("core");
    load_lisp_file("lib/machine/layout/pair-x86-64.lisp", &mut session);
    load_lisp_file("lib/machine/operands/x86-64.lisp", &mut session);
    load_lisp_file("lib/machine/lowering/semantic-x86-64.lisp", &mut session);
    // native-first is now migrated to exact D3/D4 heads while keeping local
    // symbols/human lexical names, so load it through the bounded mixed-source
    // bridge rather than the ordinary parser's decimal/SID grammar.
    load_mixed_lisp_file("lib/machine/dispatch/native-first.lisp", &mut session);
    load_mixed_lisp_file("lib/machine/dispatch/native-first-execute.lisp", &mut session);
    session
}

#[test]
fn whole_native_first_source_has_no_legacy_sid_or_call_nodes() {
    let path = repo_root().join("lib/machine/dispatch/native-first.lisp");
    let source = fs::read_to_string(&path)
        .unwrap_or_else(|error| panic!("{} must exist: {error}", path.display()));
    let parsed = parse_mixed_exact_domain(&source)
        .unwrap_or_else(|error| panic!("{} must parse as exact mixed source: {error}", path.display()));
    let lowered = lower_program(&parsed);

    for (index, expression) in lowered.iter().enumerate() {
        expr_to_exact_program_data(expression).unwrap_or_else(|error| {
            panic!("native-first form {index} contains legacy Sid/Call identity: {error}")
        });
    }
}

#[test]
fn core4_exact_list_is_visible_to_native_first_fallback_by_behavior() {
    let mut session = native_session();
    let result = eval_program(
        "(native-first-fallback (quote payload))",
        &mut session,
    )
    .expect("native-first fallback must execute exact D4 LIST")
    .value;
    assert_eq!(result.to_string(), "(evaluator-fallback payload)");
}

#[test]
fn exact_d6_let_uses_only_its_lisp_owned_macro_mechanism() {
    let mut session = Session::default();
    load_core_library(&mut session).expect("core");
    let forms = parse_mixed_exact_domain("(001000 ((x 41)) x)")
        .expect("exact D6 LET identity must parse");
    let result = eval_parsed_expressions(&forms, &mut session)
        .expect("ratified D6 LET macro mechanism must execute");
    assert_eq!(result.value, Value::Number(41.0, sens::Exactness::Exact));
}

#[test]
fn direct_exact_car_from_mixed_source_executes() {
    let mut session = Session::default();
    load_core_library(&mut session).expect("core");
    let forms = parse_mixed_exact_domain("(100 (001 (41 42)))")
        .expect("direct exact CAR source");
    let result = eval_parsed_expressions(&forms, &mut session)
        .expect("direct exact CAR must execute");
    assert_eq!(result.value.to_string(), "41");
}

#[test]
fn direct_lambda_application_with_exact_initializer_executes() {
    let mut session = Session::default();
    load_core_library(&mut session).expect("core");
    let forms = parse_mixed_exact_domain(
        "((00001000 (y) y) (100 (001 (41 42))))",
    )
    .expect("direct LET-equivalent lambda application");
    let result = eval_parsed_expressions(&forms, &mut session)
        .expect("exact initializer must execute as a lambda argument");
    assert_eq!(result.value.to_string(), "41");
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

    let actual = eval_program(
        "(native-first-plan-domain __native_first_shape __native_first_expr)",
        &mut session,
    )
    .expect("exact-domain native plan")
    .value;
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

#[test]
fn native_first_execute_keeps_only_named_eval_and_read_all_compatibility_heads() {
    let path = repo_root().join("lib/machine/dispatch/native-first-execute.lisp");
    let source = fs::read_to_string(&path)
        .unwrap_or_else(|error| panic!("{} must exist: {error}", path.display()));
    let expressions = parse_mixed_exact_domain(&source)
        .expect("native-first execution bridge must parse through exact-domain reader");
    let mut legacy_heads = Vec::new();
    for expression in &expressions {
        collect_sid_call_heads(expression, &mut legacy_heads);
    }

    assert_eq!(
        legacy_heads.len(),
        2,
        "only the documented EVAL/READ-ALL compatibility call heads may remain"
    );
    assert!(
        legacy_heads.contains(&sens::sens!(01001101)),
        "EVAL compatibility head must stay explicit"
    );
    assert!(
        legacy_heads.contains(&sens::sens!(01001011)),
        "READ-ALL compatibility head must stay explicit"
    );
}