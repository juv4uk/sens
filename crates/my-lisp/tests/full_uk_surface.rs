use my_lisp::semantic_registry_export::{
    admitted_surfaces_for_semantic_id, semantic_id_for_admitted_surface,
};

const STRING_EMPTY_ID: u8 = 60;
const CURRENT_UK_STRING_EMPTY: &str = "текст-порожній?";
const UKR_STRING_EMPTY: &str = "порожній-текст?";

#[test]
fn ratified_ukr_name_resolves_to_same_identity_as_current_uk() {
    assert_eq!(
        semantic_id_for_admitted_surface(CURRENT_UK_STRING_EMPTY),
        Some(STRING_EMPTY_ID),
        "existing stable uk spelling must remain admitted"
    );
    assert_eq!(
        semantic_id_for_admitted_surface(UKR_STRING_EMPTY),
        Some(STRING_EMPTY_ID),
        "ratified ukr spelling must resolve to the same semantic identity"
    );

    let surfaces = admitted_surfaces_for_semantic_id(STRING_EMPTY_ID);
    assert!(
        surfaces
            .iter()
            .any(|row| row.namespace == "uk" && row.name == CURRENT_UK_STRING_EMPTY),
        "current uk surface must remain present"
    );
    assert!(
        surfaces
            .iter()
            .any(|row| row.namespace == "ukr" && row.name == UKR_STRING_EMPTY),
        "ukr must be the authoritative full Ukrainian peer namespace"
    );
    assert!(
        surfaces.iter().all(|row| row.namespace != "full-uk"),
        "full-uk is not a separate namespace; ukr is the full Ukrainian surface"
    );
}

#[test]
fn admitted_ukr_registry_spellings_never_require_latin_layout() {
    let source = include_str!("../../../lib/surface/semantic-registry.lisp");
    let mut admitted = 0usize;

    assert!(
        !source.contains("(full-uk "),
        "registry must use ukr, not a duplicate full-uk namespace"
    );

    for line in source.lines() {
        let mut rest = line;
        while let Some(offset) = rest.find("(ukr ") {
            rest = &rest[offset + "(ukr ".len()..];
            let Some(end) = rest.find(')') else {
                panic!("unterminated ukr surface entry: {line}");
            };
            let fields = rest[..end].split_whitespace().collect::<Vec<_>>();
            assert_eq!(
                fields.len(),
                1,
                "ukr surface entry must be (ukr spelling) or (ukr ()): {line}"
            );
            let name = fields[0];
            if name != "()" {
                admitted += 1;
                assert!(
                    !name.chars().any(|character| character.is_ascii_alphabetic()),
                    "admitted ukr spelling requires Latin layout: {name}"
                );
            }
            rest = &rest[end + 1..];
        }
    }

    assert!(
        admitted > 0,
        "registry must contain at least one admitted ukr spelling"
    );
}

#[test]
fn full_ukr_names_preserve_action_protocol_and_representation_semantics() {
    let source = include_str!("../../../lib/surface/semantic-registry.lisp");
    let expected = [
        ("00001100", "(ukr додати)"),
        ("00001101", "(ukr відняти)"),
        ("01010100", "(ukr буфер-32-бітних-цілих-зі-знаком)"),
        ("10100000", "(ukr розібрати-текст-формату-джейсон)"),
        (
            "10100001",
            "(ukr обчислити-хеш-ша-256-тексту-у-шістнадцятковому-записі)",
        ),
        (
            "10100011",
            "(ukr прочитати-текст-з-з'єднання-протоколу-керування-передаванням)",
        ),
        (
            "10100100",
            "(ukr записати-текст-у-з'єднання-протоколу-керування-передаванням)",
        ),
        (
            "10100101",
            "(ukr слухати-порт-протоколу-керування-передаванням)",
        ),
    ];

    for (semantic_id, expected_surface) in expected {
        let prefix = format!("(\"{semantic_id}\" ");
        let row = source
            .lines()
            .map(str::trim_start)
            .find(|line| line.starts_with(&prefix))
            .unwrap_or_else(|| panic!("semantic registry is missing ID {semantic_id}"));
        assert!(
            row.contains(expected_surface),
            "byte SID {semantic_id} must keep the explicit ukr meaning {expected_surface:?}; row: {row}"
        );
    }

    for rejected in [
        "(ukr плюс)",
        "(ukr мінус)",
        "(ukr буфер-32-бітних-цілих)",
        "(ukr розібрати-джейсон)",
        "(ukr геш-ша-256-у-шістнадцятковий-текст)",
        "(ukr прочитати-з-мережевого-з'єднання)",
        "(ukr записати-у-мережеве-з'єднання)",
        "(ukr слухати-мережеві-з'єднання)",
    ] {
        assert!(
            !source.contains(rejected),
            "lossy or rejected ukr wording must not return: {rejected}"
        );
    }
}

#[test]
fn generated_function_table_uses_uk_then_ukr_without_duplicate_full_uk_column() {
    let table = include_str!("../../../lib/generated/function-table.lisp");
    let row = table
        .lines()
        .find(|line| line.trim_start().starts_with("(\"00111100\" "))
        .expect("generated function table must contain byte SID 00111100");

    let uk = row
        .find("(uk текст-порожній?)")
        .expect("row must contain current uk column");
    let ukr = row
        .find("(ukr порожній-текст?)")
        .expect("row must contain authoritative full Ukrainian ukr column");
    let en = row
        .find("(en string-empty?)")
        .expect("row must contain English column");

    assert!(
        uk < ukr && ukr < en,
        "generated machine table column order must be uk -> ukr -> en: {row}"
    );
    assert!(
        !row.contains("(full-uk "),
        "generated machine table must not duplicate ukr as full-uk: {row}"
    );

    let markdown = include_str!("../../../docs/generated/function-table.md");
    assert!(
        markdown.contains("| ID | uk | ukr | English | Sanskrit | Symbol | Intel Core i5-6400 / Skylake |"),
        "human function table must expose exactly uk and ukr Ukrainian columns"
    );
    assert!(
        markdown.contains("| `00111100` | текст-порожній? | порожній-текст? | string-empty? | śūnya? | () | () |"),
        "human row must show uk followed by full Ukrainian ukr"
    );
    assert!(
        !markdown.contains("Повна українська"),
        "human table must not duplicate ukr under a second full-Ukrainian column"
    );
}
