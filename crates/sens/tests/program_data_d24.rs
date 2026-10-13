//! Свідки перенесення даних компілятора на числові домени D24+.
//! Зовнішній тест не залежить від історичного #[cfg(test)] реєстру SID8.

use sens::{
    expr_to_exact_program_data, lowered_program_to_exact_data, Bija3, BinaryNumber, Bit3,
    CoreDomainIdentity, ErrorKind, Exactness, Expr, ExprKind, Rational, Span, Value,
};
use std::rc::Rc;

fn вузол(kind: ExprKind) -> Expr {
    Expr { kind, span: Span::default() }
}

fn доменне_число(width: usize) -> Expr {
    let mut bits = vec![0u8; width];
    bits[width - 1] = 1;
    вузол(ExprKind::BinaryNumber(
        BinaryNumber::from_numeric_domain_bits(width, &bits)
            .expect("явний ратифікований D24+"),
    ))
}

#[test]
fn тотожність_d24_і_d48_не_зливається_за_рівним_значенням() {
    let d24 = expr_to_exact_program_data(&доменне_число(24)).unwrap();
    let d48 = expr_to_exact_program_data(&доменне_число(48)).unwrap();
    assert_ne!(d24, d48);
    assert!(matches!(d24, Value::BinaryNumber(ref x) if x.numeric_domain_width() == Some(24)));
    assert!(matches!(d48, Value::BinaryNumber(ref x) if x.numeric_domain_width() == Some(48)));
}

#[test]
fn звичайні_числові_літерали_та_голі_біти_не_є_d24() {
    let old = [
        вузол(ExprKind::Number(1.0, Exactness::Exact)),
        вузол(ExprKind::Rational(Rational::from_literal("1", "2").unwrap())),
        вузол(ExprKind::BinaryNumber(BinaryNumber::parse("1").unwrap())),
    ];
    for expr in old {
        let error = expr_to_exact_program_data(&expr).unwrap_err();
        assert_eq!(error.kind, ErrorKind::InvalidForm);
    }
}

#[test]
fn вкладення_не_надає_старому_числу_нової_семантики() {
    let old = вузол(ExprKind::Number(3.0, Exactness::Exact));
    let list = вузол(ExprKind::List(Rc::from([old.clone()])));
    assert!(expr_to_exact_program_data(&list).is_err());
    let pair = вузол(ExprKind::Pair(Rc::new(доменне_число(24)), Rc::new(old.clone())));
    assert!(expr_to_exact_program_data(&pair).is_err());
    let quote = CoreDomainIdentity::D3(Bija3::from_word(Bit3::new(0b001).unwrap()));
    let call = вузол(ExprKind::DomainCall(quote, Rc::from([old])));
    assert!(expr_to_exact_program_data(&call).is_err());
}

#[test]
fn доменний_виклик_з_d24_проходить_точне_перетворення() {
    let quote = CoreDomainIdentity::D3(Bija3::from_word(Bit3::new(0b001).unwrap()));
    let call = вузол(ExprKind::DomainCall(quote, Rc::from([доменне_число(24)])));
    let program = lowered_program_to_exact_data(&[call]).expect("D3 і D24 узгоджені");
    assert!(matches!(program, Value::Pair(_, _)));
}


