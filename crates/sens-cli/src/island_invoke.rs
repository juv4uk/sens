//! Explicit low-level raw island escape hatch for exact SENS 10101000.
//!
//! SENS owns admission and function identity. This module owns mechanism only:
//! exact SENS -> opaque mechanism selector + native payload -> producer observation.
//! Kernel names and payloads are data at this boundary, never function identities.

use sens::{
    register_sens_capability, Environment, ErrorKind, LanguageError, Sens8, Span, Value,
};
use std::fs;
use std::path::PathBuf;
use std::rc::Rc;
use std::time::{SystemTime, UNIX_EPOCH};

use wsm_clips_kernel::ClipsKernel;
use wsm_common_lisp_kernel::{CommonLispKernel, LegacyAbiSemanticId, LegacyCommonLispRequest};
use wsm_datalog_kernel::{
    Atom, Database, Evaluator, Program, Rule, Term, Value as DatalogValue,
};
use wsm_prolog_kernel::{PrologKernel, PrologQuery, PrologRequest};

const RAW_INVOKE_SENS: Sens8 = sens::sens!(10101000);

fn language_error(kind: ErrorKind, message: impl Into<String>, span: Span) -> LanguageError {
    LanguageError::new(kind, format!("10101000: {}", message.into()), span)
}

fn text_argument(value: &Value, role: &str, span: Span) -> Result<String, LanguageError> {
    match value {
        Value::String(text) => Ok(text.to_string()),
        _ => Err(language_error(
            ErrorKind::Type,
            format!("{role} must be opaque text data"),
            span,
        )),
    }
}

fn native_observation(producer: &str, payload: &[u8]) -> Value {
    let text = String::from_utf8_lossy(payload)
        .trim_end_matches(['\r', '\n'])
        .to_string();
    // All three fields are boundary data. No Rust-authored symbol/tag becomes
    // a new SENS semantic identity.
    Value::list([
        Value::String(Rc::from("island-native-observation")),
        Value::String(Rc::from(producer)),
        Value::String(Rc::from(text)),
    ])
}

fn first_prolog_template(goal: &str) -> Option<String> {
    let bytes = goal.as_bytes();
    let mut start = None;
    for (index, byte) in bytes.iter().enumerate() {
        if byte.is_ascii_uppercase() || *byte == b'_' {
            if start.is_none() {
                start = Some(index);
            }
            continue;
        }
        if let Some(begin) = start {
            return Some(goal[begin..index].to_string());
        }
    }
    start.map(|index| goal[index..].to_string())
}

fn prolog_fixture_path() -> Result<PathBuf, String> {
    let stamp = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map_err(|error| format!("cannot create Prolog fixture timestamp: {error}"))?
        .as_nanos();
    let path = std::env::temp_dir().join(format!("sens-invoke-prolog-{stamp}.pl"));
    let program = r#"
parent(alice,bob).
parent(alice,carol).
parent(bob,dave).

ancestor(X,Y) :- parent(X,Y).
ancestor(X,Z) :- parent(X,Y), ancestor(Y,Z).
"#;
    fs::write(&path, program)
        .map_err(|error| format!("cannot materialize bounded Prolog witness: {error}"))?;
    Ok(path)
}

fn invoke_common_lisp(sens: Sens8, payload: &str) -> Result<Vec<u8>, String> {
    // RAW_INVOKE is an explicit historical low-level escape hatch. Preserve
    // its byte only as ABI compatibility provenance; never infer a Core domain.
    let request = LegacyCommonLispRequest::new(
        LegacyAbiSemanticId(sens.packed_byte()),
        payload,
    );
    CommonLispKernel::default()
        .evaluate_legacy_abi(&request)
        .map(|result| result.stdout)
        .map_err(|error| error.to_string())
}

fn invoke_prolog(sens: Sens8, payload: &str) -> Result<Vec<u8>, String> {
    let template = first_prolog_template(payload).unwrap_or_else(|| "true".to_string());
    let program = prolog_fixture_path()?;
    let result = PrologKernel::default().execute(
        &program,
        &PrologRequest::new(
            sens.packed_byte(),
            PrologQuery::new(payload, template),
        ),
    );
    let _ = fs::remove_file(&program);
    result
        .map(|result| result.stdout)
        .map_err(|error| error.to_string())
}

