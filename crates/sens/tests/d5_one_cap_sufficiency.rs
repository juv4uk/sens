use sens::{eval_program, ErrorKind, Session};

fn eval(source: &str) -> Result<String, sens::LanguageError> {
    let mut session = Session::default();
    eval_program(source, &mut session).map(|result| result.value.to_string())
}

#[test]
fn d5_one_cap_w1_transformer_preserves_unused_raw_operand() {
    let value = eval(
        r#"
        (define first-transformer
          (make-macro
            (lambda (a b) a)))
        (first-transformer (quote ok) never-defined)
        "#,
    )
    .expect("transformer surrogate must preserve unused raw operand");

    assert_eq!(value, "ok");
}

#[test]
fn d5_one_cap_w2_nested_transformer_expands_without_macroexpand_identity() {
    let value = eval(
        r#"
        (define inner-transformer
          (make-macro
            (lambda (x) x)))

        (define outer-transformer
          (make-macro
            (lambda (x)
              (cons
                (quote inner-transformer)
                (cons x (quote ()))))))

        (outer-transformer (quote ok))
        "#,
    )
    .expect("outer transformer should expand to an inner transformer call");

    assert_eq!(value, "ok");
}

#[test]
fn d5_one_cap_w3_expansion_runs_in_callers_lexical_environment() {
    let value = eval(
        r#"
        (define emit-local-x
          (make-macro
            (lambda () (quote local-x))))

        ((lambda (local-x)
           (emit-local-x))
         42)
        "#,
    )
    .expect("expanded symbol must resolve in caller lexical environment");

    assert_eq!(value, "42");
}

#[test]
fn d5_one_cap_w4_ordinary_lambda_remains_eager() {
    let error = eval(
        r#"
        (define ordinary-first
          (lambda (a b) a))
        (ordinary-first (quote ok) never-defined)
        "#,
    )
    .expect_err("ordinary lambda must evaluate the unused second operand eagerly");

    assert_eq!(error.kind, ErrorKind::UnknownSymbol);
    assert!(error.message.contains("never-defined"));
}

#[test]
fn d5_one_cap_w5_canonical_ukrainian_macro_executes_with_raw_operands() {
    let value = eval(
        r#"
        (визначити випробування
          (макрос (функція (перший другий) перший)))
        (випробування (як-є гаразд) невідоме-ім'я)
        "#,
    )
    .expect("D5 макрос має розгортати перший аргумент без обчислення другого");

    assert_eq!(value, "гаразд");
}

#[test]
fn d5_one_cap_w6_derived_ukrainian_macro_uses_define_and_lambda() {
    let value = eval(
        r#"
        (визначити-макрос обрати-перший (лівий правий) лівий)
        (обрати-перший (як-є готово) невідоме-ім'я)
        "#,
    )
    .expect("мовне визначення макроса використовує D4 та ратифікований D5");

    assert_eq!(value, "готово");
}
