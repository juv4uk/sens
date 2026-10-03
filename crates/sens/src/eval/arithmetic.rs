//! Exact/inexact numeric handling for `+`, `-`, `*`, and `/`.
//! Obrobka tochnykh/netochnykh chysel dlia `+`, `-`, `*` ta `/`.
//! Verarbeitung exakter/inexakter Zahlen für `+`, `-`, `*` und `/`.

use crate::{Environment, ErrorKind, Exactness, LanguageError, Rational, Span, Value};

// `Rational` wraps a heap-allocated `BigRational` (arbitrary precision), so
// it isn't `Copy` — neither is `Numeric` anymore. Both accessor methods
// below take `&self` and clone on the way out where an owned `Rational` is
// needed, rather than moving out of borrowed slice/vec elements.
// `Rational` ohortaie heap-allocated BigRational (dovilna tochnist), tozh
// ne `Copy` — tak samo y `Numeric`. Obydva metody-aktsesory nyzhche berut
// `&self` i klonuiut na vykhodi tam, de potriben vlasnyi `Rational`, zamist
// peremishchennia z pozychenykh elementiv slice/vec.
// `Rational` umschließt ein heap-allokiertes `BigRational` (beliebige
// Genauigkeit), daher ist es nicht `Copy` — `Numeric` auch nicht mehr.
// Beide Zugriffsmethoden unten nehmen `&self` und klonen beim Herausgeben,
// wo ein eigener `Rational` gebraucht wird, statt aus geliehenen
// Slice-/Vec-Elementen herauszubewegen.
#[derive(Clone)]
enum Numeric {
    Exact(Rational),
    Inexact(f64),
}

impl Numeric {
    fn as_f64(&self) -> f64 {
        match self {
            Self::Exact(value) => value.as_f64(),
            Self::Inexact(value) => *value,
        }
    }

    fn to_exact(&self) -> Rational {
        match self {
            Self::Exact(value) => value.clone(),
            Self::Inexact(_) => unreachable!("inexact operands handled before exact arithmetic"),
        }
    }
}

fn numeric_value(value: Value, span: Span) -> Result<Numeric, LanguageError> {
    // Matches on `&value`, not `value`, and clones the `Rational` out:
    // `Value` has a custom `Drop` impl (iterative, for stack-safe deep-list
    // drop — see `value.rs`), which forbids partially moving a field out of
    // a match on it by value.
    // Matchyt na `&value`, ne `value`, i klonuie `Rational`: `Value` maie
    // vlasnyi `Drop` (iteratyvnyi, dlia stack-safe drop hlybokykh spyskiv —
    // dyv. `value.rs`), yakyi zaboroniaie chastkovo peremishchuvaty pole z
    // `match` za znachenniam.
    // Matcht auf `&value`, nicht `value`, und klont das `Rational` heraus:
    // `Value` hat einen eigenen `Drop`-Impl (iterativ, für stack-sicheres
    // Droppen tiefer Listen — siehe `value.rs`), der ein teilweises
    // Herausbewegen eines Feldes aus einem `match` nach Wert verbietet.
    match &value {
        Value::Rational(rational) => Ok(Numeric::Exact(rational.clone())),
        // Reads the tag the reader/arithmetic already set (PLAN.md item 10,
        // Path A) instead of re-guessing exactness from `fract() == 0.0` —
        // an exact `Value::Number` is always integral by construction (see
        // `exact_value` below), so converting straight to `i64` is safe.
        // Chytaie teh, yakyi uzhe vstanovyv reader/aryfmetyka (PLAN.md, punkt
        // 10, shliakh A), zamist toho shchob zanovo vhaduvaty exactness cherez
        // `fract() == 0.0` — tochnyi `Value::Number` zavzhdy tsilyi za
        // pobudovoiu (dyv. `exact_value` nyzhche), tozh priama konversiia v
        // `i64` bezpechna.
        Value::Number(number, Exactness::Exact) => {
            Ok(Numeric::Exact(Rational::integer(*number as i64)))
        }
        Value::Number(number, Exactness::Inexact) => Ok(Numeric::Inexact(*number)),
        _ => Err(LanguageError::new(
            ErrorKind::Type,
            "arithmetic expects numbers · aryfmetyka ochikuie chysla · Arithmetik erwartet Zahlen",
            span,
        )),
    }
}

pub(crate) fn exact_value(value: Rational) -> Value {
    match value.as_precise_i64() {
        Some(n) => Value::Number(n as f64, Exactness::Exact),
        None => Value::Rational(value),
    }
}

