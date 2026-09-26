use sens::{Exactness, Value};
use sens_literate::SourceMode;

#[test]
fn test_literate_offsets() {
    let source = r#"
# Literate Test

This is a test document.

```sens
(def foo (lambda (x)
  (+ x 1)))
```

Some more text.

```sens
(foo 41)
```
"#;

    let mut session = sens::Session::default();
    let result = sens_literate::eval_literate(source, SourceMode::Literate, &mut session)
        .expect("should evaluate successfully");

    assert_eq!(result.0.value, Value::Number(42.0, Exactness::Exact));
}

#[test]
fn test_fallback_no_markdown() {
    let source = "(+ 10 20)";
    let mut session = sens::Session::default();
    let result = sens_literate::eval_literate(source, SourceMode::PureLisp, &mut session)
        .expect("should evaluate fallback");
    assert_eq!(result.0.value, Value::Number(30.0, Exactness::Exact));
}

#[test]
fn test_error_offsets_remapped() {
    let source = r#"
# Error Test

```sens
(+ 1 2)
```

Now an error:

```sens
(foo-bar 42)
```
"#;

    let mut session = sens::Session::default();
    let error = sens_literate::eval_literate(source, SourceMode::Literate, &mut session)
        .expect_err("should fail on unknown symbol");

    // Check if the span matches the original source
    let error_text = &source[error.span.start..error.span.end];
    assert_eq!(error_text, "foo-bar");
}
#[test]
fn test_literate_evaluation() {
    let source = "# Literate Lisp\n\nThis is a literate program.\n\n```sens\n(def x 10)\n(* x 2)\n```\n\nIt ignores non-code blocks.";
    let mut session = sens::Session::default();
    let (res, _) =
        sens_literate::eval_literate(source, SourceMode::Literate, &mut session).unwrap();
    assert_eq!(res.value.to_string(), "20");
}
