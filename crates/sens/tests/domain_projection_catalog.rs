use sens::domain_projection_catalog::{lookup, ProjectionSource, ProjectionValue};

#[test]
fn generated_inventory_covers_the_current_source_tables() {
    // D1–D10 are full tables, D11 has its ratified 43-row test vocabulary;
    // separate JSON namespaces contain D7 keyboard-v2 and D11 authority.
    assert_eq!(sens::domain_projection_catalog::entry_count(), 13_347);
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
        Some(ProjectionValue::Text("ओ")),
    );
    assert_eq!(
        lookup(ProjectionSource::DomainTable, 7, "0000000", "ук"),
        Some(ProjectionValue::EmptyList),
    );
    assert_eq!(
        lookup(ProjectionSource::D7KeyboardV2, 7, "0000000", "uk"),
        Some(ProjectionValue::Text("\0")),
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
        lookup(ProjectionSource::DomainTable, 11, "00000000000", "missing"),
        None
    );
    assert_eq!(
        lookup(ProjectionSource::DomainTable, 11, "0000000000x", "ук"),
        None
    );
}

#[test]
fn every_ratified_d11_projection_matches_its_json_authority() {
    let authority: serde_json::Value = serde_json::from_str(include_str!(
        "../../../knowledge/d11-testing-vocabulary-ratified.json"
    ))
    .expect("D11 ratified authority JSON parses");
    assert_eq!(authority["schema"], "sens.d11.testing/v1");
    assert_eq!(authority["status"], "owner-ratified");
    assert_eq!(authority["width"], 11);
    assert_eq!(authority["occupancy"], 43);
    assert_eq!(
        authority["semantic_scope"],
        "Testing vocabulary for binary SENS semantic tests; not callable Core"
    );

    let rows = authority["table"].as_array().expect("D11 table array");
    assert_eq!(rows.len(), 43);
    let mut seen = std::collections::BTreeSet::new();
    for row in rows {
        let bits = row["bits"].as_str().expect("exact D11 bits");
        assert_eq!(bits.len(), 11, "D11 coordinate width: {bits}");
        assert!(bits.bytes().all(|byte| matches!(byte, b'0' | b'1')));
        assert!(seen.insert(bits), "duplicate D11 coordinate {bits}");
        for (json_column, table_column) in [("uk", "ук"), ("ukr", "укр"), ("sym", "sym")] {
            let expected = row[json_column].as_str().expect("D11 projection string");
            let actual = lookup(ProjectionSource::DomainTable, 11, bits, table_column)
                .expect("D11 table projection exists");
            let actual = match actual {
                ProjectionValue::Symbol(value) | ProjectionValue::Text(value) => value,
                ProjectionValue::EmptyList => "",
            };
            assert_eq!(actual, expected, "D11:{bits} projection {table_column}");
        }
    }
    assert_eq!(seen.len(), 43);
}

#[test]
fn every_d7_keyboard_v2_cell_is_available_without_collapsing_columns() {
    let authority: serde_json::Value = serde_json::from_str(include_str!(
        "../../../knowledge/d7-keyboard-v2-ratified.json"
    ))
    .expect("D7 keyboard-v2 authority JSON parses");
    assert_eq!(authority["schema"], "sens.d7.keyboard/v2");
    assert_eq!(authority["status"], "owner-ratified");
    assert_eq!(authority["width"], 7);
    let rows = authority["table"].as_array().expect("D7 table array");
    assert_eq!(rows.len(), 128);
    for row in rows {
        let bits = row["bits"].as_str().expect("exact D7 bits");
        assert_eq!(bits.len(), 7);
        for column in ["ascii", "uk", "san", "iast"] {
            let expected = row[column].as_str().expect("D7 projection string");
            let actual = lookup(ProjectionSource::D7KeyboardV2, 7, bits, column)
                .expect("D7 JSON projection exists");
            assert_eq!(
                match actual {
                    ProjectionValue::Text(value) | ProjectionValue::Symbol(value) => value,
                    ProjectionValue::EmptyList => "()",
                },
                expected,
                "D7 keyboard-v2:{bits} column={column}",
            );
        }
    }
}
