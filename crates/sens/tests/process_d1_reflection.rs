//! Незалежний SENS-свідок п'яти обчислених D1 істин через D3 ATOM/QUOTE.
//! Працює без процесу ОС та UTF-8/D24+ бібліотеки.
use sens::{
    eval_parsed_expressions, parse_mixed_exact_domain_process_tcp_source, ErrorKind, Expr,
    ExprKind, Session,
};

const SOURCE: &str = include_str!("../../../lib/process.lisp");
const PATH: &str = "lib/process.lisp";

fn visit(expr: &Expr, found: &mut usize) {
    if let ExprKind::List(items) = &expr.kind {
        if let Some(head) = items.first() {
            if let ExprKind::DomainIdentity(code) = head.kind {
                if code.width() == 3 && code.packed_bits() == 0b010 {
                    assert_eq!(items.len(), 2, "D3:010 ATOM takes one operand");
                    let ExprKind::List(inner) = &items[1].kind else {
                        panic!("D3 ATOM must consume quoted D3 NIL");
                    };
                    let ExprKind::DomainIdentity(quote) = inner[0].kind else {
                        panic!("D3 QUOTE must remain an exact identity");
                    };
                    assert_eq!((quote.width(), quote.packed_bits()), (3, 0b001));
                    assert_eq!(inner.len(), 2, "QUOTE takes exactly one D3 value");
                    *found += 1;
                }
            }
        }
        for part in items.iter() {
            visit(part, found);
        }
    }
}

#[test]
fn five_live_process_truth_branches_use_real_d3_atom_quote() {
    let parsed = parse_mixed_exact_domain_process_tcp_source(PATH, SOURCE)
        .expect("process source must pass the exact path-bound reader");
    let mut count = 0;
    for form in &parsed {
        visit(form, &mut count);
    }
    assert_eq!(
        count, 5,
        "all five D1 branch values must be computed by SENS"
    );
    assert_eq!(SOURCE.matches("(атом? (як-є ()))").count(), 5);
    assert_eq!(
        SOURCE.matches("(тотожне?").count(),
        3,
        "do not silently remove the three strict D3 comparisons"
    );
    assert!(
        !SOURCE.contains("((функція"),
        "anonymous D5 value-call is not an admitted mechanism"
    );
}

fn eval_exact(source: &str) -> Result<sens::Value, sens::LanguageError> {
    let expressions = parse_mixed_exact_domain_process_tcp_source(PATH, source)?;
    Ok(eval_parsed_expressions(&expressions, &mut Session::default())?.value)
}

#[test]
fn domain_not_eq_truth_table_and_strict_fail_closed() {
    for (source, expected) in [
        ("(0100 (101 (001 decoded) (001 decoded)))", false),
        ("(0100 (101 (001 decoded) (001 rejected)))", true),
    ] {
        let actual = eval_exact(source).expect("D3 EQ and D4 NOT must run");
        assert_eq!(
            actual.as_predicate_bit(),
            Some(expected),
            "{source}: exact D1 result is required, never numeric truthiness"
        );
    }
    let failure = eval_exact("(0100 (001 ()))")
        .expect_err("D3 structural empty must never coerce into D1 NO");
    assert_eq!(failure.kind, ErrorKind::Type);
    assert!(
        failure.message.contains("D1"),
        "strict D1 rejection: {failure:?}"
    );
}

#[test]
fn path_pinned_process_reader_does_not_admit_ambient_files() {
    assert!(parse_mixed_exact_domain_process_tcp_source(
        "lib/random.lisp",
        "(0100 (101 (001 yes) (001 no)))",
    )
    .is_err());
}
