
#[test]
fn label_surface_lowers_to_exact_d5_00100() {
    let parsed = parse("(мітка self (функція (x) x))").expect("parse LABEL");
    let lowered = lower_program(&parsed);
    let ExprKind::DomainCall(CoreDomainIdentity::D5(word), _) = &lowered[0].kind else {
        panic!("LABEL surface must lower to exact D5 DomainCall");
    };
    assert_eq!(word.word().packed_bits(), 0b00100);
}

use sens::{eval_program, lower_program, parse, CoreDomainIdentity, ErrorKind, ExprKind, Session};

#[test]
fn d5_label_recurses_locally() {
    let source = r#"
        ((мітка self
           (функція (xs)
             (за-умовою
               ((атом? xs) (як-є done))
               ((тотожне? xs xs) (self (решта xs))))))
         (як-є (a b c d)))
    "#;
    let mut session = Session::default();
    let result = eval_program(source, &mut session).expect("D5 LABEL recursion");
    assert_eq!(result.value.to_string(), "done");

    let error = eval_program("self", &mut session)
        .expect_err("LABEL self-binding must remain local");
    assert_eq!(error.kind, ErrorKind::UnknownSymbol);
}

#[test]
fn d5_label_rejects_non_closure() {
    let mut session = Session::default();
    let error = eval_program("(мітка x (як-є datum))", &mut session)
        .expect_err("LABEL requires a closure");
    assert_eq!(error.kind, ErrorKind::Type);
    assert!(error.message.contains("D5:00100 LABEL"));
}
