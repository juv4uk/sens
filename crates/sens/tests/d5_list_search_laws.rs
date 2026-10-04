//! #3052/#3053 — exact Core.D5 list/search law witnesses.
//!
//! Research-only. The operation head is constructed as the ratified exact
//! five-bit Core.D5 identity. Human syntax is used only to build quoted data;
//! no human surface name and no historical Function8/Sens8 byte selects the
//! operation.

use sens::syntax::{Expr, ExprKind, Span};
use sens::{
    eval_parsed_expressions, load_core_library, parse, Bit5, CoreD5, CoreDomainIdentity, Session,
};
use std::rc::Rc;

fn d5(bits: u8, arguments: Vec<Expr>) -> Expr {
    let identity = CoreDomainIdentity::D5(CoreD5::from_word(
        Bit5::new(bits).expect("D5 coordinate must fit"),
    ));
    Expr {
        kind: ExprKind::DomainCall(identity, Rc::from(arguments.into_boxed_slice())),
        span: Span::default(),
    }
}

fn quoted(data: &str) -> Expr {
    let source = format!("(quote {data})");
    let mut parsed = parse(&source).unwrap_or_else(|error| panic!("{source}: {error:?}"));
    assert_eq!(parsed.len(), 1);
    parsed.remove(0)
}

fn run(expression: Expr) -> String {
    let mut session = Session::default();
    load_core_library(&mut session).expect("active Core should load");
    eval_parsed_expressions(&[expression], &mut session)
        .unwrap_or_else(|error| panic!("exact D5 expression failed: {error:?}"))
        .value
        .to_string()
}

#[test]
fn exact_d5_append_reverse_form_a_local_list_algebra() {
    // CURRENT OD-005 identities:
    // 10000 APPEND
    // 10001 REVERSE
    assert_eq!(
        run(d5(0b10000, vec![quoted("(a b)"), quoted("(c d)")])),
        "(a b c d)"
    );
    assert_eq!(
        run(d5(0b10001, vec![quoted("(a b c)")])),
        "(c b a)"
    );

    // Involution.
    assert_eq!(
        run(d5(
            0b10001,
            vec![d5(0b10001, vec![quoted("(a b c d)")])],
        )),
        "(a b c d)"
    );

    // Anti-homomorphism:
    // reverse(append(x,y)) = append(reverse(y), reverse(x)).
    let left = run(d5(
        0b10001,
        vec![d5(
            0b10000,
            vec![quoted("(a b)"), quoted("(c d)")],
        )],
    ));
    let right = run(d5(
        0b10000,
        vec![
            d5(0b10001, vec![quoted("(c d)")]),
            d5(0b10001, vec![quoted("(a b)")]),
        ],
    ));
    assert_eq!(left, right);
    assert_eq!(left, "(d c b a)");

    // Nested payload is opaque list data, not flattened by either operation.
    assert_eq!(
        run(d5(0b10001, vec![quoted("((a b) c (d e))")])),
        "((d e) c (a b))"
    );
}

#[test]
fn exact_d5_assoc_member_share_traversal_but_not_result_semantics() {
    // CURRENT OD-005 identities:
    // 11100 ASSOC
    // 11101 MEMBER
    assert_eq!(
        run(d5(
            0b11100,
            vec![quoted("x"), quoted("((x . first) (y . second))")],
        )),
        "(x . first)"
    );
    assert_eq!(
        run(d5(
            0b11100,
            vec![quoted("z"), quoted("((x . first) (y . second))")],
        )),
        "()"
    );

    // First-match ordering is observable.
    assert_eq!(
        run(d5(
            0b11100,
            vec![quoted("x"), quoted("((x . first) (x . second))")],
        )),
        "(x . first)"
    );

    // ASSOC admits a structural key through the Core structural-equality path.
    assert_eq!(
        run(d5(
            0b11100,
            vec![
                quoted("(a b)"),
                quoted("(((a b) . first) ((a c) . second))"),
            ],
        )),
        "((a b) . first)"
    );

    // MEMBER exposes predicate-like hit/miss rather than the matching pair.
    assert_eq!(
        run(d5(0b11101, vec![quoted("b"), quoted("(a b c)")])),
        "t"
    );
    assert_eq!(
        run(d5(0b11101, vec![quoted("z"), quoted("(a b c)")])),
        "()"
    );

    // MEMBER also uses structural equality for list elements.
    assert_eq!(
        run(d5(
            0b11101,
            vec![quoted("(a b)"), quoted("((x y) (a b) (c d))")],
        )),
        "t"
    );
}