fn arithmetic_overflow(span: Span) -> LanguageError {
    LanguageError::new(
        ErrorKind::NumericOverflow,
        "exact arithmetic overflow · perepovnennia tochnoi aryfmetyky · Überlauf der exakten Arithmetik",
        span,
    )
}

/// Enforces an *opt-in* numeric resource limit (`Environment::with_numeric_bit_limit`)
/// — a no-op when this session never configured one, which is every
/// `conformance.lisp` fixture and the Rust reference implementation by
/// default (see S1's own open note on arbitrary precision). Checked after
/// computing an exact result, never used to fall back to an inexact
/// approximation — that would violate S1, not satisfy it.
/// Zastosovuie *optsiinu* chyslovu mezhu resursu (`Environment::with_numeric_bit_limit`)
/// — nichoho ne robyt, yakshcho tsia sesiia yii ne nalashtuvala, shcho ye typovym dlia
/// kozhnoi fikstury `conformance.lisp` y Rust-realizatsii (dyv. vlasnu
/// vidkrytu prymitku S1 pro dovilnu tochnist). Pereviriaietsia pislia
/// obchyslennia tochnoho rezultatu, nikoly ne vykorystovuietsia, shchob
/// vidkotytys do netochnoho nablyzhennia — tse porushylo b S1, ne
/// zadovolnylo b yoho.
fn check_numeric_limit(
    environment: &Environment,
    result: &Rational,
    span: Span,
) -> Result<(), LanguageError> {
    if let Some(limit) = environment.numeric_bit_limit() {
        if result.bit_length() > limit {
            return Err(LanguageError::new(
                ErrorKind::NumericOverflow,
                "exact arithmetic result exceeds the configured bit-length limit · tochnyi rezultat aryfmetyky perevyshchuie nalashtovanu mezhu v bitakh · exaktes Arithmetikergebnis überschreitet die konfigurierte Bitlängengrenze",
                span,
            ));
        }
    }
    Ok(())
}

fn compare<T: PartialOrd>(operator: &str, left: T, right: T) -> bool {
    match operator {
        "<" => left < right,
        ">" => left > right,
        "=" => left == right,
        _ => unreachable!("known comparison operator"),
    }
}

fn division_error(span: Span) -> LanguageError {
    LanguageError::new(
        ErrorKind::DivisionByZero,
        "division by zero · dilennia na nul · Division durch null",
        span,
    )
}

// ── швидкий шлях точної раціональної арифметики ──
// Коли чисельник і знаменник кожного операнда влазять у i64, дріб
// рахується в i128 і скорочується на gcd — без BigInt і без купи. Якщо
// будь-який проміжний результат не влазить у i64 (або ділення на нуль),
// повертається None і рахує звичайний шлях. Результат побітово той самий,
// що й у звичайного шляху (диференційний тест нижче): точність S1 не
// змінюється, змінюється лише спосіб обчислення.

fn small_exact(value: &Value) -> Option<(i128, i128)> {
    match value {
        // Точний Number — завжди ціле в межах ±2^53 (див. exact_value).
        Value::Number(number, Exactness::Exact) => Some((*number as i64 as i128, 1)),
        Value::Rational(rational) => rational
            .small_parts()
            .map(|(numerator, denominator)| (numerator as i128, denominator as i128)),
        _ => None,
    }
}

fn gcd_u128(mut a: u128, mut b: u128) -> u128 {
    while b != 0 {
        let rest = a % b;
        a = b;
        b = rest;
    }
    a
}

fn fits_i64(value: i128) -> bool {
    (i64::MIN as i128..=i64::MAX as i128).contains(&value)
}

/// Нормальна форма: знаменник > 0, дріб скорочений, нуль — 0/1.
fn reduce_small(numerator: i128, denominator: i128) -> Option<(i128, i128)> {
    if denominator == 0 {
        return None;
    }
    let (numerator, denominator) = if denominator < 0 {
        (numerator.checked_neg()?, denominator.checked_neg()?)
    } else {
        (numerator, denominator)
    };
    let divisor = gcd_u128(numerator.unsigned_abs(), denominator as u128) as i128;
    let (numerator, denominator) = (numerator / divisor, denominator / divisor);
    (fits_i64(numerator) && fits_i64(denominator)).then_some((numerator, denominator))
}

