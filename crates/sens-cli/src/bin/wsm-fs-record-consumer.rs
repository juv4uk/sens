//! Consume the bounded F6 record stream and reconstruct its WSM root.
//! Stored envelopes are quoted data; this binary never evaluates their payload.

use sens::{
    eval_parsed_expressions, load_core_library, Bija3, Bit3, Bit4, Bit9, CoreD4, CoreD9,
    DomainIdentity, Environment, Expr, ExprKind, Session, Span, Value,
};
#[cfg(test)]
use sens::{Bit7, D7DataWord};
use std::io::{self, Read};
use std::rc::Rc;

fn exact_d4(bits: u8) -> DomainIdentity {
    DomainIdentity::D4(CoreD4::from_word(Bit4::new(bits).expect("D4 coordinate")))
}

fn exact_d9(bits: u16) -> DomainIdentity {
    DomainIdentity::D9(CoreD9::from_word(Bit9::new(bits).expect("D9 coordinate")))
}

fn exact_d3(bits: u8) -> DomainIdentity {
    DomainIdentity::D3(Bija3::from_word(Bit3::new(bits).expect("D3 coordinate")))
}

fn call(identity: DomainIdentity, arguments: Vec<Expr>) -> Expr {
    let mut items = Vec::with_capacity(arguments.len() + 1);
    items.push(Expr {
        kind: ExprKind::DomainIdentity(identity),
        span: Span::default(),
    });
    items.extend(arguments);
    Expr {
        kind: ExprKind::List(items.into()),
        span: Span::default(),
    }
}

// D4:1110 is the canonical LIST resident. D4:1001 is CADR,
// a selector, and must never be used as a packet/list constructor.
fn d4_list(arguments: Vec<Expr>) -> Expr {
    call(exact_d4(0b1110), arguments)
}

fn string_value(value: &str) -> Expr {
    Expr {
        kind: ExprKind::String(Rc::from(value)),
        span: Span::default(),
    }
}

/// Хост-маркер як СИМВОЛ — саме цю форму доводив тест f6_quoted_marker_matches_native_source
/// (видалявся комітом 3c2e259b7). Нативне SENS-цитування (як-є accepted) дає символ, не D7-список.
fn symbol_value(value: &str) -> Expr {
    Expr {
        kind: ExprKind::Symbol(Rc::from(value)),
        span: Span::default(),
    }
}

#[cfg(test)]
fn d7_text_data(value: &str) -> Expr {
    assert!(value.is_ascii(), "F6 protocol marker must be ASCII D7 data");
    Expr {
        kind: ExprKind::List(
            value
                .bytes()
                .map(|byte| Expr {
                    kind: ExprKind::DomainIdentity(DomainIdentity::D7(D7DataWord::from_word(
                        Bit7::new(byte).expect("ASCII byte fits D7"),
                    ))),
                    span: Span::default(),
                })
                .collect::<Vec<_>>()
                .into(),
        ),
        span: Span::default(),
    }
}

// Узгоджено з фізичним F6 producer: два UTF-8 записи, кожен 1..65536
// байтів, кожен завершується LF. Rust обмежує лише транспорт;
// оцінювання та перевірка вмісту залишаються в SENS.
const MAX_RECORD_BYTES: usize = 64 * 1024;
const MAX_WIRE_BYTES: usize = 2 * (MAX_RECORD_BYTES + 1);

fn read_two_records<R: Read>(input: R) -> Result<[String; 2], &'static str> {
    // +1 — свідок переповнення. Навіть ворожий stdin не може
    // змусити нас прочитати чи накопичити більше цього ліміту.
    let mut bounded = input.take((MAX_WIRE_BYTES + 1) as u64);
    let mut wire = Vec::new();
    bounded
        .read_to_end(&mut wire)
        .map_err(|_| "F6_INPUT_IO expected=readable-stream")?;
    if wire.len() > MAX_WIRE_BYTES {
        return Err("F6_RECORD_STREAM_SIZE expected<=131074");
    }
    if !wire.ends_with(b"\n") {
        return Err("F6_RECORD_TERMINATOR expected=final-LF");
    }
    if wire.contains(&b'\r') || wire.contains(&b'\0') {
        return Err("F6_RECORD_DELIMITER expected=LF-only");
    }

    // Знімаємо рівно один кінцевий LF: додатковий порожній кадр не
    // губиться, на відміну від lines().filter(trim-empty).
    let mut frames = wire[..wire.len() - 1].split(|byte| *byte == b'\n');
    let first = frames.next().ok_or("F6_RECORD_COUNT expected=2")?;
    let second = frames.next().ok_or("F6_RECORD_COUNT expected=2")?;
    if frames.next().is_some() {
        return Err("F6_RECORD_COUNT expected=2 actual=more-than-2");
    }
    if first.is_empty()
        || second.is_empty()
        || first.len() > MAX_RECORD_BYTES
        || second.len() > MAX_RECORD_BYTES
    {
        return Err("F6_RECORD_SIZE expected=1..65536");
    }
    let root = std::str::from_utf8(first).map_err(|_| "F6_RECORD_UTF8 expected=valid")?;
    let object = std::str::from_utf8(second).map_err(|_| "F6_RECORD_UTF8 expected=valid")?;
    Ok([root.to_owned(), object.to_owned()])
}