fn invoke_clips(payload: &str) -> Result<Vec<u8>, String> {
    if payload.trim() != "run" {
        return Err(
            "CLIPS bounded raw-invoke witness accepts only the native payload \"run\"".to_string(),
        );
    }

    let kernel = ClipsKernel::discover().map_err(|error| error.to_string())?;
    let environment = kernel
        .create_environment()
        .map_err(|error| error.to_string())?;
    environment
        .build("(defrule observe-signal (signal) => (assert (observed)))")
        .map_err(|error| error.to_string())?;
    let _fact = environment
        .assert_string("(signal)")
        .map_err(|error| error.to_string())?;
    let fired = environment.run(-1);
    Ok(format!("fired={fired}\n").into_bytes())
}

fn datalog_fixture() -> Database {
    let mut db = Database::new();
    db.add_fact("edge", vec![DatalogValue::int(1), DatalogValue::int(2)]);
    db.add_fact("edge", vec![DatalogValue::int(2), DatalogValue::int(3)]);
    db.add_fact("edge", vec![DatalogValue::int(3), DatalogValue::int(4)]);

    let mut program = Program::new();
    program.add_rule(Rule::with_id(
        "path-base",
        Atom::new("path", vec![Term::v("X"), Term::v("Y")]),
        vec![Atom::new("edge", vec![Term::v("X"), Term::v("Y")])],
    ));
    program.add_rule(Rule::with_id(
        "path-rec",
        Atom::new("path", vec![Term::v("X"), Term::v("Y")]),
        vec![
            Atom::new("edge", vec![Term::v("X"), Term::v("Z")]),
            Atom::new("path", vec![Term::v("Z"), Term::v("Y")]),
        ],
    ));

    Evaluator::semi_naive_fixpoint(&program, &mut db);
    db
}

fn datalog_relation_bytes(db: &Database, relation: &str) -> Vec<u8> {
    let mut tuples: Vec<_> = db.relation(relation).iter().cloned().collect();
    tuples.sort();

    let mut output = String::new();
    for tuple in tuples {
        output.push_str(relation);
        output.push('(');
        for (index, value) in tuple.iter().enumerate() {
            if index != 0 {
                output.push(',');
            }
            match value {
                DatalogValue::Symbol(symbol) => output.push_str(symbol),
                DatalogValue::Int(integer) => output.push_str(&integer.to_string()),
            }
        }
        output.push_str(")\n");
    }
    output.into_bytes()
}

fn invoke_datalog(payload: &str) -> Result<Vec<u8>, String> {
    if payload.trim() != "path" {
        return Err(
            "Datalog bounded raw-invoke witness accepts only the relation payload \"path\""
                .to_string(),
        );
    }
    let db = datalog_fixture();
    Ok(datalog_relation_bytes(&db, payload.trim()))
}

fn evaluate_raw_invoke(
    sens: Sens8,
    arguments: &[Value],
    _environment: &Environment,
    span: Span,
) -> Result<Value, LanguageError> {
    debug_assert_eq!(sens, RAW_INVOKE_SENS);

    if arguments.len() != 2 {
        return Err(language_error(
            ErrorKind::Arity,
            format!("expected 2 arguments, received {}", arguments.len()),
            span,
        ));
    }

    let mechanism = text_argument(&arguments[0], "mechanism selector", span)?;
    let payload = text_argument(&arguments[1], "native payload", span)?;

    let (producer, native_result) = match mechanism.as_str() {
        "common-lisp" => ("common-lisp", invoke_common_lisp(sens, &payload)),
        "prolog" => ("prolog", invoke_prolog(sens, &payload)),
        "clips" => ("clips", invoke_clips(&payload)),
        "datalog" => ("datalog", invoke_datalog(&payload)),
        other => {
            return Err(language_error(
                ErrorKind::MechanismUnavailable,
                format!("unsupported raw island mechanism: {other}"),
                span,
            ))
        }
    };

    let bytes = native_result.map_err(|error| {
        language_error(
            ErrorKind::MechanismUnavailable,
            format!("{producer} mechanism failed: {error}"),
            span,
        )
    })?;

    Ok(native_observation(producer, &bytes))
}

/// Install availability for exactly one already-admitted SENS function.
/// This does not select Core3 and cannot make 10101000 callable under Core4.
pub fn install() {
    register_sens_capability(RAW_INVOKE_SENS, evaluate_raw_invoke);
}
