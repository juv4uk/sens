use sens::{
    eval_expr, exact_arity, Environment, ErrorKind, Exactness, Expr, LanguageError, Span, Value,
};
use std::rc::Rc;

fn bytes_to_value(bytes: &[u8]) -> Value {
    Value::list(
        bytes
            .iter()
            .map(|byte| Value::Number(*byte as f64, Exactness::Exact)),
    )
}

fn expect_string_list(value: &Value, span: Span) -> Result<Vec<String>, LanguageError> {
    let mut items = Vec::new();
    let mut current = value;
    loop {
        match current {
            Value::Nil => return Ok(items),
            Value::Pair(head, tail) => {
                let Value::String(ref text) = **head else {
                    return Err(LanguageError::new(
                        ErrorKind::Type,
                        "process-run-raw expects a list of strings for its second argument · process-run-raw ochikuie spysok riadkiv druhym arhumentom · process-run-raw erwartet eine Liste von Zeichenketten als zweites Argument",
                        span,
                    ));
                };
                items.push(text.to_string());
                current = tail;
            }
            _ => {
                return Err(LanguageError::new(
                    ErrorKind::Type,
                    "process-run-raw expects a proper list of strings for its second argument · process-run-raw ochikuie pravylnyi spysok riadkiv druhym arhumentom · process-run-raw erwartet eine echte Liste von Zeichenketten als zweites Argument",
                    span,
                ))
            }
        }
    }
}

#[cfg(not(target_arch = "wasm32"))]
fn process_run(
    program: &str,
    args: &[String],
    span: Span,
) -> Result<std::process::Output, LanguageError> {
    std::process::Command::new(program)
        .args(args)
        .output()
        .map_err(|error| {
            LanguageError::new(
                ErrorKind::InvalidForm,
                format!("process-run-raw: failed to run {program}: {error}"),
                span,
            )
        })
}

#[cfg(target_arch = "wasm32")]
fn process_run(
    _program: &str,
    _args: &[String],
    span: Span,
) -> Result<std::process::Output, LanguageError> {
    Err(LanguageError::new(
        ErrorKind::InvalidForm,
        "process-run-raw: process execution is not available in this build",
        span,
    ))
}

/// `(process-run-raw program args)` runs one host process and returns the
/// transport observation without interpreting stdout/stderr as text:
///
///   (process-result exit-code-or-() stdout-bytes stderr-bytes)
///
/// Process selection and allowlisting remain host capability policy. Text
/// decoding belongs to the language layer (`lib/utf8.lisp`).
pub(super) fn evaluate_process_run_raw(
    arguments: &[Expr],
    environment: &Environment,
    span: Span,
) -> Result<Value, LanguageError> {
    exact_arity("process-run-raw", arguments, 2, span)?;
    let program_value = eval_expr(&arguments[0], environment)?;
    let Value::String(ref program) = program_value else {
        return Err(LanguageError::new(
            ErrorKind::Type,
            "process-run-raw expects a string program name · process-run-raw ochikuie riadok-imia prohramy · process-run-raw erwartet einen String-Programmnamen",
            arguments[0].span,
        ));
    };
    if !environment.is_process_allowed(program) {
        return Err(LanguageError::new(
            ErrorKind::InvalidForm,
            format!("process-run-raw: {program} is not on this session's allowlist · process-run-raw: {program} nemaie v allowlist tsiiei sesii · process-run-raw: {program} steht nicht auf der Allowlist dieser Sitzung"),
            span,
        ));
    }

    let args_value = eval_expr(&arguments[1], environment)?;
    let args = expect_string_list(&args_value, arguments[1].span)?;
    let output = process_run(program, &args, span)?;

    let exit_code = output
        .status
        .code()
        .map(|code| Value::Number(code as f64, Exactness::Exact))
        .unwrap_or(Value::Nil);

    Ok(Value::list([
        Value::Symbol(Rc::from("process-result")),
        exit_code,
        bytes_to_value(&output.stdout),
        bytes_to_value(&output.stderr),
    ]))
}