fn main() {
    let records = read_two_records(io::stdin()).unwrap_or_else(|error| {
        eprintln!("wsm-fs-record-consumer: {error}");
        std::process::exit(2)
    });
    let mut session = Session {
        environment: Environment::root(),
    };
    load_core_library(&mut session).unwrap();
    if let Err(error) = sens_cli::bootstrap_f6_t5m_libraries(&mut session) {
        eprintln!("wsm-fs-record-consumer: physical F6 bootstrap failed: {error}");
        std::process::exit(1);
    }
    // Точні зовнішні оболонки — дані, не програми.
    // D8:11101010 READ повертає самі пакети, без зайвого
    // deserialize -> CADR -> repackage, що могло змінити оболонку.
    // Наявний D9 FS-RECONSTRUCT-ROOT перевіряє структуру й адреси
    // обох оригінальних пакетів за законами SENS.
    let root_package = call(exact_d8_read(), vec![string_value(&records[0])]);
    let object_package = call(exact_d8_read(), vec![string_value(&records[1])]);
    let object_packages = d4_list(vec![object_package]);
    let reconstruction = call(
        exact_d9(0b010101000),
        vec![root_package.clone(), object_packages],
    );
    // SENS performs the D3 selection and D8 structural comparison. Rust
    // checks only the resulting exact D1 answer.
    let status = call(exact_d3(0b100), vec![reconstruction.clone()]);
    // У фізичному F6-свідку (як-є accepted) зберігає точний D7 carrier,
    // не Rust Symbol. SENS D8 EQUAL порівнює саме цей носій без alias.
    let expected = call(exact_d3(0b001), vec![d7_text_data("accepted")]);
    let accepted = call(exact_d8_equal(), vec![status, expected]);
    let verdict = eval_parsed_expressions(&[accepted], &mut session)
        .unwrap_or_else(|error| {
            eprintln!("root reconstruction failed: {error}");
            std::process::exit(1)
        })
        .value;
    let accepted_bit = sens::PredicateBit::from_word(sens::Bit1::new(1).unwrap());
    if verdict != Value::DomainIdentity(DomainIdentity::D1(accepted_bit)) {
        // Re-run only this immutable SENS reconstruction on failure so CI
        // captures the exact semantic result/reason, not just a D1:0 summary.
        let detail = eval_parsed_expressions(&[reconstruction], &mut session)
            .map(|result| result.value.to_string())
            .unwrap_or_else(|error| format!("diagnostic-evaluation-error={error}"));
        // F6 fail-closed proof: inspect only the D1 equality verdicts of
        // the exact FIRST root field. Do not render the incoming payload:
        // only SENS decides whether WRITE→READ preserved the format identity.
        // This differentiates a quoted D7 marker, a D8 READ marker, and a
        // host String without accepting any of them as an extra protocol type.
        let format_value = call(
            exact_d3(0b011), // D3 CDR of the first (format . value) pair
            vec![call(exact_d3(0b100), vec![root_package.clone()])],
        );
        let source_marker = call(exact_d3(0b001), vec![symbol_value("wsm-fs-root")]);
        let read_marker = call(exact_d8_read(), vec![string_value("wsm-fs-root")]);
        let format_proof = d4_list(vec![
            call(exact_d8_equal(), vec![format_value.clone(), source_marker]),
            call(exact_d8_equal(), vec![format_value.clone(), read_marker]),
            call(
                exact_d8_equal(),
                vec![format_value, string_value("wsm-fs-root")],
            ),
        ]);
        let format_proof_result = eval_parsed_expressions(&[format_proof], &mut session)
            .map(|result| result.value.to_string())
            .unwrap_or_else(|error| format!("proof-type-error={error}"));
        eprintln!(
            "root reconstruction rejected: verdict={verdict} detail={detail} F6_FORMAT_BRIDGE_D1=[quote,read,string]:{format_proof_result}"
        );
        std::process::exit(1);
    }
    println!("f6-semantic-consumer-ok records=2");
}

