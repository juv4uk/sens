//! Current exact D12+ mathematical operations. D1–D10 words, host numeric
//! literals, legacy Number/Rational and unqualified BinaryNumber are never
//! admitted arithmetic operands. The legacy value projection helper remains
//! only for independent non-mathematical readers (e.g. JSON).
use crate::domain_numeric;
use crate::{Environment, ErrorKind, Exactness, LanguageError, Rational, Span, Value};

/// Legacy data/presentation bridge, NOT a mathematical operand admission.
/// Existing JSON decoding uses this conversion independently of Core math.
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

fn division_error(span: Span) -> LanguageError {
    LanguageError::new(
        ErrorKind::DivisionByZero,
        "division by zero · dilennia na nul · Division durch null",
        span,
    )
}

/// Only explicit numeric D12/D24/D48/... values admit Core mathematical operations.
/// Reader literals and host/Rust Number remain representable as data, not math.
fn require_math_domain(values: &[Value], span: Span) -> Result<(), LanguageError> {
    const REASON: &str =
        "math requires explicit D12+ operands; D1-D10 bit words and unqualified numbers are not arithmetic values";
    if values.is_empty() {
        return Err(LanguageError::new(ErrorKind::Type, REASON, span));
    }
    if let Some((index, rejected)) = values
        .iter()
        .enumerate()
        .find(|(_, value)| !domain_numeric::is_domain_value(value))
    {
        // Діагностувати справжній зламаний операнд, а не маскувати RED:
        // жодного допуску Number/Rational чи перетворення D1–D10 на число.
        let kind = match rejected {
            Value::Number(..) => "legacy-number",
            Value::Rational(..) => "unqualified-rational",
            Value::BinaryNumber(..) => "non-D12-binary",
            Value::DomainIdentity(..) => "domain-word",
            Value::Nil => "structural-empty",
            _ => "non-numeric",
        };
        return Err(LanguageError::new(
            ErrorKind::Type,
            format!(
                "{REASON}; operand_position={} actual_kind={kind}",
                index + 1
            ),
            span,
        ));
    }
    Ok(())
}

fn exact_domain_result_width(result: &Value, span: Span) -> Result<usize, LanguageError> {
    // Resource limits count the admitted full-width Dn result, not its
    // normalized magnitude. D48:1 still occupies an exact D48 identity.
    // The same rule applies to reduced fractions with small constituents.
    match result {
        Value::BinaryNumber(number) => number.numeric_domain_width().ok_or_else(|| {
            LanguageError::new(ErrorKind::Type, "numeric result lacks explicit Dn", span)
        }),
        Value::NumericComposition(composition) => Ok(composition.domain_width()),
        _ => Err(LanguageError::new(
            ErrorKind::Type,
            "numeric composite invariant",
            span,
        )),
    }
}

fn check_domain_result_limit(
    result: &Value,
    environment: &Environment,
    span: Span,
) -> Result<(), LanguageError> {
    let bit_length = exact_domain_result_width(result, span)?;
    if environment
        .numeric_bit_limit()
        .is_some_and(|limit| bit_length > limit)
    {
        return Err(arithmetic_overflow(span));
    }
    Ok(())
}

/// No literal/legacy fallback: one admitted D12+ arithmetic execution path.
pub(super) fn arithmetic_on_values(
    operator: &str,
    values: &[Value],
    environment: &Environment,
    span: Span,
) -> Result<Value, LanguageError> {
    require_math_domain(values, span)?;
    let result = match values {
        [single] if operator == "-" => domain_numeric::unary("-", single),
        [left, right] => domain_numeric::compute(operator, left, right),
        _ => None,
    }
    .ok_or_else(|| {
        LanguageError::new(
            ErrorKind::Type,
            "numeric Dn composition requires same-domain operands and a supported operation",
            span,
        )
    })?;
    check_domain_result_limit(&result, environment, span)?;
    Ok(result)
}

/// D12+ reciprocal and exact rational division, never legacy float/Rational.
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
    // An arithmetic Dn / D(2n) operand pair is invalid *before*
    // checking for division by zero (which needs an admitted division).
    let admitted_operands = match values {
        [single] => domain_numeric::is_domain_value(single),
        // Domain admission is an exact-width identity check, not a
        // rational equality query. Comparing fractions here would multiply
        // potentially huge numerators before the actual division even starts.
        [lhs, rhs] if argument_count == 2 => {
            domain_numeric::shared_numeric_domain_width(lhs, rhs).is_some()
        }
        _ => false,
    };
    if !admitted_operands {
        return Err(LanguageError::new(
            ErrorKind::Type,
            "numeric division requires admitted same-Dn values",
            span,
        ));
    }
    let denominator_is_zero = match values {
        [single] => matches!(single, Value::BinaryNumber(n) if n.is_zero()),
        [_, rhs] => matches!(rhs, Value::BinaryNumber(n) if n.is_zero()),
        _ => false,
    };
    if denominator_is_zero {
        return Err(division_error(span));
    }
    let result = match values {
        [single] => domain_numeric::unary("/", single),
        [lhs, rhs] if argument_count == 2 => domain_numeric::compute("/", lhs, rhs),
        _ => None,
    }
    .ok_or_else(|| {
        LanguageError::new(
            ErrorKind::Type,
            "Dn rational division requires exactly two same-domain inputs or unary reciprocal",
            span,
        )
    })?;
    check_domain_result_limit(&result, environment, span)?;
    Ok(result)
}

/// Numeric order is D12+ only. D3 EQ remains a distinct identity law.
pub(super) fn comparison_on_values(
    operator: &str,
    values: &[Value],
    span: Span,
) -> Result<Value, LanguageError> {
    require_math_domain(values, span)?;
    let holds = match values {
        [left, right] => domain_numeric::compare(operator, left, right),
        _ => None,
    }
    .ok_or_else(|| {
        LanguageError::new(
            ErrorKind::Type,
            "Dn comparison requires exactly two same-domain numeric values",
            span,
        )
    })?;
    Ok(Value::predicate_bit(holds))
}
