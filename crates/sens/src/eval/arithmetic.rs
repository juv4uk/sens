//! Exact/inexact numeric handling for `+`, `-`, `*`, and `/`.
//! Obrobka tochnykh/netochnykh chysel dlia `+`, `-`, `*` ta `/`.
//! Verarbeitung exakter/inexakter Zahlen für `+`, `-`, `*` und `/`.

use crate::{BinaryNumber, Environment, ErrorKind, Exactness, LanguageError, Rational, Span, Value};
use crate::domain_numeric;

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

/// Domain words are exact binary digit strings, not automatically numbers.
/// Only explicitly qualified D24+ values admit arithmetic and numeric ordering.
/// Legacy unqualified Number/Rational/BinaryNumber remains representable for
/// transport/migration, never a source of mathematical operand authority.
fn require_math_domain(values: &[Value], span: Span) -> Result<(), LanguageError> {
    if values.is_empty() || values.iter().any(|v| !domain_numeric::is_domain_value(v)) {
        return Err(LanguageError::new(
            ErrorKind::Type,
            "math requires explicit D24+ operands; D1-D10 bit words and unqualified numbers are not arithmetic values",
            span,
        ));
    }
    Ok(())
}

pub(super) fn arithmetic_on_values(
    operator: &str,
    values: &[Value],
    environment: &Environment,
    span: Span,
) -> Result<Value, LanguageError> {
    require_math_domain(values, span)?;
    // Domain-qualified numeric atoms and lawful NEG/RATIO compositions are
    // handled by ONE exact binary arithmetic engine. No implicit conversion
    // from legacy Number/Rational, no new Dn domain, no host floating point.
    if values.iter().any(domain_numeric::is_domain_value) {
        let result = match values {
            [single] if operator == "-" => domain_numeric::unary("-", single),
            [left, right] => domain_numeric::compute(operator, left, right),
            _ => None,
        }.ok_or_else(|| LanguageError::new(
            ErrorKind::Type,
            "numeric Dn composition requires same-domain operands and a supported operation",
            span,
        ))?;
        let bit_length = match &result {
            Value::BinaryNumber(value) => value.width(),
            Value::NumericComposition(value) => {
                let (_, numerator, denominator) = value.as_parts();
                numerator.width().max(denominator.map_or(0, BinaryNumber::width))
            }
            _ => return Err(LanguageError::new(ErrorKind::Type, "numeric composite invariant", span)),
        };
        if environment.numeric_bit_limit().is_some_and(|limit| bit_length > limit) {
            return Err(arithmetic_overflow(span));
        }
        return Ok(result);
    }

    // #3022 canonical Number path. Once a BinaryNumber participates, every
    // operand must be a BinaryNumber; no implicit bridge to legacy f64/Q is
    // permitted. Natural subtraction is partial until signed Number is ratified.
    if values.iter().any(|value| matches!(value, Value::BinaryNumber(_))) {
        let numbers = values
            .iter()
            .map(|value| match value {
                Value::BinaryNumber(number) => Ok(number),
                _ => Err(LanguageError::new(
                    ErrorKind::Type,
                    "binary Number does not implicitly coerce legacy numeric values",
                    span,
                )),
            })
            .collect::<Result<Vec<&BinaryNumber>, _>>()?;

        // Core accepts exact binary arithmetic only on TWO operands with
        // explicitly identical Dn numeric domains. Naturals keep their Dn
        // identity. ADD/MUL promote only if the result actually needs more
        // bits, to the next D(2n); SUB stays in Dn if nonnegative.
        // A negative SUB needs canonical NEG composition, not a wrapped word.
        if numbers.iter().any(|number| number.numeric_domain_width().is_some()) {
            if numbers.len() != 2
                || numbers[0].numeric_domain_width().is_none()
                || numbers[0].numeric_domain_width() != numbers[1].numeric_domain_width()
            {
                return Err(LanguageError::new(
                    ErrorKind::Type,
                    "qualified numeric arithmetic requires exactly two operands in the same Dn",
                    span,
                ));
            }
            let result = match operator {
                "+" => numbers[0].add_admitted_numeric(numbers[1]),
                "*" => numbers[0].mul_admitted_numeric(numbers[1]),
                "-" => numbers[0].checked_sub_admitted_numeric(numbers[1]),
                _ => None,
            }.ok_or_else(|| LanguageError::new(
                ErrorKind::Type,
                "unsupported Dn operation or negative result requiring unimplemented NEG composition",
                span,
            ))?;
            if environment.numeric_bit_limit().is_some_and(|limit| result.width() > limit) {
                return Err(arithmetic_overflow(span));
            }
            return Ok(Value::BinaryNumber(result));
        }

        let result = match operator {
            "+" => numbers
                .into_iter()
                .fold(BinaryNumber::zero(), |acc, value| acc.add(value)),
            "*" => numbers
                .into_iter()
                .fold(BinaryNumber::one(), |acc, value| acc.mul(value)),
            "-" => {
                let mut result = if numbers.len() == 1 {
                    BinaryNumber::zero()
                } else {
                    (*numbers[0]).clone()
                };
                let subtractors = if numbers.len() == 1 {
                    &numbers[..]
                } else {
                    &numbers[1..]
                };
                for &number in subtractors {
                    result = result.checked_sub(number).ok_or_else(|| {
                        LanguageError::new(
                            ErrorKind::Type,
                            "negative binary Number requires an unratified signed encoding",
                            span,
                        )
                    })?;
                }
                result
            }
            _ => {
                return Err(LanguageError::new(
                    ErrorKind::Type,
                    "binary Number operation is not admitted in the natural-number slice",
                    span,
                ))
            }
        };

        if environment
            .numeric_bit_limit()
            .is_some_and(|limit| result.width() > limit)
        {
            return Err(arithmetic_overflow(span));
        }
        return Ok(Value::BinaryNumber(result));
    }

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
    require_math_domain(values, span)?;
    // Reciprocal or exact rational division over admitted D24+ values.
    if values.iter().any(domain_numeric::is_domain_value) {
        // Validate domain admission BEFORE divisor error classification:
        // D24 / D48(0) is a forbidden mixed-domain expression, not an
        // admitted D24 divide-by-zero.
        let admitted_operands = match values {
            [single] => domain_numeric::is_domain_value(single),
            [lhs, rhs] if argument_count == 2 =>
                domain_numeric::compare("=", lhs, rhs).is_some(),
            _ => false,
        };
        if !admitted_operands {
            return Err(LanguageError::new(
                ErrorKind::Type, "numeric division requires admitted same-Dn values", span,
            ));
        }
        let denominator_is_zero = match values {
            [_] => matches!(&values[0], Value::BinaryNumber(n) if n.is_zero()),
            [_, rhs] => matches!(rhs, Value::BinaryNumber(n) if n.is_zero()),
            _ => false,
        };
        if denominator_is_zero { return Err(division_error(span)); }
        let result = match values {
            [single] => domain_numeric::unary("/", single),
            [lhs, rhs] if argument_count == 2 => domain_numeric::compute("/", lhs, rhs),
            _ => None,
        }.ok_or_else(|| LanguageError::new(
            ErrorKind::Type,
            "Dn rational division requires exactly two same-domain inputs or unary reciprocal",
            span,
        ))?;
        let bit_length = match &result {
            Value::BinaryNumber(n) => n.width(),
            Value::NumericComposition(n) => {
                let (_, num, den) = n.as_parts();
                num.width().max(den.map_or(0, BinaryNumber::width))
            }
            _ => return Err(LanguageError::new(ErrorKind::Type, "numeric composite invariant", span)),
        };
        if environment.numeric_bit_limit().is_some_and(|limit| bit_length > limit) {
            return Err(arithmetic_overflow(span));
        }
        return Ok(result);
    }

    // Binary Number division is exact on naturals. Non-integral quotients
    // cannot silently become a host Rational until a canonical binary
    // rational layout is ratified (#3021).
    if values.iter().any(|value| matches!(value, Value::BinaryNumber(_))) {
        let numbers = values
            .iter()
            .map(|value| match value {
                Value::BinaryNumber(number) => Ok(number),
                _ => Err(LanguageError::new(
                    ErrorKind::Type,
                    "binary Number does not implicitly coerce legacy numeric values",
                    span,
                )),
            })
            .collect::<Result<Vec<&BinaryNumber>, _>>()?;

        if numbers.iter().any(|number| number.numeric_domain_width().is_some()) {
            if argument_count != 2 || numbers.len() != 2
                || numbers[0].numeric_domain_width().is_none()
                || numbers[0].numeric_domain_width() != numbers[1].numeric_domain_width()
            {
                return Err(LanguageError::new(
                    ErrorKind::Type,
                    "qualified numeric division requires two operands in the same Dn",
                    span,
                ));
            }
            if numbers[1].is_zero() {
                return Err(division_error(span));
            }
            let (quotient, remainder) = numbers[0].div_rem_admitted_numeric(numbers[1])
                .ok_or_else(|| LanguageError::new(
                    ErrorKind::Type, "numeric domain division failed closed", span,
                ))?;
            if !remainder.is_zero() {
                // Canonical reduced RATIO is a ratified *mathematical*
                // composition, but it has no admitted executable/wire codec.
                return Err(LanguageError::new(
                    ErrorKind::Type,
                    "non-integral Dn division requires canonical RATIO composition, not rounding",
                    span,
                ));
            }
            if environment.numeric_bit_limit().is_some_and(|limit| quotient.width() > limit) {
                return Err(arithmetic_overflow(span));
            }
            return Ok(Value::BinaryNumber(quotient));
        }
        let mut result = if argument_count == 1 {
            BinaryNumber::one()
        } else {
            (*numbers[0]).clone()
        };
        let divisors = if argument_count == 1 {
            &numbers[..]
        } else {
            &numbers[1..]
        };
        for &divisor in divisors {
            let (quotient, remainder) = result
                .div_rem(divisor)
                .ok_or_else(|| division_error(span))?;
            if !remainder.is_zero() {
                return Err(LanguageError::new(
                    ErrorKind::Type,
                    "fractional binary Number requires an unratified rational encoding",
                    span,
                ));
            }
            result = quotient;
        }
        if environment
            .numeric_bit_limit()
            .is_some_and(|limit| result.width() > limit)
        {
            return Err(arithmetic_overflow(span));
        }
        return Ok(Value::BinaryNumber(result));
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
    // Numeric order/equality is mathematical. D3 EQ is a distinct identity
    // law, and does not pass through this arithmetic admission gate.
    require_math_domain(values, span)?;
    if values.iter().any(domain_numeric::is_domain_value) {
        let holds = match values {
            [left, right] => domain_numeric::compare(operator, left, right),
            _ => None,
        }.ok_or_else(|| LanguageError::new(
            ErrorKind::Type, "Dn comparison requires exactly two same-domain numeric values", span,
        ))?;
        return Ok(Value::predicate_bit(holds));
    }
    // #3022 comparisons over canonical Number return the exact D1
    // PredicateBit domain, not legacy numeric 0/1 and not a host bool.
    if values.iter().any(|value| matches!(value, Value::BinaryNumber(_))) {
        let numbers = values
            .iter()
            .map(|value| match value {
                Value::BinaryNumber(number) => Ok(number),
                _ => Err(LanguageError::new(
                    ErrorKind::Type,
                    "binary Number comparison does not implicitly coerce legacy numeric values",
                    span,
                )),
            })
            .collect::<Result<Vec<&BinaryNumber>, _>>()?;

        if numbers.iter().any(|number| number.numeric_domain_width().is_some()) {
            let width = numbers.first().and_then(|number| number.numeric_domain_width());
            if width.is_none() || numbers.iter().any(|number| number.numeric_domain_width() != width) {
                return Err(LanguageError::new(
                    ErrorKind::Type,
                    "cross-domain or unqualified numeric comparison is not admitted",
                    span,
                ));
            }
        }
        let holds = numbers.windows(2).all(|pair| match operator {
            "<" => pair[0] < pair[1],
            ">" => pair[0] > pair[1],
            "=" => pair[0] == pair[1],
            _ => unreachable!("known comparison operator"),
        });
        return Ok(Value::predicate_bit(holds));
    }

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
        // #1716/#1826: the comparison predicate has no exact D1 answer once
        // any operand is inexact. Do not collapse unknown to NO/EMPTY and do
        // not manufacture a host/numeric truth carrier.
        return Err(LanguageError::new(
            ErrorKind::Type,
            format!(
                "{operator} requires exact numeric operands to produce D1 PredicateBit"
            ),
            span,
        ));
    }

    let holds = numerics
        .windows(2)
        .all(|pair| compare(operator, pair[0].to_exact(), pair[1].to_exact()));

    // #1716/#1826: exact-Q decides whether the predicate may answer; the
    // answer itself belongs to the exact one-bit predicate domain.
    Ok(Value::predicate_bit(holds))
}

