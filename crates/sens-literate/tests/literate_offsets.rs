use sens::Session;
use sens_literate::SourceMode;

#[test]
fn test_literate_offsets() {
    let source = r#"
# Український SENS

Це виконуваний документ.

```sens
(визначити крок (функція (лічильник)
  (додати лічильник 1)))
```

Між блоками є звичайний текст.

```sens
(крок 41)
```
"#;

    let mut session = Session::default();
    let result = sens_literate::eval_literate_ukr(source, SourceMode::Literate, &mut session)
        .expect("should evaluate successfully");

    assert_eq!(result.0.value.to_string(), "42");
}

#[test]
fn test_fallback_no_markdown() {
    let source = "(додати 10 20)";
    let mut session = Session::default();
    let result = sens_literate::eval_literate_ukr(source, SourceMode::PureLisp, &mut session)
        .expect("should evaluate fallback");
    assert_eq!(result.0.value.to_string(), "30");
}

#[test]
fn test_error_offsets_remapped() {
    let source = r#"
# Помилка у блоці SENS

```sens
(додати 1 2)
```

Далі навмисно невідома функція:

```sens
(невідома-функція 42)
```
"#;

    let mut session = Session::default();
    let error = sens_literate::eval_literate_ukr(source, SourceMode::Literate, &mut session)
        .expect_err("should fail on unknown symbol");

    // Check if the span matches the original source
    let error_text = &source[error.span.start..error.span.end];
    assert_eq!(error_text, "невідома-функція");
}
#[test]
fn test_literate_evaluation() {
    let source = "# Український SENS\n\nЦе виконувана програма.\n\n```sens\n(визначити значення 10)\n(помножити значення 2)\n```\n\nТекст поза блоком ігнорується.";
    let mut session = Session::default();
    let (res, _) =
        sens_literate::eval_literate_ukr(source, SourceMode::Literate, &mut session).unwrap();
    assert_eq!(res.value.to_string(), "20");
}