fn exact_d8_read() -> DomainIdentity {
    DomainIdentity::D8(sens::CoreD8::from_word(
        sens::Bit8::new(0b11101010).expect("D8 READ identity"),
    ))
}

fn exact_d8_equal() -> DomainIdentity {
    DomainIdentity::D8(sens::CoreD8::from_word(
        sens::Bit8::new(0b11110111).expect("D8 equal identity"),
    ))
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::io::Cursor;

    #[test]
    fn f6_accepted_marker_is_encoded_as_exact_d7_words() {
        let value = d7_text_data("accepted");
        let ExprKind::List(words) = value.kind else {
            panic!("text data must be a D7 word list");
        };
        assert_eq!(words.len(), "accepted".len());
        for (word, byte) in words.iter().zip(b"accepted") {
            let ExprKind::DomainIdentity(DomainIdentity::D7(word)) = &word.kind else {
                panic!("text symbol must lower only to D7 identities");
            };
            assert_eq!(word.word().packed_bits(), *byte);
        }
    }

    #[test]
    fn f6_reader_accepts_exactly_two_records_and_preserves_whitespace() {
        let decoded = read_two_records(" root \nobject \n".as_bytes()).unwrap();
        assert_eq!(decoded, [" root ".to_owned(), "object ".to_owned()]);
        let maximum = "x".repeat(MAX_RECORD_BYTES);
        let stream = format!("{maximum}\n{maximum}\n");
        assert_eq!(
            read_two_records(stream.as_bytes()).unwrap(),
            [maximum.clone(), maximum]
        );
    }

    #[test]
    fn f6_reader_rejects_hidden_empty_and_extra_frames() {
        for stream in [
            "",
            "root\n",
            "root\n\n",
            "root\n\nobject\n",
            "root\nobject\n\n",
            "root\nobject\nthird\n",
            "root\nobject",
            "\nobject\n",
        ] {
            assert!(
                read_two_records(stream.as_bytes()).is_err(),
                "додатковий чи порожній кадр прийнято: {stream:?}"
            );
        }
    }

    #[test]
    fn f6_reader_rejects_control_bytes_non_utf8_and_oversize_record() {
        for stream in [
            &b"root\r\nobject\n"[..],
            &b"root\0\nobject\n"[..],
            &b"root\nob\0ject\n"[..],
            &b"\xff\nobject\n"[..],
        ] {
            assert!(
                read_two_records(stream).is_err(),
                "пошкоджені байти прийнято"
            );
        }
        let oversized = format!("{}\nobject\n", "x".repeat(MAX_RECORD_BYTES + 1));
        assert!(read_two_records(oversized.as_bytes()).is_err());
    }

    #[test]
    fn f6_reader_stops_reading_after_bounded_overflow_witness() {
        let bytes = vec![b'x'; MAX_WIRE_BYTES + 4096];
        let mut reader = Cursor::new(bytes);
        assert!(read_two_records(&mut reader).is_err());
        assert_eq!(reader.position(), (MAX_WIRE_BYTES + 1) as u64);
    }

    /// ПОВЕРНУТО (видалявся комітом 3c2e259b7 разом із заміною symbol_value -> d7_text_data).
    /// Доводить, що ПОТОЧНИЙ виробничий хелпер (d7_text_data) мусить збігатися з НАТИВНИМ SENS-цитуванням (як-є accepted). Якщо падає — виробниче представлення маркера хибне.
    #[test]
    fn f6_quoted_marker_matches_native_source() {
        let mut session = Session {
            environment: Environment::root(),
        };
        load_core_library(&mut session).expect("native SENS Core");
        let expected_from_source = sens::eval_program("(як-є accepted)", &mut session)
            .expect("native SENS quoted symbol")
            .value;
        let expected_from_wire = eval_parsed_expressions(
            &[call(exact_d3(0b001), vec![symbol_value("accepted")])],
            &mut session,
        )
        .expect("native D3:001 SENS QUOTE")
        .value;
        assert_eq!(
            expected_from_wire, expected_from_source,
            "test_id=F6-QUOTED-MARKER layer=SENS expected=source-quote actual=transport-AST"
        );
    }
}