fn small_step(operator: char, left: (i128, i128), right: (i128, i128)) -> Option<(i128, i128)> {
    let ((n1, d1), (n2, d2)) = (left, right);
    let (numerator, denominator) = match operator {
        '+' => (n1.checked_mul(d2)?.checked_add(n2.checked_mul(d1)?)?, d1.checked_mul(d2)?),
        '-' => (n1.checked_mul(d2)?.checked_sub(n2.checked_mul(d1)?)?, d1.checked_mul(d2)?),
        '*' => (n1.checked_mul(n2)?, d1.checked_mul(d2)?),
        '/' => (n1.checked_mul(d2)?, d1.checked_mul(n2)?),
        _ => return None,
    };
    reduce_small(numerator, denominator)
}

fn small_rational_fast_path(
    operator: char,
    values: &[Value],
    environment: &Environment,
    span: Span,
) -> Option<Result<Value, LanguageError>> {
    let parts = values.iter().map(small_exact).collect::<Option<Vec<_>>>()?;
    let (numerator, denominator) = match (operator, parts.len()) {
        (_, 0) => return None,
        ('-', 1) => reduce_small(parts[0].0.checked_neg()?, parts[0].1)?,
        ('/', 1) => small_step('/', (1, 1), parts[0])?,
        ('+', _) => parts.iter().try_fold((0, 1), |acc, &part| small_step('+', acc, part))?,
        ('*', _) => parts.iter().try_fold((1, 1), |acc, &part| small_step('*', acc, part))?,
        _ => parts[1..]
            .iter()
            .try_fold(parts[0], |acc, &part| small_step(operator, acc, part))?,
    };
    const MAX_EXACT: i128 = 1 << 53;
    if denominator == 1
        && (-MAX_EXACT..=MAX_EXACT).contains(&numerator)
        && environment.numeric_bit_limit().is_none()
    {
        return Some(Ok(Value::Number(numerator as f64, Exactness::Exact)));
    }
    let rational = Rational::from_reduced_small(numerator as i64, denominator as i64);
    Some(check_numeric_limit(environment, &rational, span).map(|()| exact_value(rational)))
}

// ── contract 2.1: value-level entry points (first-class builtins) ──
// The expr-handlers above evaluate arguments then delegate here; the
// builtin closures in eval/builtins.rs call these directly with
// pre-evaluated values. Single compute path, two front doors.

pub(super) fn arithmetic_on_values(
    operator: &str,
    values: &[Value],
    environment: &Environment,
    span: Span,
) -> Result<Value, LanguageError> {
    if operator == "-" && values.is_empty() {
        return Err(LanguageError::new(
            ErrorKind::Arity,
            "- expects at least one argument · - ochikuie shchonaimenshe odyn arhument · - erwartet mindestens ein Argument",
            span,
        ));
    }
    // ── fast path: all exact integers that fit in i64 ──
    // Avoids BigRational allocation + gcd normalization for the
    // most common case in real workloads (WSM-24 evidence).
    // ── fast path: all exact integers that fit in i64 ──
    if values.iter().all(|v| {
        matches!(
            v, Value::Number(f, Exactness::Exact)
            if *f == (*f as i64) as f64 && f.abs() <= 9_000_000_000_000.0
        )
    }) {
        let ints: Vec<i64> = values
            .iter()
            .map(|v| {
                if let Value::Number(f, Exactness::Exact) = v {
                    *f as i64
                } else {
                    unreachable!()
                }
            })
            .collect();
        let result: Option<i64> = match operator {
            "+" => ints.iter().try_fold(0i64, |acc, &x| acc.checked_add(x)),
            "-" => match ints.len() {
                1 => Some(-ints[0]),
                _ => ints[1..]
                    .iter()
                    .try_fold(ints[0], |acc, &x| acc.checked_sub(x)),
            },
            "*" => ints.iter().try_fold(1i64, |acc, &x| acc.checked_mul(x)),
            _ => None,
        };
        if let Some(result) = result {
            let exact = Rational::integer(result);
            check_numeric_limit(environment, &exact, span)?;
            // `checked_*` proves only i64 range, not f64 exact-integer range.
            // Route through the one compression gate that knows the ±2^53
            // boundary so a fast-path result can never be silently rounded
            // while still carrying `Exactness::Exact`.
            return Ok(exact_value(exact));
        }
        // overflow: fall through to bignum path below
    }

    let operator_char = operator.chars().next().unwrap_or(' ');
    if let Some(result) = small_rational_fast_path(operator_char, values, environment, span) {
        return result;
    }

    let numerics = values
        .iter()
        .map(|value| numeric_value(value.clone(), span))
        .collect::<Result<Vec<_>, _>>()?;

    if numerics
        .iter()
        .any(|value| matches!(value, Numeric::Inexact(_)))
    {
        let floats = numerics.iter().map(Numeric::as_f64).collect::<Vec<_>>();
        let mut result = floats[0];
        for &operand in &floats[1..] {
            result = match operator {
                "+" => result + operand,
                "-" => result - operand,
                "*" => result * operand,
                _ => unreachable!("known arithmetic operator"),
            };
        }
        return Ok(Value::Number(result, Exactness::Inexact));
    }

    let exact = numerics.iter().map(Numeric::to_exact).collect::<Vec<_>>();
    let result = match operator {
        "+" => exact
            .into_iter()
            .try_fold(Rational::integer(0), Rational::checked_add),
        "*" => exact
            .into_iter()
            .try_fold(Rational::integer(1), Rational::checked_mul),
        "-" if exact.len() == 1 => exact[0].clone().checked_neg(),
        "-" => exact[1..]
            .iter()
            .try_fold(exact[0].clone(), |result, value| {
                result.checked_sub(value.clone())
            }),
        _ => unreachable!("known arithmetic operator"),
    }
    .ok_or_else(|| arithmetic_overflow(span))?;
    check_numeric_limit(environment, &result, span)?;
    Ok(exact_value(result))
}

