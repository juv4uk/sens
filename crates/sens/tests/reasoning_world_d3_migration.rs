//! Перевірка джерельної межі незмінного світу після українського переходу.
//! Поведінку та точну арність перевіряє сам СЕНС у
//! tests/semantic/world-exact-arity-witness.lisp; Rust перевіряє межі джерела.

use sens::{parse_mixed_exact_domain_reasoning_source, ErrorKind, Expr, ExprKind};

const BEFORE: &str = include_str!("../../../tests/fixtures/world-d3-before.lisp");
const WORLD: &str = include_str!("../../../lib/world.lisp");
const D3: &str = include_str!("../../../lib/domains/d3.lisp");
const D4: &str = include_str!("../../../lib/domains/d4.lisp");

#[test]
fn ukrainian_world_preserves_quoted_protocol_without_old_w8_calls() {
    // Історичний W8 був вилучений: вимагати його в оновленому before —
    // хибна перевірка, а не доказ міграції.
    assert!(BEFORE.contains("(визначити д3-створити-світ"));
    assert!(BEFORE.contains("(визначити д3-свідок-світу-до"));
    assert!(!BEFORE.contains("(визначити make-world"));
    assert!(!BEFORE.contains("(00000111"));

    assert!(WORLD.contains("(визначити створити-світ"));
    assert!(WORLD.contains("(визначити світ?"));
    assert!(!WORLD.contains("(визначити world?"));
    assert!(!WORLD.contains("(00000111"));

    // Цитований символ world та теги подій — дані, їх не перекладаємо.
    for tag in ["(як-є world)", "(як-є tell)", "(як-є retract)"] {
        assert!(BEFORE.contains(tag), "у свідку втрачено дані {tag}");
        assert!(WORLD.contains(tag), "у бібліотеці втрачено дані {tag}");
    }
    assert_eq!(
        parse_mixed_exact_domain_reasoning_source("lib/not-world.lisp", WORLD)
            .expect_err("сторонній шлях має відхилятися")
            .kind,
        ErrorKind::Parse
    );
}

#[test]
fn world_shape_uses_ukrainian_d3_d4_law_and_checks_exact_arity() {
    let forms = parse_mixed_exact_domain_reasoning_source("lib/world.lisp", WORLD)
        .expect("чинне джерело світу має розбиратися");
    let definition = forms.iter().find(|form| {
        let ExprKind::List(items) = &form.kind else {
            return false;
        };
        matches!(
            items.get(1),
            Some(Expr { kind: ExprKind::Symbol(name), .. }) if name.as_ref() == "світ?"
        )
    });
    assert!(
        definition.is_some(),
        "у світі відсутнє українське визначення світ?"
    );

    // Точні координати беруться лише з ратифікованої драбини;
    // застарілі голі восьмибітні виклики не підміняють D3/D4.
    for row in [
        "(001 (ук як-є)",
        "(010 (ук атом?)",
        "(011 (ук решта)",
        "(101 (ук тотожне?)",
        "(110 (ук за-умовою)",
    ] {
        assert!(D3.contains(row), "відсутній закон третього домену: {row}");
    }
    assert!(D4.contains("(0101 (ук порожнє?)"));

    // Відкидаємо кожну коротку форму та зайве п'яте поле,
    // а не вгадуємо валідність структури за host truthiness.
    for clause in [
        "(атом? (решта значення))",
        "(атом? (решта (решта значення)))",
        "(атом? (решта (решта (решта значення))))",
        "(порожній? (решта (решта (решта (решта значення)))))",
    ] {
        assert!(WORLD.contains(clause), "зникла перевірка арності: {clause}");
    }
}
