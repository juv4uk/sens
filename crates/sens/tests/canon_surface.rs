use sens::{eval_program, ErrorKind, Session};

fn eval(source: &str) -> String {
    let mut session = Session::default();
    eval_program(source, &mut session)
        .expect("canonical surface program should evaluate")
        .value
        .to_string()
}

#[test]
fn historical_ukrainian_and_sanskrit_surfaces_are_observationally_equal() {
    let cases = [
        ("(quote (1 2 3))", "(як-є (1 2 3))", "(svarūpa (1 2 3))"),
        ("(atom? (quote кіт))", "(атом? (як-є кіт))", "(aṇu (svarūpa кіт))"),
        ("(eq? (quote кіт) (quote кіт))", "(тотожне? (як-є кіт) (як-є кіт))", "(abheda (svarūpa кіт) (svarūpa кіт))"),
        ("(cons 1 2)", "(сполучити 1 2)", "(saṃyuj 1 2)"),
        ("(car (cons 1 2))", "(перше (сполучити 1 2))", "(ādi (saṃyuj 1 2))"),
        ("(cdr (quote (1 2 3)))", "(решта (як-є (1 2 3)))", "(śeṣa (svarūpa (1 2 3)))"),
        ("(cond (() (quote ні)) ((atom? ()) (quote так)))", "(за-умовою (() (як-є ні)) ((атом? ()) (як-є так)))", "(anukrama (() (svarūpa na)) ((aṇu ()) (svarūpa так)))"),
    ];

    for (historical, ukrainian, sanskrit) in cases {
        let historical_value = eval(historical);
        let ukrainian_value = eval(ukrainian);
        let sanskrit_value = eval(sanskrit);
        assert_eq!(historical_value, ukrainian_value);
        assert_eq!(historical_value, sanskrit_value);
    }
}

#[test]
fn ukrainian_canon_surface_is_reserved_but_ordinary_binding_is_lexical() {
    let mut session = Session::default();
    let error = eval_program("(def перше (lambda (x) (як-є затінено)))", &mut session)
        .expect_err("Contract 6.0 must reject shadowing a Ukrainian Canon spelling");
    assert_eq!(error.kind, ErrorKind::InvalidForm);

    let ordinary = eval_program(
        "(def локальна-функція (lambda (x y) (як-є локально))) (локальна-функція 1 2)",
        &mut session,
    )
    .expect("ordinary non-registry bindings must remain lexical values");
    assert_eq!(ordinary.value.to_string(), "локально");
}
