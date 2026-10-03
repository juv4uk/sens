use sens::{
    parse, render_value_for_presentation, Exactness, Expr, ExprKind, PresentationLanguage,
    Rational, Value,
};
use std::{env, fs, hint::black_box, path::PathBuf};

const DOMAIN: &str = "Core-Math-QGroupFactor";

#[derive(Clone, Debug, Eq, PartialEq)]
struct QOp {
    bits: Box<str>,
}

impl QOp {
    fn lower(bits: &str) -> Result<Self, String> {
        if !(bits.len() == 1 || bits.len() == 2)
            || !bits.bytes().all(|b| matches!(b, b'0' | b'1'))
        {
            return Err(format!("invalid Q-group operation bits: {bits}"));
        }
        Ok(Self { bits: bits.into() })
    }

    fn root(&self) -> u8 {
        self.bits.as_bytes()[0] - b'0'
    }

    fn role(&self) -> Option<u8> {
        (self.bits.len() == 2).then(|| self.bits.as_bytes()[1] - b'0')
    }
}

#[derive(Clone, Debug)]
struct Case {
    op: QOp,
    args: Vec<Rational>,
}

#[derive(Clone, Debug, Eq, PartialEq)]
enum Outcome {
    Value(Rational),
    UndefinedMathematically,
}

fn derive_child(root: &str, role: char) -> String {
    assert!(matches!(root, "0" | "1"));
    assert!(matches!(role, '0' | '1'));
    format!("{root}{role}")
}

fn exact_arg(expr: &Expr) -> Result<Rational, String> {
    match &expr.kind {
        ExprKind::Rational(value) => Ok(value.clone()),
        ExprKind::Number(value, Exactness::Exact)
            if value.is_finite()
                && value.fract() == 0.0
                && *value >= i64::MIN as f64
                && *value <= i64::MAX as f64 =>
        {
            Ok(Rational::integer(*value as i64))
        }
        other => Err(format!("expected exact rational argument, got {other:?}")),
    }
}

fn lower_program(source: &str) -> Result<Vec<Case>, String> {
    let forms = parse(source).map_err(|e| e.render(source))?;
    let mut cases = Vec::with_capacity(forms.len());

    for form in forms {
        let ExprKind::List(items) = form.kind else {
            return Err("top-level arithmetic case must be a list".into());
        };
        if items.len() < 2 {
            return Err("arithmetic case requires operation bits and arguments".into());
        }
        let ExprKind::String(bits) = &items[0].kind else {
            return Err("operation coordinate must be a width-preserving source string".into());
        };
        let op = QOp::lower(bits)?;
        let args = items[1..]
            .iter()
            .map(exact_arg)
            .collect::<Result<Vec<_>, _>>()?;
        cases.push(Case { op, args });
    }

    Ok(cases)
}

fn combine(root: u8, left: Rational, right: Rational) -> Result<Rational, String> {
    match root {
        0 => left
            .checked_add(right)
            .ok_or_else(|| "exact additive operation failed".to_string()),
        1 => left
            .checked_mul(right)
            .ok_or_else(|| "exact multiplicative operation failed".to_string()),
        _ => Err("unknown Q-group family root".into()),
    }
}

fn inverse(root: u8, value: Rational) -> Result<Outcome, String> {
    match root {
        0 => value
            .checked_neg()
            .map(Outcome::Value)
            .ok_or_else(|| "exact additive inverse failed".to_string()),
        1 => match Rational::integer(1).checked_div(value) {
            Some(value) => Ok(Outcome::Value(value)),
            None => Ok(Outcome::UndefinedMathematically),
        },
        _ => Err("unknown Q-group family root".into()),
    }
}

fn execute_factorized(case: &Case) -> Result<Outcome, String> {
    let root = case.op.root();
    match case.op.role() {
        None => {
            if case.args.len() != 2 {
                return Err("family operation expects two arguments".into());
            }
            combine(root, case.args[0].clone(), case.args[1].clone()).map(Outcome::Value)
        }
        Some(0) => {
            if case.args.len() != 1 {
                return Err("inverse role expects one argument".into());
            }
            inverse(root, case.args[0].clone())
        }
        Some(1) => {
            if case.args.len() != 2 {
                return Err("quotient role expects two arguments".into());
            }
            let rhs_inverse = inverse(root, case.args[1].clone())?;
            match rhs_inverse {
                Outcome::UndefinedMathematically => Ok(Outcome::UndefinedMathematically),
                Outcome::Value(rhs) => {
                    combine(root, case.args[0].clone(), rhs).map(Outcome::Value)
                }
            }
        }
        Some(_) => unreachable!(),
    }
}

