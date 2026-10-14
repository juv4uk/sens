//! Explicit diagnostic: physically decoded T5 narrator evaluated against
//! existing SENS-owned self-verdict/one-bit mutant, in the REAL reason environment.
//! This runner is transport only and does not grant D9 callable admission.

use sens::{
    eval_parsed_expressions, load_core_library, parse_mixed_exact_domain,
    parse_mixed_exact_domain_reasoning_source, PhysicalT5Program, Session,
};
use std::{env, fs, process::ExitCode};

const LAW: &str = include_str!("../../../tests/fixtures/narrate-d4-bind-law.lisp");
const MUTANT: &str = include_str!("../../../tests/fixtures/narrate-d4-bind-mutant.lisp");

fn evaluate(physical: &[u8], source: &str) -> Result<bool, String> {
    let mut session = Session::default();
    load_core_library(&mut session).map_err(|e| format!("core bootstrap: {e:?}"))?;
    // These are the actual SENS definitions, not a host copy of provenance.
    for (name, code) in [
        ("lib/unify.lisp", include_str!("../../../lib/unify.lisp")),
        ("lib/reason.lisp", include_str!("../../../lib/reason.lisp")),
        ("lib/result-status.lisp", include_str!("../../../lib/result-status.lisp")),
    ] {
        let parsed = parse_mixed_exact_domain_reasoning_source(name, code)
            .map_err(|e| format!("source reader {name}: {e}"))?;
        eval_parsed_expressions(&parsed, &mut session)
            .map_err(|e| format!("SENS definitions {name}: {e}"))?;
    }
    // Cross-file LINK (not semantic implementation): use the exact D7
    // canonical wire key for the *existing SENS-defined* provenance closure.
    // Neither a new function nor a new D9 resident is created.
    let linked = session.environment.get("provenance-list")
        .ok_or("reason.lisp did not DEFINE provenance-list")?;
    let provider_wire = sens::Text7::from_ascii_projection("provenance-list")
        .map_err(|e| format!("ratified D7 provider projection: {e:?}"))?
        .to_canonical_wire_token();
    session.environment.define(provider_wire, linked);

    // Only the physical T5 bytes, never the visible narrator .lisp source,
    // may introduce narrator functions in this test session.
    let program = PhysicalT5Program::decode(physical)
        .map_err(|e| format!("physical narrate decode: {e:?}"))?;
    eprintln!("PHYSICAL_NARRATE_FORMS={}", program.form_count());
    program.execute(&mut session)
        .map_err(|e| format!("physical narrator SENS evaluation: {e}"))?;

    // The EXISTING .lisp SENS-owned self-verdict has human surface spellings;
    // bind those as TEST ADAPTER aliases to the closures just defined by T5.
    // Physical internal calls continue to use their exact D7 wire keys.
    for name in [
        "narrate-answer", "narrate-outcome", "narrate-proper-list?",
        "provenance-derived-from",
    ] {
        let wire = sens::Text7::from_ascii_projection(name)
            .map_err(|e| format!("ratified D7 call-surface projection: {e:?}"))?
            .to_canonical_wire_token();
        let existing = session.environment.get(&wire)
            .ok_or_else(|| format!("T5 never defined lexical Text7 binding for {name}"))?;
        session.environment.define(name, existing);
    }
    let parsed = parse_mixed_exact_domain(source)
        .map_err(|e| format!("SENS self-verdict reader: {e}"))?;
    let observed = eval_parsed_expressions(&parsed, &mut session)
        .map_err(|e| format!("SENS self-verdict evaluator: {e}"))?;
    observed.value.as_predicate_bit()
        .ok_or_else(|| "SENS self-verdict was not a D1 predicate".to_string())
}

fn run() -> Result<(), String> {
    let path = env::args().nth(1).ok_or("usage: probe_linked_narrate_t5 FILE.sens")?;
    if env::args().nth(2).is_some() || !path.ends_with(".sens") {
        return Err("expected one explicitly named physical .sens input".into());
    }
    let physical = fs::read(&path).map_err(|e| format!("physical read: {e}"))?;
    if LAW.len() != MUTANT.len() ||
        LAW.bytes().zip(MUTANT.bytes())
            .filter(|(a, b)| a != b)
            .collect::<Vec<_>>().as_slice() != &[(b'1', b'0')]
    {
        return Err("SENS fixtures are not a single D1:1→D1:0 mutation".into());
    }
    for (label, source, expected) in [
        ("law", LAW, true),
        ("one-bit-mutant", MUTANT, false),
    ] {
        let verdict = evaluate(&physical, source)?;
        eprintln!("PHYSICAL_NARRATE_SENS_VERDICT {label}={verdict}");
        if verdict != expected {
            return Err(format!("physical T5 narrator did not respect SENS-owned {label} verdict"));
        }
    }
    Ok(())
}

fn main() -> ExitCode {
    match run() {
        Ok(()) => {
            println!("PHYSICAL_NARRATE_SENS_LAW_AND_MUTANT=PASS");
            ExitCode::SUCCESS
        }
        Err(error) => {
            eprintln!("PHYSICAL_NARRATE_SENS_LAW_AND_MUTANT=BLOCKED {error}");
            ExitCode::FAILURE
        }
    }
}