#[cfg(test)]
mod qualified_numeric_domain_value_tests {
    use super::*;

    #[test]
    fn binary_code_domains_and_unqualified_numbers_are_never_math_operands() {
        let env = Environment::root();
        let words = [
            crate::BinarySourceWord::W1(crate::Bit1::new(1).unwrap()),
            crate::BinarySourceWord::W2(crate::Bit2::new(1).unwrap()),
            crate::BinarySourceWord::W3(crate::Bit3::new(1).unwrap()),
            crate::BinarySourceWord::W4(crate::Bit4::new(1).unwrap()),
            crate::BinarySourceWord::W5(crate::Bit5::new(1).unwrap()),
            crate::BinarySourceWord::W6(crate::Bit6::new(1).unwrap()),
            crate::BinarySourceWord::W7(crate::Bit7::new(1).unwrap()),
            crate::BinarySourceWord::W8(crate::Bit8::new(1).unwrap()),
            crate::BinarySourceWord::W9(crate::Bit9::new(1).unwrap()),
        ];
        for word in words {
            let identity = crate::DomainIdentity::from_source_word(word);
            let value = Value::DomainIdentity(identity);
            for op in ["+", "-", "*"] {
                assert_eq!(
                    arithmetic_on_values(op, &[value.clone(), value.clone()], &env, Span::default())
                        .unwrap_err().kind,
                    ErrorKind::Type,
                    "D{} is not an arithmetic operand", identity.width()
                );
            }
            assert_eq!(division_on_values(&[value.clone(), value.clone()], 2, &env, Span::default())
                .unwrap_err().kind, ErrorKind::Type);
            for op in ["=", "<", ">"] {
                assert_eq!(comparison_on_values(op, &[value.clone(), value.clone()], Span::default())
                    .unwrap_err().kind, ErrorKind::Type);
            }
        }
        for value in [
            Value::Number(1.0, Exactness::Exact),
            Value::Rational(Rational::integer(1)),
            Value::BinaryNumber(BinaryNumber::one()),
        ] {
            assert_eq!(arithmetic_on_values("+", &[value.clone(), value.clone()], &env, Span::default())
                .unwrap_err().kind, ErrorKind::Type);
            assert_eq!(division_on_values(&[value.clone(), value.clone()], 2, &env, Span::default())
                .unwrap_err().kind, ErrorKind::Type);
            assert_eq!(comparison_on_values("=", &[value.clone(), value], Span::default())
                .unwrap_err().kind, ErrorKind::Type);
        }
        assert_eq!(
            arithmetic_on_values("+", &[], &env, Span::default()).unwrap_err().kind,
            ErrorKind::Type
        );
    }