pub(super) fn division_on_values(
    values: &[Value],
    argument_count: usize,
    environment: &Environment,
    span: Span,
) -> Result<Value, LanguageError> {
    if values.is_empty() {
        return Err(LanguageError::new(
            ErrorKind::Arity,
            "/ expects at least one argument · / ochikuie shchonaimenshe odyn arhument · / erwartet mindestens ein Argument",
            span,
        ));
    }
    if argument_count == values.len() {
        if let Some(result) = small_rational_fast_path('/', values, environment, span) {
            return result;
        }
    }

    let numerics = values
        .iter()
        .map(|value| numeric_value(value.clone(), span))
        .collect::<Result<Vec<_>, _>>()?;

    let single = argument_count == 1;

    if numerics
        .iter()
        .any(|value| matches!(value, Numeric::Inexact(_)))
    {
        let floats = numerics.iter().map(Numeric::as_f64).collect::<Vec<_>>();
        let mut result = floats[0];
        if single {
            if result == 0.0 {
                return Err(division_error(span));
            }
            result = 1.0 / result;
        } else {
            for &divisor in &floats[1..] {
                if divisor == 0.0 {
                    return Err(division_error(span));
                }
                result /= divisor;
            }
        }
        return Ok(Value::Number(result, Exactness::Inexact));
    }

    let exact = numerics.iter().map(Numeric::to_exact).collect::<Vec<_>>();
    let mut result = exact[0].clone();
    if single {
        result = Rational::integer(1)
            .checked_div(result)
            .ok_or_else(|| division_error(span))?;
    } else {
        for divisor in exact.into_iter().skip(1) {
            result = result
                .checked_div(divisor)
                .ok_or_else(|| division_error(span))?;
        }
    }
    check_numeric_limit(environment, &result, span)?;
    Ok(exact_value(result))
}

pub(super) fn comparison_on_values(
    operator: &str,
    values: &[Value],
    span: Span,
) -> Result<Value, LanguageError> {
    if values.is_empty() {
        return Err(LanguageError::new(
            ErrorKind::Arity,
            format!("{operator} expects at least one argument · {operator} ochikuie shchonaimenshe odyn arhument · {operator} erwartet mindestens ein Argument"),
            span,
        ));
    }
    let numerics = values
        .iter()
        .map(|value| numeric_value(value.clone(), span))
        .collect::<Result<Vec<_>, _>>()?;

    if numerics
        .iter()
        .any(|value| matches!(value, Numeric::Inexact(_)))
    {
        return Err(LanguageError::new(
            ErrorKind::Type,
            "comparison predicate requires exact numeric operands",
            span,
        ));
    }

    let holds = numerics
        .windows(2)
        .all(|pair| compare(operator, pair[0].to_exact(), pair[1].to_exact()));

    Ok(Value::predicate_bit(holds))
}

#[cfg(test)]
mod rational_fast_path_tests {
    use super::*;

