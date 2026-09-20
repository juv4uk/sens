//! REPL implementation projection for the Lisp-owned INVOKE semantic identity.
//!
//! This module is a host-side adapter only. The semantic identity is resolved
//! by the core registry and registered here by opaque SID; this code does not
//! define or renumber semantic identities.
//!
//! The first REPL slice intentionally uses the four real-kernel witness
//! contexts already proven by the archipelago tests. Each call returns an
//! explicit Lisp data projection of native producer bytes/observations rather
//! than pretending there is one universal kernel result type.

use my_lisp::{
    register_semantic_capability, ErrorKind, Environment, Expr, ExprKind, LanguageError, Span,
    Value,
};
use std::fs;
use std::path::PathBuf;
use std::rc::Rc;
use std::time::{SystemTime, UNIX_EPOCH};

use wsm_clips_kernel::ClipsKernel;
use wsm_common_lisp_kernel::{CommonLispKernel, CommonLispRequest};
use wsm_datalog_kernel::{
    Atom, Database, Evaluator, Program, Rule, Term, Value as DatalogValue,
};
use wsm_prolog_kernel::{PrologKernel, PrologQuery, PrologRequest};

fn language_error(kind: ErrorKind, message: impl Into<String>, span: Span) -> LanguageError {
    LanguageError::new(kind, format!("invoke: {}", message.into()), span)
}

fn quoted_or_plain_symbol(expr: &Expr, span: Span) -> Result<String, LanguageError> {
    match &expr.kind {
        ExprKind::Symbol(name) => Ok(name.to_string()),
        ExprKind::List(items)
            if items.len() == 2
                && matches!(&items[0].kind, ExprKind::Symbol(name) if &**name == "quote")
                && matches!(&items[1].kind, ExprKind::Symbol(_)) =>
        {
            match &items[1].kind {
                ExprKind::Symbol(name) => Ok(name.to_string()),
                _ => unreachable!("guard above proves Symbol"),
            }
        }
        _ => Err(language_error(
            ErrorKind::Type,
            "first argument must be a kernel symbol or quoted kernel symbol",
            span,
        )),
    }
}

fn string_argument(expr: &Expr, span: Span) -> Result<String, LanguageError> {
    match &expr.kind {
        ExprKind::String(value) => Ok(value.to_string()),
        _ => Err(language_error(
            ErrorKind::Type,
            "second argument must be a native payload string",
            span,
        )),
    }
}

fn invoke_result(producer: &str, payload: &[u8]) -> Value {
    let text = String::from_utf8_lossy(payload)
        .trim_end_matches(['\r', '\n'])
        .to_string();
    Value::list([
        Value::Symbol(Rc::from("invoke-result")),
        Value::Symbol(Rc::from(producer)),
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
        if start.is_some() {
            let end = index;
            return Some(goal[start.unwrap()..end].to_string());
        }
    }
    start.map(|index| goal[index..].to_string())
}

fn prolog_fixture_path() -> Result<PathBuf, LanguageError> {
    let stamp = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map_err(|error| language_error(ErrorKind::MechanismUnavailable, format!("cannot create Prolog fixture timestamp: {error}"), Span::default()))?
        .as_nanos();
    let path = std::env::temp_dir().join(format!("my-lisp-invoke-prolog-{stamp}.pl"));
    let program = r#"
parent(alice,bob).
parent(alice,carol).
parent(bob,dave).

ancestor(X,Y) :- parent(X,Y).
ancestor(X,Z) :- parent(X,Y), ancestor(Y,Z).
"#;
    fs::write(&path, program).map_err(|error| {
        language_error(
            ErrorKind::MechanismUnavailable,
            format!("cannot materialize bounded Prolog witness: {error}"),
            Span::default(),
        )
    })?;
    Ok(path)
}

fn invoke_common_lisp(payload: &str) -> Result<Vec<u8>, String> {
    CommonLispKernel::default()
        .evaluate(&CommonLispRequest::new(0b1010_1000, payload))
        .map(|result| result.stdout)
        .map_err(|error| error.to_string())
}

fn invoke_prolog(payload: &str) -> Result<Vec<u8>, String> {
    let template = first_prolog_template(payload).unwrap_or_else(|| "true".to_string());
    let program = prolog_fixture_path().map_err(|error| error.message)?;
    let result = PrologKernel::default().execute(
        &program,
        &PrologRequest::new(
            0b1010_1000,
            PrologQuery::new(payload, template),
        ),
    );
    let _ = fs::remove_file(&program);
    result.map(|result| result.stdout).map_err(|error| error.to_string())
}

fn invoke_clips(payload: &str) -> Result<Vec<u8>, String> {
    if payload.trim() != "run" {
        return Err("CLIPS bounded REPL witness accepts only the native payload \"run\"".to_string());
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
        return Err("Datalog bounded REPL witness accepts only the relation payload \"path\"".to_string());
    }
    let db = datalog_fixture();
    Ok(datalog_relation_bytes(&db, payload.trim()))
}

fn evaluate_invoke(
    arguments: &[Expr],
    _environment: &Environment,
    span: Span,
) -> Result<Value, LanguageError> {
    if arguments.len() != 2 {
        return Err(language_error(
            ErrorKind::Arity,
            format!("expected 2 arguments, received {}", arguments.len()),
            span,
        ));
    }

    let kernel = quoted_or_plain_symbol(&arguments[0], span)?;
    let payload = string_argument(&arguments[1], span)?;

    let (producer, bytes) = match kernel.as_str() {
        "common-lisp" => ("common-lisp", invoke_common_lisp(&payload)),
        "prolog" => ("prolog", invoke_prolog(&payload)),
        "clips" => ("clips", invoke_clips(&payload)),
        "datalog" => ("datalog", invoke_datalog(&payload)),
        other => {
            return Err(language_error(
                ErrorKind::MechanismUnavailable,
                format!("unsupported kernel: {other}"),
                span,
            ))
        }
    }
    .map_err(|error| {
        language_error(
            ErrorKind::MechanismUnavailable,
            format!("{producer} kernel invocation failed: {error}"),
            span,
        )
    })?;

    Ok(invoke_result(producer, &bytes))
}

/// Install the implementation projection for the Lisp-owned invoke identity.
///
/// The SID is discovered from the canonical registry projection, never
/// hard-coded as an authority in this module.
pub fn install() {
    let semantic_id = my_lisp::semantic_registry_export::semantic_id_for_admitted_surface("invoke")
        .expect("semantic registry must admit invoke");
    register_semantic_capability(semantic_id, evaluate_invoke);
}
