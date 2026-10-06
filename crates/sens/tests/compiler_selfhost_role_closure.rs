//! sens#3824 — whole-current-nucleus role closure through executable SENS law.
//!
//! The inventory comes from parsing/lowering the real compiler nucleus.  This
//! test contains no DomainIdentity->role table.

use sens::syntax::{Expr, ExprKind};
use sens::{
    compiler_execution_role_from_sens, compiler_lowering_role_from_sens,
    compiler_program_artifact_from_program_data, compiler_program_artifact_from_sens,
    lower_program, parse, wire_encode_program, Bija3, Bit3, Bit4, Bit5, Bit8,
    CompilerExecutionRole, CompilerLoweringRole, CoreD4, CoreD5, CoreD8,
    CoreDomainIdentity, Value,
};

const NUCLEUS: &str = include_str!("../../../lib/compiler-nucleus.lisp");

fn collect_roles(expr: &Expr, roles: &mut Vec<CompilerLoweringRole>) {
    match &expr.kind {
        ExprKind::DomainCall(identity, args) => {
            let role = compiler_lowering_role_from_sens(*identity)
                .unwrap_or_else(|error| panic!("SENS lowering-role execution failed: {error:?}"))
                .unwrap_or_else(|| {
                    panic!(
                        "current compiler nucleus contains an exact-domain call without a selfhost lowering role: {identity}"
                    )
                });
            if !roles.contains(&role) {
                roles.push(role);
            }
            for arg in args.iter() {
                collect_roles(arg, roles);
            }
        }
        ExprKind::List(items) => {
            for item in items.iter() {
                collect_roles(item, roles);
            }
        }
        ExprKind::Pair(head, tail) => {
            collect_roles(head, roles);
            collect_roles(tail, roles);
        }
        ExprKind::Sid(_)
        | ExprKind::Call(_, _)
        | ExprKind::Number(_, _)
        | ExprKind::Rational(_)
        | ExprKind::BinaryNumber(_)
        | ExprKind::NumericBuffer(_)
        | ExprKind::DomainIdentity(_)
        | ExprKind::String(_)
        | ExprKind::Symbol(_)
        | ExprKind::Local { .. } => {}
    }
}

#[test]
fn real_compiler_nucleus_is_closed_over_nine_sens_derived_roles() {
    let parsed = parse(NUCLEUS).expect("current compiler nucleus parses");
    let lowered = lower_program(&parsed);

    let mut roles = Vec::new();
    for expr in &lowered {
        collect_roles(expr, &mut roles);
    }

    for expected in [
        CompilerLoweringRole::QuoteForm,
        CompilerLoweringRole::AtomPredicate,
        CompilerLoweringRole::SelectorTail,
        CompilerLoweringRole::SelectorHead,
        CompilerLoweringRole::AtomEquality,
        CompilerLoweringRole::CondForm,
        CompilerLoweringRole::PairConstruct,
        CompilerLoweringRole::LambdaForm,
        CompilerLoweringRole::DefineForm,
    ] {
        assert!(
            roles.contains(&expected),
            "current compiler nucleus did not exercise expected SENS-derived role {expected:?}; observed {roles:?}"
        );
    }

    assert_eq!(roles.len(), 9, "bounded current nucleus closure must stay explicit");
}

#[test]
fn equal_payloads_in_other_domains_do_not_gain_selfhost_roles() {
    let cases = [
        CoreDomainIdentity::D4(CoreD4::from_word(Bit4::new(0b0001).unwrap())),
        CoreDomainIdentity::D5(CoreD5::from_word(Bit5::new(0b00010).unwrap())),
        CoreDomainIdentity::D8(CoreD8::from_word(Bit8::new(0b0000_0010).unwrap())),
    ];

    for identity in cases {
        assert_eq!(
            compiler_lowering_role_from_sens(identity)
                .expect("wrong-domain query is a normal fail-closed result"),
            None,
            "equal packed payload under another domain must not inherit a compiler role"
        );
    }
}

#[test]
fn established_three_role_execution_api_remains_compatibility_stable() {
    let parsed = parse(NUCLEUS).expect("current compiler nucleus parses");
    let lowered = lower_program(&parsed);

    let mut saw_old_role = false;
    fn walk(expr: &Expr, saw_old_role: &mut bool) {
        match &expr.kind {
            ExprKind::DomainCall(identity, args) => {
                if let Some(role) = compiler_execution_role_from_sens(*identity)
                    .expect("bounded execution-role API remains executable")
                {
                    assert!(matches!(
                        role,
                        CompilerExecutionRole::SelectorHead
                            | CompilerExecutionRole::SelectorTail
                            | CompilerExecutionRole::PairConstruct
                    ));
                    *saw_old_role = true;
                }
                for arg in args.iter() {
                    walk(arg, saw_old_role);
                }
            }
            ExprKind::List(items) => {
                for item in items.iter() {
                    walk(item, saw_old_role);
                }
            }
            ExprKind::Pair(head, tail) => {
                walk(head, saw_old_role);
                walk(tail, saw_old_role);
            }
            _ => {}
        }
    }

    for expr in &lowered {
        walk(expr, &mut saw_old_role);
    }
    assert!(saw_old_role, "current nucleus must still exercise the merged three-role vertical");
}


