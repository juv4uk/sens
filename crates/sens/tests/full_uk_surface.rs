use sens::semantic_registry_export::{
    admitted_surfaces_for_semantic_id, semantic_id_for_admitted_surface,
};

const CURRENT_UK_STRING_EMPTY: &str = "текст-порожній?";
const UKR_STRING_EMPTY: &str = "порожній-текст?";

#[test]
fn ratified_ukr_name_resolves_to_same_identity_as_current_uk() {
    let string_empty_id = semantic_id_for_admitted_surface(CURRENT_UK_STRING_EMPTY)
        .expect("existing stable uk spelling must remain admitted");
    assert_eq!(
        semantic_id_for_admitted_surface(CURRENT_UK_STRING_EMPTY),
        Some(string_empty_id),
        "existing stable uk spelling must remain admitted"
    );
    assert_eq!(
        semantic_id_for_admitted_surface(UKR_STRING_EMPTY),
        Some(string_empty_id),
        "ratified ukr spelling must resolve to the same semantic identity"
    );

    let surfaces = admitted_surfaces_for_semantic_id(string_empty_id);
    assert!(
        surfaces
            .iter()
            .any(|row| row.namespace == "ук" && row.name == CURRENT_UK_STRING_EMPTY),
        "current uk surface must remain present"
    );
    assert!(
        surfaces
            .iter()
            .any(|row| row.namespace == "укр" && row.name == UKR_STRING_EMPTY),
        "ukr must be the authoritative full Ukrainian peer namespace"
    );
    assert!(
        surfaces.iter().all(|row| row.namespace != "full-uk"),
        "full-uk is not a separate namespace; ukr is the full Ukrainian surface"
    );
}

#[test]
fn admitted_ukr_registry_spellings_never_require_latin_layout() {
    let mut admitted = 0usize;
    for semantic_id in sens::semantic_registry_export::admitted_semantic_ids() {
        for row in sens::semantic_registry_export::admitted_surfaces_for_semantic_id(semantic_id) {
            if row.namespace == "укр" {
                admitted += 1;
                assert!(
                    !row.name
                        .chars()
                        .any(|character| character.is_ascii_alphabetic()),
                    "admitted ukr spelling requires Latin layout: {}",
                    row.name
                );
            }
        }
    }
    assert!(
        admitted > 0,
        "registry must contain at least one admitted ukr spelling"
    );
}

#[test]
fn українські_арифметичні_назви_мають_точні_ратифіковані_d5_адреси() {
    // Старі W8 коди 00001100 / 00001101 не є D5:01010 / D5:01011.
    // Беремо саме чинну українську проєкцію, а не legacy u8 слот.
    for (name, bits) in [
        ("додати", 0b01010),
        ("відняти", 0b01011),
        ("помножити", 0b10110),
        ("частка", 0b10111),
    ] {
        let identity = sens::semantic_registry_export::admitted_core_domain_for_surface(name)
            .unwrap_or_else(|| panic!("не знайдено ратифікованої D5 поверхні {name}"));
        assert_eq!(
            (identity.width(), identity.packed_bits()),
            (5, bits),
            "українська голова {name} втратила D5 або її точні біти",
        );
        let source = format!("({name} #d24:000000000000000000000110 #d24:000000000000000000000010)");
        let lowered = sens::lower_program(&sens::parse(&source).expect("SENS reader"));
        assert!(matches!(
            &lowered[0].kind,
            sens::ExprKind::DomainCall(call, _)
                if (call.width(), call.packed_bits()) == (5, bits)
        ), "{name}: реальний lowering мусить зберігати точну D5 адресу");
    }

    // Відкинуті людинописні синоніми не отримують нової identity.
    for rejected in ["плюс", "мінус", "розібрати-джейсон"] {
        assert!(
            sens::semantic_registry_export::admitted_core_domain_for_surface(rejected).is_none(),
            "нератифіковане ім'я не може стати машинним законом: {rejected}"
        );
    }
}

#[test]
fn generated_function_table_uses_uk_then_ukr_without_duplicate_full_uk_column() {
    let table = include_str!("../../../lib/generated/function-table.lisp");
    let row = table
        .lines()
        .find(|line| line.trim_start().starts_with("(00111100 "))
        .expect("generated function table must contain byte SID 00111100");

    let uk = row
        .find("(ук текст-порожній?)")
        .expect("row must contain current uk column");
    let ukr = row
        .find("(укр порожній-текст?)")
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
        markdown.contains(
            "| ID | ук | укр | English | Sanskrit | Symbol | Intel Core i5-6400 / Skylake |"
        ),
        "human function table must expose exactly uk and ukr Ukrainian columns"
    );
    assert!(
        markdown.contains(
            "| `00111100` | текст-порожній? | порожній-текст? | string-empty? | śūnya? | () | () |"
        ),
        "human row must show uk followed by full Ukrainian ukr"
    );
    assert!(
        !markdown.contains("Повна українська"),
        "human table must not duplicate ukr under a second full-Ukrainian column"
    );
}
