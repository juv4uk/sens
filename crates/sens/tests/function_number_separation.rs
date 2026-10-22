//! Чинний SENS: точна D5 identity не є числом D24+ і навпаки.
//! Людський десятковий запис аргументів належить математичному D24+, не коду D5.
use sens::{
    eval_program, lower_program, parse, parse_exact_domain_source, Bit5, CoreD5,
    DomainIdentity, ExprKind, Session, Value,
};

fn додавання_d5() -> DomainIdentity {
    DomainIdentity::D5(CoreD5::from_word(Bit5::new(0b01010).expect("точна п'ятибітність")))
}

#[test]
fn українське_додавання_приймає_десяткову_проєкцію_d24_з_d5_головою() {
    let source = "(додати 4 6)";
    let lowered = lower_program(&parse(source).expect("читач українського Lisp"));
    let [expr] = lowered.as_slice() else {
        panic!("потрібен один виклик");
    };
    assert!(matches!(
        &expr.kind,
        ExprKind::DomainCall(identity, _)
            if (identity.width(), identity.packed_bits()) == (5, 0b01010)
    ), "голова «додати» мусить мати D5:01010");

    let result = eval_program(source, &mut Session::default())
        .expect("живе додавання D24+ у SENS").value;
    let Value::BinaryNumber(number) = &result else {
        panic!("арифметика мусить повертати D24+, а не функцію: {result:?}");
    };
    assert_eq!(number.numeric_domain_width(), Some(24));
    assert_eq!(number.to_decimal_string(), "10");
    assert_ne!(result, Value::DomainIdentity(додавання_d5()));
}

#[test]
fn голе_d5_слово_є_доменом_а_не_десятковим_числом() {
    let parsed = parse_exact_domain_source("01010").expect("точний доменний читач");
    let [expr] = parsed.as_slice() else {
        panic!("потрібна одна D5 identity");
    };
    assert_eq!(expr.kind, ExprKind::DomainIdentity(додавання_d5()));
    let numeric = eval_program("10", &mut Session::default())
        .expect("людська десяткова проєкція D24+ у SENS")
        .value;
    assert_ne!(Value::DomainIdentity(додавання_d5()), numeric);
}

#[test]
fn людські_числа_є_d24_операндами_але_не_кодами_функцій() {
    let value = eval_program("(додати 1 2)", &mut Session::default())
        .expect("SENS виконує D5 над сучасною десятковою проєкцією D24+")
        .value;
    let Value::BinaryNumber(number) = &value else {
        panic!("потрібне математичне значення D24+, отримано: {value:?}");
    };
    assert_eq!(number.numeric_domain_width(), Some(24));
    assert_eq!(number.to_decimal_string(), "3");
    assert_ne!(value, Value::DomainIdentity(додавання_d5()));
}

#[test]
fn точні_d5_і_d8_з_однаковим_payload_не_тотожні() {
    let d5 = parse_exact_domain_source("01010").expect("D5");
    let d8 = parse_exact_domain_source("00001010").expect("D8");
    assert!(matches!(&d5[0].kind, ExprKind::DomainIdentity(DomainIdentity::D5(_))));
    assert!(matches!(&d8[0].kind, ExprKind::DomainIdentity(DomainIdentity::D8(_))));
    assert_ne!(d5[0].kind, d8[0].kind, "ширина є частиною тотожності");
}
