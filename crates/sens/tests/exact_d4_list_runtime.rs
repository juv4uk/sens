//! Black-box exact-domain D4:1110 LIST: current evaluator, not only a Rust helper.
//! Core source always carries exact width.  D4 LIST is not D5 CDDAR or D8 SQRT.

use sens::{
    eval_parsed_expressions, Bit3, Bit4, Bija3, CoreD4, DomainIdentity,
    Expr, ExprKind, Session, Span,
};

fn id(identity: DomainIdentity) -> Expr {
    Expr { kind: ExprKind::DomainIdentity(identity), span: Span::default() }
}

fn quoted_nil() -> Expr {
    let quote: DomainIdentity = Bija3::from_word(Bit3::new(0b001).unwrap()).into();
    Expr {
        kind: ExprKind::List(vec![
            id(quote),
            Expr { kind: ExprKind::List(vec![].into()), span: Span::default() },
        ].into()),
        span: Span::default(),
    }
}

fn list(items: Vec<Expr>) -> Expr {
    let head: DomainIdentity = CoreD4::from_word(Bit4::new(0b1110).unwrap()).into();
    let mut all = vec![id(head)];
    all.extend(items);
    Expr { kind: ExprKind::List(all.into()), span: Span::default() }
}

#[test]
fn exact_list_current_eval_preserves_nil_as_one_real_list_element() {
    let result = eval_parsed_expressions(
        &[list(vec![quoted_nil()])], &mut Session::default(),
    ).expect("ratified D4:1110 LIST must be callable in current evaluator");
    assert_eq!(result.value.to_string(), "(())",
               "LIST of quoted EMPTY must be a one-element proper list");
}

#[test]
fn exact_list_current_eval_zero_and_multiple_arguments() {
    let empty = eval_parsed_expressions(
        &[list(vec![])], &mut Session::default(),
    ).expect("zero-argument D4:1110 LIST is empty");
    assert_eq!(empty.value.to_string(), "()");

    let nested = eval_parsed_expressions(
        &[list(vec![quoted_nil(), quoted_nil()])], &mut Session::default(),
    ).expect("D4 LIST must preserve multiple evaluated NILs");
    assert_eq!(nested.value.to_string(), "(() ())");
}
