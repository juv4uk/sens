use sens::{eval_program, Session};

const SOURCE: &str =
    include_str!("../../../fixtures/emrg/v1/medical-assistance-request-v1.source.lisp");
const WIRE: &str =
    include_str!("../../../fixtures/emrg/v1/medical-assistance-request-v1.wire");
const SURFACES: &str =
    include_str!("../../../fixtures/emrg/v1/medical-assistance-request-v1.surfaces.tsv");

const EXPECTED_WIRE_HEX: &str =
    "282371323a312f31202371323a31312f312022612d30303031222022323032362d31302d30345430303a30303a30305a22202371323a302f31202371323a312f3120282371323a302f312920282371323a302f312929";

fn eval(source: &str) -> String {
    let mut session = Session::default();
    eval_program(source, &mut session)
        .expect("EMRG medical-assistance fixture expression should evaluate")
        .value
        .to_string()
}

fn hex(bytes: &[u8]) -> String {
    const DIGITS: &[u8; 16] = b"0123456789abcdef";
    let mut out = String::with_capacity(bytes.len() * 2);
    for byte in bytes {
        out.push(DIGITS[(byte >> 4) as usize] as char);
        out.push(DIGITS[(byte & 0x0f) as usize] as char);
    }
    out
}

#[test]
fn medical_assistance_request_v1_has_runtime_verified_canonical_wire() {
    let program = format!("(write-to-string (quote {SOURCE}))");
    assert_eq!(eval(&program), format!("{WIRE:?}"));

    let round_trip =
        format!("(write-to-string (read (write-to-string (quote {SOURCE}))))");
    assert_eq!(eval(&round_trip), format!("{WIRE:?}"));
}

#[test]
fn medical_assistance_request_v1_records_exact_consumer_payload_size() {
    assert_eq!(WIRE.as_bytes().len(), 86);
    assert_eq!(WIRE.as_bytes().len() * 8, 688);
    assert_eq!(hex(WIRE.as_bytes()), EXPECTED_WIRE_HEX);
}

#[test]
fn medical_assistance_request_v1_projection_coordinates_are_language_neutral() {
    let mut lines = SURFACES.lines();
    assert_eq!(lines.next(), Some("p\tuk\tpl\ten"));

    for line in lines {
        let coordinate = line
            .split('\t')
            .next()
            .expect("surface row must begin with a projection coordinate");
        assert!(!coordinate.is_empty());
        assert!(
            coordinate
                .bytes()
                .all(|byte| byte.is_ascii_digit() || byte == b'/'),
            "projection identity must be positional/numeric, got: {coordinate}"
        );
    }
}

#[test]
fn medical_assistance_request_v1_human_labels_are_projection_only() {
    for required in [
        "Запит медичної допомоги",
        "Prośba o pomoc medyczną",
        "Medical assistance request",
        "Медична допомога",
        "Pomoc medyczna",
        "Medical assistance",
        "Невідомо",
        "Nieznana",
        "Unknown",
        "Відсутня",
        "Brak",
        "Absent",
    ] {
        assert!(SURFACES.contains(required));
        assert!(!WIRE.contains(required));
    }
}

#[test]
fn assistance_person_count_unknown_and_absent_are_structurally_separate() {
    let rows: Vec<Vec<&str>> = SURFACES
        .lines()
        .skip(1)
        .map(|line| line.split('\t').collect())
        .collect();

    for required in ["4/0", "5", "6/0", "7/0"] {
        assert!(
            rows.iter().any(|row| row.first() == Some(&required)),
            "required projection coordinate missing: {required}"
        );
    }

    let source_fields: Vec<&str> = SOURCE
        .trim_matches(['(', ')'])
        .split_whitespace()
        .collect();
    assert_eq!(source_fields[4], "0", "slot 4 assistance category");
    assert_eq!(source_fields[5], "1", "slot 5 exact person count");
    assert_eq!(source_fields[6], "(0)", "slot 6 explicit unknown location");
    assert_eq!(source_fields[7], "(0)", "slot 7 explicit absent note");
}
