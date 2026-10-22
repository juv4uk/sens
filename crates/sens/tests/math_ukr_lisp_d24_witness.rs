//! Наскрізний свідок межі Lisp-проєкції та вже допущеної арифметики D24+.
//! Не є свідком виконання фізичного T5M: #d24 лишається перехідним
//! явним текстовим носієм, а не новим канонічним синтаксисом SENS.
use sens::{eval_program, lower_program, parse, ErrorKind, ExprKind, Session, Value};

#[test]
fn українські_d5_виклики_виконують_явні_d24_без_неявних_літералів() {
    let один = "000000000000000000000001";
    let два = "000000000000000000000010";
    let нуль = "000000000000000000000000";
    let максимум_д24 = "011111111111111111111111";

    for (id, head, opcode, lhs, rhs, expected_width, expected_decimal) in [
        ("add", "додати", 0b01010, один, два, 24, "3"),
        ("sub-negative", "відняти", 0b01011, нуль, один, 24, "-1"),
        (
            "add-carry",
            "додати",
            0b01010,
            максимум_д24,
            один,
            48,
            "8388608",
        ),
    ] {
        let source = format!("({head} #d24:{lhs} #d24:{rhs})");
        let parsed = parse(&source).expect("точний D24-носій у людській Lisp-проєкції");
        let lowered = lower_program(&parsed);
        let ExprKind::DomainCall(identity, _) = &lowered[0].kind else {
            panic!(
                "test_id={id} layer=lower expected=DomainCall actual={:?}",
                lowered[0].kind
            );
        };
        assert_eq!(
            (identity.width(), identity.packed_bits()),
            (5, opcode),
            "test_id={id} layer=identity expected=D5:{opcode:05b}"
        );

        let actual = eval_program(&source, &mut Session::default())
            .unwrap_or_else(|error| {
                panic!("test_id={id} layer=lisp-to-eval expected=success actual={error}")
            })
            .value;
        let Value::BinaryNumber(ref word) = actual else {
            panic!("test_id={id} layer=eval expected=D{expected_width} actual={actual:?}");
        };
        assert_eq!(
            word.numeric_domain_width(),
            Some(expected_width),
            "test_id={id} layer=domain expected=D{expected_width}"
        );
        assert_eq!(
            word.exact_numeric_domain_bits().unwrap().len(),
            expected_width,
            "test_id={id} layer=bits expected_width={expected_width}"
        );
        assert_eq!(
            word.to_decimal_string(),
            expected_decimal,
            "test_id={id} layer=human expected={expected_decimal}"
        );
    }

    // Людський напис сам не надає Number(1) права стати D24-операндом.
    let error = eval_program("(додати 1 2)", &mut Session::default())
        .expect_err("некваліфіковані історичні числа не допускаються в арифметику D24+");
    assert_eq!(
        error.kind,
        ErrorKind::Type,
        "test_id=unqualified-numeric-input layer=admission expected=Type"
    );
}
