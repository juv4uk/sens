use sens::{ErrorKind, LanguageError, Span};

#[test]
fn renderer_handles_span_ending_inside_ukrainian_utf8_character() {
    let source = "(додай-крок)";
    let error = LanguageError::new(
        ErrorKind::UnknownSymbol,
        "невідоме ім'я",
        Span { start: 0, end: 13 },
    );

    let rendered = error.render(source);

    assert!(rendered.contains("невідоме ім'я"));
    assert!(rendered.contains(source));
    assert!(rendered.contains("1:1"));
}
