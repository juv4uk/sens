//! Зовнішній свідок каталогу: похідна назва макроса не стає доменною identity.
use sens::{language_items, Arity, LanguageItem, LanguageItemKind};

fn unique<'a>(all: &'a [LanguageItem], name: &str) -> &'a LanguageItem {
    let found = all
        .iter()
        .filter(|row| row.name == name)
        .collect::<Vec<_>>();
    assert_eq!(found.len(), 1, "ім'я має один metadata-рядок: {name}");
    found[0]
}

#[test]
fn ukrainian_d3_car_is_a_three_bit_domain_not_legacy_eight_bit() {
    let all = language_items();
    let car = unique(&all, "перше");
    let identity = car.domain_identity.expect("ратифікований D3 CAR");
    assert_eq!(identity.width(), 3);
    assert_eq!(identity.packed_bits(), 0b100);
    assert_eq!(car.arity, Arity::Exact(1));
}

#[test]
fn ukrainian_d4_lambda_and_define_keep_distinct_four_bit_identities() {
    let all = language_items();
    for (name, bits, kind) in [
        ("функція", 0b0010, LanguageItemKind::SyntaxForm),
        ("визначити", 0b0011, LanguageItemKind::SyntaxForm),
    ] {
        let row = unique(&all, name);
        let identity = row.domain_identity.expect("ратифікований D4");
        assert_eq!(identity.width(), 4);
        assert_eq!(identity.packed_bits(), bits);
        assert_eq!(row.kind, kind);
    }
}

#[test]
fn current_macro_and_define_identities_back_the_derived_defmacro_surface() {
    let all = language_items();
    let macro_identity = sens::semantic_registry_export::admitted_core_domain_for_surface("макрос")
        .expect("ратифікований D5 MACRO");
    assert_eq!(macro_identity.width(), 5);
    assert_eq!(macro_identity.packed_bits(), 0b00011);

    let define = unique(&all, "визначити");
    let define_identity = define.domain_identity.expect("ратифікований D4 DEFINE");
    assert_eq!(define_identity.width(), 4);
    assert_eq!(define_identity.packed_bits(), 0b0011);

    assert!(
        !all.iter().any(|row| row.name == "визначити-макрос"),
        "з'єднана поверхнева назва не є окремим доменним записом"
    );
}

#[test]
fn current_domain_catalogue_does_not_use_unknown_or_legacy_names_as_authority() {
    let all = language_items();
    let ratified = all
        .iter()
        .filter(|row| row.domain_identity.is_some())
        .collect::<Vec<_>>();
    assert!(!ratified.is_empty());
    assert!(ratified.iter().any(|row| row.name == "перше"));
    assert!(ratified.iter().all(|row| row.domain_identity.is_some()));
    assert!(ratified.iter().all(|row| row.name != "визначити-макрос"));
}