#[test]
fn вичерпний_точковий_тест_2046_координат_з_реальним_program_data() {
    use sens::domain_ladder::DomainCoordinate;
    use sens::{BinarySourceWord, DomainIdentity, Bit1, Bit2, Bit4, Bit5, Bit6, Bit7, Bit8, Bit9};
    use std::collections::HashSet;

    let mut seen = HashSet::new();
    let mut typed = Vec::new();
    let mut all = 0usize;
    let mut held_d10 = 0usize;

    for width in 1u8..=10 {
        for bits in 0u16..(1u16 << width) {
            let coordinate = DomainCoordinate::new(width, bits).expect("кожне число має точну ширину");
            assert_eq!((coordinate.width(), coordinate.bits()), (width, bits));
            assert!(seen.insert((width, bits)), "зіткнення бітів між доменами");
            all += 1;
            if width == 10 {
                assert_eq!(coordinate.owner_residency(), Some(true));
                held_d10 += 1;
                continue; // D10 has no admitted AST identity yet.
            }
            let source = match width {
                1 => BinarySourceWord::W1(Bit1::new(bits as u8).unwrap()),
                2 => BinarySourceWord::W2(Bit2::new(bits as u8).unwrap()),
                3 => BinarySourceWord::W3(Bit3::new(bits as u8).unwrap()),
                4 => BinarySourceWord::W4(Bit4::new(bits as u8).unwrap()),
                5 => BinarySourceWord::W5(Bit5::new(bits as u8).unwrap()),
                6 => BinarySourceWord::W6(Bit6::new(bits as u8).unwrap()),
                7 => BinarySourceWord::W7(Bit7::new(bits as u8).unwrap()),
                8 => BinarySourceWord::W8(Bit8::new(bits as u8).unwrap()),
                9 => BinarySourceWord::W9(Bit9::new(bits).unwrap()),
                _ => unreachable!(),
            };
            let id = DomainIdentity::from_source_word(source);
            assert_eq!(id.width(), usize::from(width));
            assert_eq!(id.packed_bits(), bits);
            let v = expr_to_exact_program_data(&вузол(ExprKind::DomainIdentity(id)))
                .expect("існуюча D1–D9 AST-тотожність не губить біти");
            assert!(matches!(v, Value::DomainIdentity(x) if x == id));
            typed.push(вузол(ExprKind::DomainIdentity(id)));
            // The D7 text-data domain must never gain Core callable status.
            if width == 7 {
                assert!(id.core_operation().is_none());
            }
        }
    }

    let converted = lowered_program_to_exact_data(&typed)
        .expect("1022 бітно-точних AST атомів проходять єдиним шляхом");
    let mut current = &converted;
    for form in &typed {
        let ExprKind::DomainIdentity(expected) = &form.kind else { unreachable!() };
        let Value::Pair(head, tail) = current else { panic!("втрачена форма"); };
        assert!(matches!(head.as_ref(), Value::DomainIdentity(actual) if *actual == *expected));
        current = tail.as_ref();
    }
    assert!(matches!(current, Value::Nil));
    assert_eq!(all, 2046);
    assert_eq!(seen.len(), 2046);
    assert_eq!(typed.len(), 1022);
    assert_eq!(held_d10, 1024);

    let d3 = DomainCoordinate::new(3, 0b010).unwrap();
    let d4 = DomainCoordinate::new(4, 0b0010).unwrap();
    assert_eq!(d3.bits(), d4.bits());
    assert_ne!(d3, d4);
}

#[test]
fn ітеративний_обхід_зберігає_порядок_форми_та_блокує_надмірну_глибину() {
    let quote = CoreDomainIdentity::D3(Bija3::from_word(Bit3::new(0b001).unwrap()));
    let atom = вузол(ExprKind::DomainIdentity(sens::DomainIdentity::from(quote)));
    let pair = вузол(ExprKind::Pair(
        Rc::new(вузол(ExprKind::List(Rc::from([atom.clone(), доменне_число(24)])))),
        Rc::new(доменне_число(48)),
    ));
    let call = вузол(ExprKind::DomainCall(quote, Rc::from([pair])));
    let converted = expr_to_exact_program_data(&call).unwrap();

    let Value::Pair(head, tail) = &converted else { panic!("очікувався виклик"); };
    assert!(matches!(head.as_ref(), Value::DomainIdentity(id) if id.width() == 3 && id.packed_bits() == 1));
    let Value::Pair(argument, nil) = tail.as_ref() else { panic!("один аргумент"); };
    assert!(matches!(nil.as_ref(), Value::Nil));
    let Value::Pair(first, second) = argument.as_ref() else { panic!("пара"); };
    assert!(matches!(second.as_ref(), Value::BinaryNumber(n) if n.numeric_domain_width() == Some(48)));
    let Value::Pair(first_atom, t) = first.as_ref() else { panic!("перший елемент списку"); };
    assert!(matches!(first_atom.as_ref(), Value::DomainIdentity(id) if id.width() == 3));
    let Value::Pair(second_num, n) = t.as_ref() else { panic!("другий елемент списку"); };
    assert!(matches!(second_num.as_ref(), Value::BinaryNumber(v) if v.numeric_domain_width() == Some(24)));
    assert!(matches!(n.as_ref(), Value::Nil));

    // Invalid legacy node nested at depth must not be sanitized by the walk.
    let bad = вузол(ExprKind::Sid(sens::sens!(00100011)));
    assert_eq!(expr_to_exact_program_data(&вузол(ExprKind::List(Rc::from([bad]))))
        .unwrap_err().kind, ErrorKind::InvalidForm);

    let mut too_deep = вузол(ExprKind::DomainIdentity(sens::DomainIdentity::from(quote)));
    for _ in 0..800 {
        too_deep = вузол(ExprKind::List(Rc::from([too_deep])));
    }
    let error = expr_to_exact_program_data(&too_deep).unwrap_err();
    assert_eq!(error.kind, ErrorKind::InvalidForm, "глибина має відхилятися, а не обвалювати стек");
}
