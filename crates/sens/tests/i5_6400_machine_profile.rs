use std::path::Path;

fn repo_root() -> std::path::PathBuf {
    Path::new(env!("CARGO_MANIFEST_DIR")).join("../..")
}

#[test]
fn i5_6400_human_profile_uses_full_ukr_peers_not_legacy_sid8_slots() {
    let root = repo_root();
    let profile_path = root.join("lib/machine/intel-core-i5-6400.lisp");
    let profile = std::fs::read_to_string(&profile_path).unwrap_or_else(|error| {
        panic!("missing i5-6400 Ukrainian profile at {profile_path:?}: {error}")
    });
    sens::parse(&profile).expect("i5-6400 profile must remain valid SENS data");
    assert!(profile.contains("Українська проєкція машинного профілю"));
    assert!(profile.contains("Цей файл НЕ є чинним джерелом семантичних повноважень."));
    assert!(profile.contains("lib/machine/profile/current-domain-x86-64.lisp"));

    // Ці 14 пар звірені за старою семантикою та поточною колонкою «укр»
    // відповідного D3/D4/D5/D6/D8/D9. Самі маршрути не є законами SENS.
    for (ukr, machine_path) in [
        ("атом?", "tag-test: TEST/AND/CMP"),
        ("тотожне?", "CMP/SETE"),
        ("сполучити", "allocate+STORE-pair"),
        ("перше", "LOAD-pair-head"),
        ("решта", "LOAD-pair-tail"),
        ("за-умовою", "TEST/CMP+Jcc"),
        ("частка", "IDIV-quotient"),
        ("однакові?", "CMP/SETE"),
        ("не-більше?", "CMP/SETLE"),
        ("не-менше?", "CMP/SETGE"),
        ("рядок?", "tag-test: string"),
        ("числовий-буфер?", "tag-test: numeric-buffer"),
        ("друге", "LOAD-tail+LOAD-head"),
        ("третє", "2xLOAD-tail+LOAD-head"),
    ] {
        let prefix = format!("({ukr} ");
        let row = profile.lines().map(str::trim_start)
            .find(|line| line.starts_with(&prefix))
            .unwrap_or_else(|| panic!("missing migrated «укр» machine row: {ukr}"));
        assert!(row.contains(machine_path),
            "unexpected mechanism for migrated {ukr}: {row}");
    }
    assert!(!profile.lines().any(|line| {
        let trimmed = line.trim_start();
        trimmed.starts_with('(')
            && trimmed.as_bytes().get(1..9)
                .is_some_and(|word| word.iter().all(|b| *b == b'0' || *b == b'1'))
            && trimmed.as_bytes().get(9).is_some_and(u8::is_ascii_whitespace)
    }), "historical SID8 machine row must not survive as a live profile key");
}

#[test]
fn current_i5_6400_profile_uses_width_safe_domain_keys_for_migrated_cpu_slice() {
    let current = include_str!("../../../lib/machine/profile/current-domain-x86-64.lisp");

    assert!(current.contains("(machine-domain-profile-3"));
    assert!(current.contains("(key-shape domain+ukr-resident)"));

    for (domain, resident, expected_machine_path) in [
        ("домен-п'ятий", "нуль?", "CMP+SETE+MOVZX"),
        ("домен-п'ятий", "додати", "ADD"),
        ("домен-п'ятий", "відняти", "SUB"),
        ("домен-п'ятий", "помножити", "IMUL"),
        ("домен-п'ятий", "частка", "CQO+IDIV"),
        ("домен-п'ятий", "менше?", "CMP+SETL"),
        ("домен-п'ятий", "більше?", "CMP+SETG"),
        ("домен-шостий", "додати-1", "ADD"),
        ("домен-шостий", "відняти-1", "SUB"),
        ("домен-третій", "тотожне?", "CMP/SETE"),
        ("домен-третій", "за-умовою", "CMP+Jcc"),
        ("домен-третій", "сполучити", "STORE-pair"),
        ("домен-третій", "перше", "LOAD-pair-head"),
        ("домен-третій", "решта", "LOAD-pair-tail"),
    ] {
        let row_prefix = format!("({domain} {resident} ");
        let row = current
            .lines()
            .map(str::trim_start)
            .find(|line| line.starts_with(&row_prefix))
            .unwrap_or_else(|| panic!("missing migrated «укр» machine row: {domain} {resident}"));
        assert!(
            row.contains(expected_machine_path),
            "unexpected mechanism for {domain} {resident}: {row}"
        );
    }

    assert!(!current.contains("(домен-четвертий додати "));
    assert!(!current.contains("(домен-п'ятий додати-1 "));
}

#[test]
fn generated_function_table_keeps_legacy_i5_projection_out_of_semantic_table() {
    let markdown = include_str!("../../../docs/generated/function-table.md");
    assert!(
        markdown.contains("Intel Core i5-6400 / Skylake"),
        "historical human function table may preserve the processor compatibility column"
    );

    let semantic_table = include_str!("../../../lib/generated/function-table.lisp");
    assert!(
        !semantic_table.contains("intel-core-i5-6400"),
        "processor-specific realization must not contaminate semantic machine-readable data"
    );
}

#[test]
fn function_table_generator_with_machine_projection_is_valid_lisp() {
    let source = include_str!("../../../scripts/generate-function-table.lisp");
    sens::parse(source).expect("function-table generator must remain valid sens source");
}