// Deliberately flat six-operation control.  This is the architecture #2698
// compares against; it is not semantic authority for factorized execution.
fn execute_six_table(case: &Case) -> Result<Outcome, String> {
    match case.op.bits.as_ref() {
        "0" => {
            if case.args.len() != 2 {
                return Err("ADD control arity".into());
            }
            case.args[0]
                .clone()
                .checked_add(case.args[1].clone())
                .map(Outcome::Value)
                .ok_or_else(|| "ADD control failed".into())
        }
        "1" => {
            if case.args.len() != 2 {
                return Err("MUL control arity".into());
            }
            case.args[0]
                .clone()
                .checked_mul(case.args[1].clone())
                .map(Outcome::Value)
                .ok_or_else(|| "MUL control failed".into())
        }
        "00" => {
            if case.args.len() != 1 {
                return Err("NEG control arity".into());
            }
            case.args[0]
                .clone()
                .checked_neg()
                .map(Outcome::Value)
                .ok_or_else(|| "NEG control failed".into())
        }
        "01" => {
            if case.args.len() != 2 {
                return Err("SUB control arity".into());
            }
            case.args[0]
                .clone()
                .checked_sub(case.args[1].clone())
                .map(Outcome::Value)
                .ok_or_else(|| "SUB control failed".into())
        }
        "10" => {
            if case.args.len() != 1 {
                return Err("RECIP control arity".into());
            }
            match Rational::integer(1).checked_div(case.args[0].clone()) {
                Some(value) => Ok(Outcome::Value(value)),
                None => Ok(Outcome::UndefinedMathematically),
            }
        }
        "11" => {
            if case.args.len() != 2 {
                return Err("DIV control arity".into());
            }
            match case.args[0].clone().checked_div(case.args[1].clone()) {
                Some(value) => Ok(Outcome::Value(value)),
                None => Ok(Outcome::UndefinedMathematically),
            }
        }
        _ => Err("unknown six-table control row".into()),
    }
}

fn render(outcome: &Outcome) -> String {
    match outcome {
        Outcome::Value(value) => render_value_for_presentation(
            &Value::Rational(value.clone()),
            PresentationLanguage::Canonical,
        ),
        Outcome::UndefinedMathematically => "UNDEFINED-MATHEMATICALLY".into(),
    }
}

fn main() -> Result<(), String> {
    let mut args = env::args().skip(1);
    let mode = args.next().ok_or("mode required: factorized|six-table")?;
    let program = PathBuf::from(args.next().ok_or("program path required")?);
    let iterations: usize = args
        .next()
        .unwrap_or_else(|| "1".into())
        .parse()
        .map_err(|_| "iterations must be an integer")?;
    let quiet = args.next().as_deref() == Some("--quiet");

    let source = fs::read_to_string(&program).map_err(|e| e.to_string())?;
    let cases = lower_program(&source)?;

    assert_eq!(derive_child("0", '0'), "00");
    assert_eq!(derive_child("0", '1'), "01");
    assert_eq!(derive_child("1", '0'), "10");
    assert_eq!(derive_child("1", '1'), "11");

    let expected = [
        "5",
        "5/6",
        "-6",
        "1/2",
        "-3",
        "3/2",
        "UNDEFINED-MATHEMATICALLY",
    ];
    if cases.len() != expected.len() {
        return Err(format!("expected {} cases, got {}", expected.len(), cases.len()));
    }

    let executor: fn(&Case) -> Result<Outcome, String> = match mode.as_str() {
        "factorized" => execute_factorized,
        "six-table" => execute_six_table,
        _ => return Err("mode must be factorized or six-table".into()),
    };

    let once = cases
        .iter()
        .map(executor)
        .collect::<Result<Vec<_>, _>>()?;
    for (index, outcome) in once.iter().enumerate() {
        let rendered = render(outcome);
        if rendered != expected[index] {
            return Err(format!(
                "case {index}: expected {}, got {rendered}",
                expected[index]
            ));
        }
        if !quiet {
            println!(
                "CASE={index}	DOMAIN={DOMAIN}	BITS={}	RESULT={rendered}",
                cases[index].op.bits
            );
        }
    }

    let mut checksum = 0usize;
    for _ in 0..iterations {
        for case in &cases {
            let outcome = black_box(executor(black_box(case))?);
            checksum = checksum.wrapping_add(match outcome {
                Outcome::Value(value) => value.bit_length(),
                Outcome::UndefinedMathematically => 1,
            });
        }
    }

    println!("MODE={mode}");
    println!("SOURCE_FORMS={}", cases.len());
    println!("RUNTIME_TEXT_NAME_DISPATCH=0");
    println!("PER_RESULT_LOOKUP_ROWS_FACTOR_EXECUTOR=0");
    println!("GENERATED_COORDINATES=00,01,10,11");
    println!("D5_D6_ALLOCATIONS=0");
    println!("CHECKSUM={checksum}");
    Ok(())
}