    fn in_domain(width: usize, bits: Vec<u8>) -> Value {
        Value::BinaryNumber(
            BinaryNumber::from_numeric_domain_bits(width, &bits)
                .expect("exact numeric domain bits"),
        )
    }

    #[test]
    fn core_runtime_adds_d24_values_to_d48_value_and_retains_domain_identity() {
        let max = in_domain(24, vec![1; 24]);
        let env = Environment::root();
        let sum = arithmetic_on_values("+", &[max.clone(), max.clone()], &env, Span::default())
            .expect("same-domain natural ADD");
        let Value::BinaryNumber(ref sum_bits) = sum else {
            panic!("must return an exact domain-qualified numeric Value")
        };
        assert_eq!(sum_bits.numeric_domain_width(), Some(48));
        let full = sum_bits.exact_numeric_domain_bits().unwrap();
        assert_eq!(full.len(), 48);
        assert_eq!(&full[..23], &[0; 23]);
        assert_eq!(full[47], 0);

        let zero = in_domain(24, vec![0; 24]);
        let result = arithmetic_on_values("+", &[zero.clone(), zero], &env, Span::default())
            .unwrap();
        let Value::BinaryNumber(ref same) = result else { panic!("D24 result") };
        assert_eq!(same.numeric_domain_width(), Some(24));
        assert_eq!(same.exact_numeric_domain_bits(), Some(vec![0; 24]));
    }

