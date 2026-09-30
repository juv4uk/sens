use sens::{eval_program, load_core_library, ErrorKind, Session, Value};

#[test]
fn string_order_is_exact_predicatebit_after_strict_cond_migration() {
    let mut session = Session::default();
    load_core_library(&mut session).expect("strict Core4 must load");

    for (source, expected) in [
        ("(00100101 \"\" \"\")", false),
        ("(00100101 \"\" \"a\")", true),
        ("(00100101 \"a\" \"\")", false),
        ("(00100101 \"a\" \"b\")", true),
        ("(00100101 \"b\" \"a\")", false),
        ("(00100101 \"aa\" \"ab\")", true),
        ("(00100101 \"ab\" \"aa\")", false),
        ("(00100101 \"a\" \"a\")", false),
        ("(00100101 \"ю\" \"я\")", true),
    ] {
        let value = eval_program(source, &mut session)
            .unwrap_or_else(|error| panic!("{source}: {error}"))
            .value;
        assert_eq!(value, Value::predicate_bit(expected), "{source}");
    }

    let error = eval_program("(00100101 #b1 \"a\")", &mut session)
        .expect_err("string<? must fail closed on a non-string operand");
    assert_eq!(error.kind, ErrorKind::Type);
}
