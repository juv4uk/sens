//! Consume the bounded F6 record stream and reconstruct its WSM root.
//! Stored envelopes are quoted data; this binary never evaluates their payload.

use sens::{
    eval_parsed_expressions, load_core_library, Bija3, Bit3, Bit4, Bit7, Bit9, CoreD4, CoreD9,
    D7DataWord, DomainIdentity, Environment, Expr, ExprKind, Session, Span, Value,
};
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

fn string_value(value: &str) -> Expr {
    Expr {
        kind: ExprKind::String(Rc::from(value)),
        span: Span::default(),
    }
}

fn d7_text(value: &str) -> Expr {
    Expr {
        kind: ExprKind::List(
            value
                .bytes()
                .map(|byte| Expr {
                    kind: ExprKind::DomainIdentity(DomainIdentity::D7(D7DataWord::from_word(
                        Bit7::new(byte).expect("D7 protocol glyph"),
                    ))),
                    span: Span::default(),
                })
                .collect::<Vec<_>>()
                .into(),
        ),
        span: Span::default(),
    }
}

fn main() {
    let mut input = String::new();
    io::stdin().read_to_string(&mut input).unwrap();
    let records: Vec<_> = input
        .lines()
        .filter(|line| !line.trim().is_empty())
        .collect();
    if records.len() != 2 {
        eprintln!("expected exactly two records");
        std::process::exit(2);
    }
    let mut session = Session {
        environment: Environment::root(),
    };
    load_core_library(&mut session).unwrap();
    if let Err(error) = sens_cli::bootstrap_f6_t5m_libraries(&mut session) {
        eprintln!("wsm-fs-record-consumer: physical F6 bootstrap failed: {error}");
        std::process::exit(1);
    }
    // These exact identities are the ratified D9/D4 entries in
    // lib/domains/d9.lisp and lib/domains/d4.lisp. Rust builds only an exact
    // SENS call tree; all record parsing and validation executes in SENS.
    let root_package = call(
        exact_d4(0b1001),
        vec![call(exact_d9(0b001110011), vec![string_value(records[0])])],
    );
    let object_value = call(
        exact_d4(0b1001),
        vec![call(exact_d9(0b101000110), vec![string_value(records[1])])],
    );
    let object_package = call(exact_d9(0b010100010), vec![object_value]);
    let object_packages = call(exact_d4(0b1110), vec![object_package]);
    let reconstruction = call(exact_d9(0b010101000), vec![root_package, object_packages]);
    // SENS performs the D3 selection and D8 structural comparison. Rust
    // checks only the resulting exact D1 answer.
    let status = call(exact_d3(0b100), vec![reconstruction]);
    let expected = call(exact_d3(0b001), vec![d7_text("accepted")]);
    let accepted = call(exact_d8_equal(), vec![status, expected]);
    let verdict = eval_parsed_expressions(&[accepted], &mut session)
        .unwrap_or_else(|error| {
            eprintln!("root reconstruction failed: {error}");
            std::process::exit(1)
        })
        .value;
    let accepted_bit = sens::PredicateBit::from_word(sens::Bit1::new(1).unwrap());
    if verdict != Value::DomainIdentity(DomainIdentity::D1(accepted_bit)) {
        eprintln!("root reconstruction rejected: {verdict}");
        std::process::exit(1);
    }
    println!("f6-semantic-consumer-ok records=2");
}

fn exact_d8_equal() -> DomainIdentity {
    DomainIdentity::D8(sens::CoreD8::from_word(
        sens::Bit8::new(0b11110111).expect("D8 equal identity"),
    ))
}