    /// Еталон: повільний шлях на BigRational, без швидкого шляху.
    fn reference(operator: char, values: &[Value]) -> Option<Value> {
        let exact = values
            .iter()
            .map(|value| match numeric_value(value.clone(), Span::default()).ok()? {
                Numeric::Exact(rational) => Some(rational),
                Numeric::Inexact(_) => None,
            })
            .collect::<Option<Vec<_>>>()?;
        let result = match (operator, exact.len()) {
            (_, 0) => return None,
            ('-', 1) => exact[0].clone().checked_neg()?,
            ('/', 1) => Rational::integer(1).checked_div(exact[0].clone())?,
            ('+', _) => exact.into_iter().try_fold(Rational::integer(0), Rational::checked_add)?,
            ('*', _) => exact.into_iter().try_fold(Rational::integer(1), Rational::checked_mul)?,
            ('-', _) => exact[1..].iter().try_fold(exact[0].clone(), |r, v| r.checked_sub(v.clone()))?,
            ('/', _) => exact[1..].iter().try_fold(exact[0].clone(), |r, v| r.checked_div(v.clone()))?,
            _ => return None,
        };
        Some(exact_value(result))
    }

    struct Lcg(u64);
    impl Lcg {
        fn next(&mut self) -> u64 {
            self.0 = self.0.wrapping_mul(6364136223846793005).wrapping_add(1442695040888963407);
            self.0 >> 11
        }
        fn int(&mut self) -> i64 {
            match self.next() % 8 {
                0 => 0,
                1 => i64::MAX - (self.next() % 3) as i64,
                2 => i64::MIN + (self.next() % 3) as i64,
                3 => (self.next() as i64) >> (self.next() % 60),
                _ => (self.next() % 2001) as i64 - 1000,
            }
        }
        fn value(&mut self) -> Value {
            let numerator = self.int();
            let denominator = match self.next() % 3 {
                0 => 1,
                _ => self.int(),
            };
            match Rational::new(numerator, denominator) {
                Some(rational) => exact_value(rational),
                None => exact_value(Rational::integer(numerator)),
            }
        }
    }

    fn same(left: &Value, right: &Value) -> bool {
        match (left, right) {
            (Value::Number(a, ea), Value::Number(b, eb)) => a == b && ea == eb,
            (Value::Rational(a), Value::Rational(b)) => a == b,
            _ => false,
        }
    }

    #[test]
    fn fast_path_is_identical_to_bigrational_reference() {
        let environment = Environment::root();
        let mut random = Lcg(0x5e45_1413);
        let (mut fast_hits, mut fallbacks) = (0usize, 0usize);
        for _ in 0..200_000 {
            let operator = ['+', '-', '*', '/'][(random.next() % 4) as usize];
            let arity = 1 + (random.next() % 4) as usize;
            let values: Vec<Value> = (0..arity).map(|_| random.value()).collect();
            match small_rational_fast_path(operator, &values, &environment, Span::default()) {
                Some(Ok(fast)) => {
                    fast_hits += 1;
                    let expected = reference(operator, &values)
                        .unwrap_or_else(|| panic!("fast path answered where reference failed: {operator} {values:?}"));
                    assert!(same(&fast, &expected), "{operator} {values:?}: fast={fast} reference={expected}");
                }
                Some(Err(error)) => panic!("fast path error without limit: {error:?}"),
                None => fallbacks += 1,
            }
        }
        assert!(fast_hits > 100_000, "швидкий шлях має покривати більшість малих випадків: {fast_hits}");
        eprintln!("швидкий шлях: {fast_hits}, передано повільному: {fallbacks}");
    }

    #[test]
    fn fast_path_matches_conformance_examples() {
        let environment = Environment::root();
        let q = |n, d| exact_value(Rational::new(n, d).unwrap());
        let cases = [
            ('/', vec![q(5, 1), q(6, 1), q(8, 1), q(7, 1)], "5/336"),
            ('+', vec![q(1, 3), q(1, 3)], "2/3"),
            ('-', vec![q(1, 1), q(1, 3)], "2/3"),
            ('*', vec![q(2, 3), q(9, 4)], "3/2"),
            ('-', vec![q(1, 3)], "-1/3"),
            ('+', vec![q(1, 3), q(1, 6)], "1/2"),
            ('/', vec![q(6, 1), q(3, 1)], "2"),
        ];
        for (operator, values, expected) in cases {
            let result = small_rational_fast_path(operator, &values, &environment, Span::default())
                .expect("small case takes the fast path")
                .unwrap();
            assert_eq!(result.to_string(), expected, "{operator} {values:?}");
        }
    }

    #[test]
    fn division_by_zero_falls_back_to_the_named_error() {
        let environment = Environment::root();
        let values = [exact_value(Rational::integer(1)), exact_value(Rational::integer(0))];
        assert!(small_rational_fast_path('/', &values, &environment, Span::default()).is_none());
        assert!(division_on_values(&values, 2, &environment, Span::default()).is_err());
    }
}