fn list_values(value: &Value) -> Option<Vec<&Value>> {
    let mut out = Vec::new();
    let mut cursor = value;
    loop {
        match cursor {
            Value::Nil => return Some(out),
            Value::Pair(head, tail) => {
                out.push(head.as_ref());
                cursor = tail.as_ref();
            }
            _ => return None,
        }
    }
}

fn artifact_requests(value: &Value) -> Option<Vec<&Value>> {
    let outer = list_values(value)?;
    if outer.len() != 2 {
        return None;
    }
    if !matches!(
        outer[0],
        Value::Symbol(name) if name.as_ref() == "compiler-compilation-artifact/1"
    ) {
        return None;
    }
    list_values(outer[1])
}

fn d3(raw: u8) -> CoreDomainIdentity {
    CoreDomainIdentity::D3(Bija3::from_word(Bit3::new(raw).expect("D3 word")))
}

fn domain_call(identity: CoreDomainIdentity, arguments: Vec<Expr>) -> Expr {
    Expr {
        kind: ExprKind::DomainCall(identity, arguments.into()),
        span: Default::default(),
    }
}

#[test]
fn sens_whole_program_body_emits_deterministic_real_nucleus_artifact() {
    let first = compiler_program_artifact_from_sens(NUCLEUS)
        .expect("SENS whole-program compiler executes on the real nucleus");
    let second = compiler_program_artifact_from_sens(NUCLEUS)
        .expect("second SENS whole-program compile executes");
    assert_eq!(first, second, "whole-program artifact must be deterministic");

    let requests = artifact_requests(&first).expect("versioned whole-program artifact");
    assert!(
        requests.len() >= 9,
        "real nucleus must exercise the complete current D3+D4 compiler closure"
    );

    let observed_roles = requests
        .iter()
        .map(|request| {
            let row = list_values(request).expect("compiler request is a proper list");
            assert_eq!(row.len(), 4);
            match row[1] {
                Value::Symbol(role) => role.to_string(),
                other => panic!("compiler request role must be symbolic, got {other}"),
            }
        })
        .collect::<std::collections::HashSet<_>>();

    let expected_roles = [
        "quote-form",
        "atom-predicate",
        "selector-tail",
        "selector-head",
        "atom-equality",
        "cond-form",
        "pair-construct",
        "lambda-form",
        "define-form",
    ]
    .into_iter()
    .map(str::to_string)
    .collect::<std::collections::HashSet<_>>();

    assert_eq!(observed_roles, expected_roles);
}

#[test]
fn sens_whole_program_body_owns_quote_opacity_and_fail_closed_domain_admission() {
    let quoted_d8 = domain_call(
        d3(0b001),
        vec![domain_call(
            CoreDomainIdentity::D8(CoreD8::from_word(Bit8::new(0b0000_0100).unwrap())),
            vec![],
        )],
    );
    let quote_artifact =
        compiler_program_artifact_from_program_data(&wire_encode_program(&[quoted_d8]))
            .expect("quoted D8 is opaque program data");
    let quote_requests = artifact_requests(&quote_artifact).expect("QUOTE artifact");
    assert_eq!(
        quote_requests.len(),
        1,
        "SENS traversal, not the host, must stop at quoted children"
    );
    let quote_row = list_values(quote_requests[0]).unwrap();
    assert!(matches!(
        quote_row[1],
        Value::Symbol(role) if role.as_ref() == "quote-form"
    ));

    let admitted = domain_call(d3(0b100), vec![]);
    assert!(
        artifact_requests(
            &compiler_program_artifact_from_program_data(&wire_encode_program(&[admitted]))
                .expect("D3 CAR is an admitted compiler node")
        )
        .is_some()
    );

    let wrong_domain = domain_call(
        CoreDomainIdentity::D4(CoreD4::from_word(Bit4::new(0b0100).unwrap())),
        vec![],
    );
    let wrong_domain_result =
        compiler_program_artifact_from_program_data(&wire_encode_program(&[wrong_domain]))
            .expect("unsupported D4 coordinate fails closed as a language result");
    assert!(matches!(
        wrong_domain_result,
        Value::Symbol(ref name) if name.as_ref() == "compiler-failure"
    ));

    let d8 = domain_call(
        CoreDomainIdentity::D8(CoreD8::from_word(Bit8::new(0b0000_0100).unwrap())),
        vec![],
    );
    let d8_result = compiler_program_artifact_from_program_data(&wire_encode_program(&[d8]))
        .expect("D8 fails closed as a language result");
    assert!(matches!(
        d8_result,
        Value::Symbol(ref name) if name.as_ref() == "compiler-failure"
    ));
}