    #[test]
    fn source_expression_uses_binary_domain_values_without_numeric_literals() {
        // Only the admitted D24 payloads are supplied directly as values.
        // This is the real evaluator path through a named environment binding.
        let mut session = crate::Session::default();
        let max = in_domain(24, vec![1; 24]);
        session.environment.define("a", max.clone());
        session.environment.define("b", max);
        let result = crate::eval_program("(+ a b)", &mut session)
            .expect("Core addition over domain-qualified values").value;
        let Value::BinaryNumber(ref value) = result else {
            panic!("domain-qualified Value expected")
        };
        assert_eq!(value.numeric_domain_width(), Some(48));
        assert_eq!(value.exact_numeric_domain_bits().unwrap().len(), 48);
    }

    #[test]
    fn core_runtime_exact_d24_natural_mul_sub_div_without_literals() {
        let mut session = crate::Session::default();
        let make = |number: u32| {
            let mut bits = vec![0u8;24];
            for i in 0..24 { bits[23-i] = ((number>>i)&1) as u8; }
            in_domain(24,bits)
        };
        session.environment.define("a", make(6));
        session.environment.define("b", make(2));
        for (expr, expected) in [
            ("(* a b)", 12),
            ("(- a b)", 4),
            ("(/ a b)", 3),
        ] {
            let result = crate::eval_program(expr, &mut session)
                .expect("same-D24 natural arithmetic").value;
            let Value::BinaryNumber(ref bits) = result else { panic!("numeric D24 Value") };
            assert_eq!(bits.numeric_domain_width(), Some(24), "{expr}");
            assert_eq!(bits.to_decimal_string(), expected.to_string(), "{expr}");
        }
        session.environment.define("a", make(1));
        session.environment.define("b", make(3));
        let minus = crate::eval_program("(- a b)", &mut session).unwrap().value;
        assert_eq!(minus.to_string(), "-2");
        let fraction = crate::eval_program("(/ a b)", &mut session).unwrap().value;
        assert_eq!(fraction.to_string(), "1/3");
        session.environment.define("negative", minus);
        session.environment.define("fraction", fraction);
        assert_eq!(crate::eval_program("(+ negative b)", &mut session).unwrap().value, make(1));
        assert_eq!(crate::eval_program("(* fraction b)", &mut session).unwrap().value, make(1));
        session.environment.define("b", make(0));
        let err = crate::eval_program("(/ a b)", &mut session)
            .expect_err("divide by zero must fail");
        assert_eq!(err.kind, ErrorKind::DivisionByZero);
    }

