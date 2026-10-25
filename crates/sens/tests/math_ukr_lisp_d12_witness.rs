//! Наскрізний свідок української десяткової проєкції та математики D12+.
//! Людські цифри — десяткові дані; проєктор призначає домен, а не ширина
//! запису. Переповнення D12 зберігає значення переходом у D24.
use sens::{eval_parsed_expressions, lower_program, parse, Session, Value};

fn eval_d12_source(source: &str, session: &mut Session) -> Result<Value, sens::LanguageError> {
    let parsed = parse(source)?;
    let projected =
        sens::source_projection::project_ukr_decimal_integer_literals_with_minimum_width(
            &parsed, source, 12,
        )?;
    let lowered = lower_program(&projected);
    eval_parsed_expressions(&lowered, session).map(|result| result.value)
}

fn signed(width: usize, value: i32) -> Value {
    let encoded = if value < 0 {
        ((1_i64 << width) + i64::from(value)) as u64
    } else {
        value as u64
    };
    let bits = (0..width)
        .rev()
        .map(|shift| ((encoded >> shift) & 1) as u8)
        .collect::<Vec<_>>();
    Value::BinaryNumber(
        sens::BinaryNumber::from_numeric_domain_bits(width, &bits)
            .expect("ratified signed D12+ width"),
    )
}

#[test]
fn українська_десяткова_проєкція_виконує_d12_арифметику_і_розширює_без_втрати() {
    let mut session = Session::default();
    for (source, expected_width, expected) in [
        ("(додати 2047 1)", 24, 2048),
        ("(відняти -2048 1)", 24, -2049),
        ("(помножити -12 13)", 12, -156),
        ("(додати 12 30)", 12, 42),
    ] {
        let actual = eval_d12_source(source, &mut session)
            .unwrap_or_else(|error| panic!("{source}: {error}"));
        assert_eq!(actual, signed(expected_width, expected), "{source}");
    }
}
