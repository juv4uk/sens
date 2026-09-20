use my_lisp::semantic_registry_export::{
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
    for semantic_id in my_lisp::semantic_registry_export::admitted_semantic_ids() {
        for row in my_lisp::semantic_registry_export::admitted_surfaces_for_semantic_id(semantic_id)
        {
            if row.namespace == "укр" {
                admitted += 1;
                assert!(
                    !row.name.chars().any(|character| character.is_ascii_alphabetic()),
                    "admitted ukr spelling requires Latin layout: {}",
                    row.name
                );
            }
        }
    }
    assert!(admitted > 0, "registry must contain at least one admitted ukr spelling");
}

#[test]
fn full_ukr_names_preserve_action_protocol_and_representation_semantics() {
    let expected = [
        ("00001100", "додати"),
        ("00001101", "відняти"),
        ("01010100", "буфер-32-бітних-цілих-зі-знаком"),
        ("10100000", "розібрати-текст-формату-джейсон"),
        ("10100001", "обчислити-хеш-ша-256-тексту-у-шістнадцятковому-записі"),
        ("10100011", "прочитати-текст-з-з'єднання-протоколу-керування-передаванням"),
        ("10100100", "записати-текст-у-з'єднання-протоколу-керування-передаванням"),
        ("10100101", "слухати-порт-протоколу-керування-передаванням"),
    ];

    for (semantic_id, name) in expected {
        let id = u8::from_str_radix(semantic_id, 2).expect("binary SID");
        assert!(
            my_lisp::semantic_registry_export::admitted_surfaces_for_semantic_id(id)
                .iter()
                .any(|row| row.namespace == "укр" && row.name == name),
            "semantic SID {semantic_id} must keep the explicit ukr meaning {name:?}"
        );
    }

    for rejected in [
        "плюс",
        "мінус",
        "буфер-32-бітних-цілих",
        "розібрати-джейсон",
        "геш-ша-256-у-шістнадцятковий-текст",
        "прочитати-з-мережевого-з'єднання",
        "записати-у-мережеве-з'єднання",
        "слухати-мережеві-з'єднання",
    ] {
        assert!(
            my_lisp::semantic_registry_export::semantic_id_for_admitted_surface(rejected).is_none(),
            "lossy or rejected ukr wording must not return: {rejected}"
        );
    }
}