    #[test]
    fn core_runtime_d24_full_multiplication_produces_exact_d48() {
        let env = Environment::root();
        let max = in_domain(24, vec![1;24]);
        let result = arithmetic_on_values("*", &[max.clone(),max], &env, Span::default()).unwrap();
        let Value::BinaryNumber(ref bits) = result else { panic!("numeric D48 Value") };
        assert_eq!(bits.numeric_domain_width(), Some(48));
        assert_eq!(bits.width(), 48);
        assert_eq!(bits.exact_numeric_domain_bits().unwrap().len(), 48);
    }

    #[test]
    fn core_runtime_rejects_unadmitted_numeric_domain_operations() {
        let env = Environment::root();
        let d24 = in_domain(24, vec![0; 24]);
        let d48 = in_domain(48, vec![0; 48]);
        for values in [
            vec![d24.clone(), d48.clone()],
            vec![d24.clone(), Value::BinaryNumber(BinaryNumber::one())],
        ] {
            let e = arithmetic_on_values("+", &values, &env, Span::default()).unwrap_err();
            assert_eq!(e.kind, ErrorKind::Type);
            let cmp = comparison_on_values("=", &values, Span::default()).unwrap_err();
            assert_eq!(cmp.kind, ErrorKind::Type);
        }
        for op in ["*", "-", "+"] {
            let e = arithmetic_on_values(op, &[d24.clone(), d48.clone()], &env, Span::default()).unwrap_err();
            assert_eq!(e.kind, ErrorKind::Type);
        }
        let e = division_on_values(&[d24.clone(), d48.clone()], 2, &env, Span::default()).unwrap_err();
        assert_eq!(e.kind, ErrorKind::Type);
        let e = arithmetic_on_values("+", &[d24], &env, Span::default()).unwrap_err();
        assert_eq!(e.kind, ErrorKind::Type);
    }
}
