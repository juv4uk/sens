//! Точковий доказ: епістемічні посилання порівнюються лише D3/D1,
 //! а історичний W8 не може підмінити чинну D8-тотожність.
use sens::{
    eval_parsed_expressions, parse_domain_ladder_source_words,
    parse_mixed_exact_domain, Expr, ExprKind, Session,
};

const SOURCE: &str = include_str!("../../../lib/epistemic.lisp");
const NAME: &str = "епістеміка--рівні-посилання?";

fn helper_source() -> &'static str {
    let start = SOURCE.find("(0011 епістеміка--рівні-посилання?")
        .expect("епістемічна Lisp-функція мусить мати D4 DEFINE");
    let end = SOURCE[start..]
        .find("; supporting-evidence —")
        .expect("наступне визначення має залишатися в джерелі")
        + start;
    &SOURCE[start..end]
}

#[test]
fn historical_w8_equal_cannot_steal_ratified_d8_or_d3_identity() {
    assert_eq!(SOURCE.matches("(11110111 ").count(), 0,
        "непідтверджений старий W8 EQUAL не може бути виконуваною головою");
    assert!(SOURCE.contains(
        "(епістеміка--рівні-посилання? (evidence-claim-ref evidence) claim-ref)"
    ));

    let words = parse_domain_ladder_source_words("111 00000111 11110111")
        .expect("точні D3/D8 координати");
    assert_eq!(words.len(), 3);
    assert_eq!(words[0].coordinate.width(), 3);
    assert_eq!(words[1].coordinate.width(), 8);
    assert_eq!(words[2].coordinate.width(), 8);
    assert_eq!(words[0].coordinate.bits(), words[1].coordinate.bits());
    assert_ne!(words[0].coordinate, words[1].coordinate,
        "однаковий payload не стирає доменну ширину");
    assert_eq!(words[2].coordinate.bits(), 0b11110111);
    assert_ne!(words[0].coordinate, words[2].coordinate);

    let definitions = parse_mixed_exact_domain(helper_source())
        .expect("D3/D4 слова мають зберігати ратифіковану ширину");
    assert_eq!(definitions.len(), 1);
    let ExprKind::List(define) = &definitions[0].kind else {
        panic!("похідна структурна рівність має бути Lisp визначенням");
    };
    assert!(matches!(&define[0].kind, ExprKind::DomainIdentity(id)
        if id.width() == 4 && id.packed_bits() == 0b0011));
    let ExprKind::List(lambda) = &define[2].kind else {
        panic!("значенням визначення має бути LAMBDA");
    };
    assert!(matches!(&lambda[0].kind, ExprKind::DomainIdentity(id)
        if id.width() == 4 && id.packed_bits() == 0b0010));

    fn check_d3(expr: &Expr, seen: &mut [bool; 8]) {
        let ExprKind::List(items) = &expr.kind else { return };
        if let Some(Expr { kind: ExprKind::DomainIdentity(id), .. }) = items.first() {
            if id.width() == 3 {
                seen[id.packed_bits() as usize] = true;
            } else {
                panic!("тіло використовує лише D3 операції, а не W8/D8");
            }
        }
        for item in items.iter() {
            check_d3(item, seen);
        }
    }
    let mut seen = [false; 8];
    check_d3(&lambda[2], &mut seen);
    for code in [0b001, 0b010, 0b011, 0b100, 0b101, 0b110] {
        assert!(seen[code], "відсутня необхідна D3 операція {code:03b}");
    }
}

#[test]
fn nested_reference_equality_returns_only_exact_d1() {
    let expressions = parse_mixed_exact_domain(helper_source())
        .expect("точний D3/D4 синтаксис");
    let mut session = Session::default();
    eval_parsed_expressions(&expressions, &mut session)
        .expect("похідна Lisp-функція має визначитися без W8");

    // Позитивні, негативні, нерівна глибина, неправильний хвіст, порожній список.
    let cases = [
        ("(001 ())", "(001 ())", true),
        ("(001 а)", "(001 а)", true),
        ("(001 а)", "(001 б)", false),
        ("(001 (а))", "(001 а)", false),
        ("(001 а)", "(001 (а))", false),
        ("(001 (а б))", "(001 (а б))", true),
        ("(001 (а б))", "(001 (а в))", false),
        ("(001 (а б))", "(001 (а))", false),
        ("(001 ((а б) (в г)))", "(001 ((а б) (в г)))", true),
        ("(001 ((а б) (в г)))", "(001 ((а б) (в ґ)))", false),
        ("(001 (((а))))", "(001 (((а))))", true),
        ("(001 (((а))))", "(001 ((а)))", false),
    ];
    for (left, right, expected) in cases {
        let query = format!("({NAME} {left} {right})");
        // Той самий exact-reader, що й у визначенні функції: 001 це D3 QUOTE,
        // а не некваліфіковане число у звичайному Lisp-reader.
        let call = parse_mixed_exact_domain(&query)
            .unwrap_or_else(|error| panic!("{query}: {error}"));
        let result = eval_parsed_expressions(&call, &mut session)
            .unwrap_or_else(|error| panic!("{query}: {error}"));
        assert_eq!(
            result.value.as_predicate_bit(), Some(expected),
            "строга D1 відповідь і структурна рівність у {query}"
        );
    }
}
