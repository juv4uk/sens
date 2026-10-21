use sens::domain_projection_catalog::{lookup, ProjectionSource, ProjectionValue};
use sens::{d7_keyboard, render_text7, Text7, Text7Layout};

#[test]
fn generated_inventory_covers_the_current_source_tables() {
    // The general current-domain catalog contains only D1–D10 Lisp tables.
    // D11+ stays future; D7 text modes are served by the current codec.
    assert_eq!(sens::domain_projection_catalog::entry_count(), 12_276);
}

#[test]
fn source_namespaces_keep_exact_values_and_do_not_merge_d7_san_columns() {
    assert_eq!(
        lookup(ProjectionSource::DomainTable, 1, "0", "ук"),
        Some(ProjectionValue::Symbol("ні")),
    );
    assert_eq!(
        lookup(ProjectionSource::DomainTable, 7, "1000001", "san"),
        Some(ProjectionValue::Symbol("o")),
    );
    assert_eq!(
        lookup(ProjectionSource::D7KeyboardV2, 7, "1000001", "san"),
        Some(ProjectionValue::Character(d7_keyboard::SAN[0b1000001])),
    );
    assert_eq!(
        lookup(ProjectionSource::DomainTable, 7, "0000000", "ук"),
        Some(ProjectionValue::EmptyList),
    );
    assert_eq!(
        lookup(ProjectionSource::D7KeyboardV2, 7, "0000000", "uk"),
        Some(ProjectionValue::Character(d7_keyboard::UK[0])),
    );
}

#[test]
fn unknown_or_inexact_coordinates_fail_closed() {
    assert_eq!(lookup(ProjectionSource::DomainTable, 1, "00", "ук"), None);
    assert_eq!(
        lookup(ProjectionSource::DomainTable, 12, "000000000000", "ук"),
        None
    );
    assert_eq!(
        lookup(ProjectionSource::DomainTable, 10, "0000000000", "missing"),
        None
    );
    assert_eq!(
        lookup(ProjectionSource::DomainTable, 10, "000000000x", "ук"),
        None
    );
    assert_eq!(
        lookup(ProjectionSource::DomainTable, 11, "00000000000", "ук"),
        None,
        "future D11 must not enter the current runtime catalog",
    );
}

#[test]
fn future_d11_is_not_part_of_the_current_projection_catalog() {
    assert_eq!(
        lookup(ProjectionSource::DomainTable, 11, "00000000000", "ук"),
        None,
    );
}

#[test]
fn every_d7_keyboard_v2_cell_uses_the_native_projection_tables() {
    for code in 0_u8..=127 {
        let bits = format!("{code:07b}");
        assert_eq!(
            lookup(ProjectionSource::D7KeyboardV2, 7, &bits, "ascii"),
            Some(ProjectionValue::Character(char::from(code))),
        );
        assert_eq!(
            lookup(ProjectionSource::D7KeyboardV2, 7, &bits, "uk"),
            Some(ProjectionValue::Character(
                d7_keyboard::UK[usize::from(code)]
            )),
        );
        assert_eq!(
            lookup(ProjectionSource::D7KeyboardV2, 7, &bits, "san"),
            Some(ProjectionValue::Character(
                d7_keyboard::SAN[usize::from(code)]
            )),
        );
        let datum = Text7::from_cells(vec![code]).unwrap();
        let iast = render_text7(&datum, Text7Layout::SaIast).unwrap();
        assert_eq!(
            lookup(ProjectionSource::D7KeyboardV2, 7, &bits, "iast").map(|value| match value {
                ProjectionValue::Text(value) => value,
                _ => panic!("IAST projection must remain text"),
            }),
            Some(iast.as_str()),
        );
    }
}
