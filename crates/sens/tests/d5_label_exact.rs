use sens::{eval_program, ErrorKind, Session};

#[test]
fn d5_label_recurses_locally() {
    let source = r#"
        ((мітка self
           (функція (n)
             (за-умовою
               ((нуль? n) (як-є done))
               ((тотожне? n n) (self (відняти n 1))))))
         12)
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
