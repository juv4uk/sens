//! Exercises lib/clips-import.my — Step 1 of a universal-ish importer for
//! old symbolic-AI systems: CLIPS's `deffacts` (facts only, no variables),
//! per PLAN.md's forward-chaining/CLIPS thread and NASA's Johnson Space
//! Center origin of CLIPS itself. Real CLIPS source parses cleanly as
//! ordinary sens data via `read`/`quote` — no dedicated tokenizer or
//! string primitives needed.
//! Pereviriaie lib/clips-import.my — Krok 1 universalnoho(-uvatoho)
//! importera zi starykh symvolnykh AI-system: CLIPS `deffacts` (fakty bez
//! zminnykh). Spravzhnii CLIPS-kod chysto parsytsia yak zvychaini sens dani
//! cherez `read`/`quote` — bez okremoho tokenizatora chy riadkovykh
//! prymityviv.
//! Prüft lib/clips-import.my — Schritt 1 eines universell(-ähnlichen)
//! Importers für alte symbolische KI-Systeme: CLIPS' `deffacts` (Fakten
//! ohne Variablen). Echter CLIPS-Quellcode parst sauber als gewöhnliche
//! sens-Daten über `read`/`quote` — kein eigener Tokenizer oder
//! String-Primitive nötig.

use sens::{eval_program, Session};

fn eval_import(source: &str) -> String {
    let mut session = Session::default();
    eval_program(include_str!("../../../lib/core.lisp"), &mut session).unwrap();
    eval_program(include_str!("../../../lib/unify.lisp"), &mut session).unwrap();
    eval_program(include_str!("../../../lib/reason.lisp"), &mut session).unwrap();
    eval_program(include_str!("../../../lib/forward.lisp"), &mut session).unwrap();
    eval_program(include_str!("../../../lib/knowledge.lisp"), &mut session).unwrap();
    eval_program(include_str!("../../../lib/clips-import.lisp"), &mut session).unwrap();
    eval_program(source, &mut session)
        .unwrap_or_else(|e| panic!("evaluation failed: {e}\nsource: {source}"))
        .value
        .to_string()
}

#[test]
fn clips_deffacts_becomes_zero_condition_clauses() {
    // A real CLIPS `deffacts` block, read as data rather than evaluated.
    let source = r#"
        (clips-import (quote ((deffacts initial-facts (planet earth) (planet mars) (star sun)))))
    "#;
    assert_eq!(
        eval_import(source),
        "(((planet earth)) ((planet mars)) ((star sun)))"
    );
}

#[test]
fn clips_import_skips_unsupported_forms_without_erroring() {
    // deffunction isn't supported (no step covers it) — a mixed file
    // still imports whatever it can, rather than failing the whole import.
    let source = r#"
        (clips-import (quote (
            (deffacts initial-facts (planet earth))
            (deffunction square (?x) (* ?x ?x))
        )))
    "#;
    assert_eq!(eval_import(source), "(((planet earth)))");
}

#[test]
fn clips_defrule_converts_question_mark_variables_to_var_terms() {
    let source = r#"
        (clips-import (quote ((defrule mass-rule (planet ?x) => (assert (has-mass ?x))))))
    "#;
    assert_eq!(
        eval_import(source),
        "(((has-mass (var x)) (planet (var x))))"
    );
}

#[test]
fn clips_defrule_leaves_non_variable_arguments_untouched() {
    // A CLIPS fact argument can be a plain symbol or a number, not just a
    // `?`-prefixed variable — clips-var? must not choke on either.
    let source = r#"
        (clips-import (quote ((defrule hot (temperature 98) => (assert (alert critical))))))
    "#;
    assert_eq!(eval_import(source), "(((alert critical) (temperature 98)))");
}

#[test]
fn clips_defrule_with_multiple_conditions_converts_all_of_them() {
    let source = r#"
        (clips-import (quote ((defrule grandparent-rule
                           (parent ?x ?z) (parent ?z ?y)
                           => (assert (grandparent ?x ?y))))))
    "#;
    assert_eq!(
        eval_import(source),
        "(((grandparent (var x) (var y)) (parent (var x) (var z)) (parent (var z) (var y))))"
    );
}

#[test]
fn clips_defrule_with_no_asserts_imports_as_no_clauses() {
    let source = r#"
        (clips-import (quote ((defrule broken (planet ?x) => (printout t "hello")))))
    "#;
    assert_eq!(eval_import(source), "()");
}

#[test]
fn clips_defrule_strips_a_docstring_before_its_conditions() {
    // Regression: an empty docstring "" right after the rule name used to
    // land in the condition list as a stray, never-matching pattern,
    // silently killing the whole rule.
    let source = r#"
        (clips-import (quote ((defrule mass-rule "explains why planets have mass"
                           (planet ?x) => (assert (has-mass ?x))))))
    "#;
    assert_eq!(
        eval_import(source),
        "(((has-mass (var x)) (planet (var x))))"
    );
}

#[test]
fn clips_defrule_strips_a_declare_salience_before_its_conditions() {
    let source = r#"
        (clips-import (quote ((defrule mass-rule (declare (salience 10))
                           (planet ?x) => (assert (has-mass ?x))))))
    "#;
    assert_eq!(
        eval_import(source),
        "(((has-mass (var x)) (planet (var x))))"
    );
}

#[test]
fn clips_defrule_strips_both_docstring_and_declare_together() {
    let source = r#"
        (clips-import (quote ((defrule mass-rule "docstring" (declare (salience 10))
                           (planet ?x) => (assert (has-mass ?x))))))
    "#;
    assert_eq!(
        eval_import(source),
        "(((has-mass (var x)) (planet (var x))))"
    );
}

#[test]
fn clips_defrule_with_a_multi_fact_assert_produces_one_clause_per_fact() {
    // Real CLIPS assert can take multiple facts in one call:
    // (assert (number 0) (number 1) (number 2)) is one assert, three
    // facts — found on a genuine external .clp file, not guessed.
    let source = r#"
        (clips-import (quote ((defrule init (foo) => (assert (number 0) (number 1) (number 2))))))
    "#;
    assert_eq!(
        eval_import(source),
        "(((number 0) (foo)) ((number 1) (foo)) ((number 2) (foo)))"
    );
}

#[test]
fn clips_defrule_with_multiple_asserts_produces_one_clause_per_assert() {
    // N assertions sharing one LHS become N clauses, each with the same
    // (converted) condition list — logically equivalent to CLIPS firing
    // all N assertions together whenever the shared conditions hold.
    let source = r#"
        (clips-import (quote ((defrule two-asserts (planet ?x) => (assert (a ?x)) (assert (b ?x))))))
    "#;
    assert_eq!(
        eval_import(source),
        "(((a (var x)) (planet (var x))) ((b (var x)) (planet (var x))))"
    );
}

#[test]
fn clips_import_mixes_deffacts_and_defrule_into_one_usable_module() {
    let source = r#"
        (def imported (clips-import (quote (
            (deffacts init (planet earth))
            (defrule mass-rule (planet ?x) => (assert (has-mass ?x)))
        ))))
        (defmodule imported-astro imported)
        (forward-in (quote imported-astro))
    "#;
    assert_eq!(eval_import(source), "((has-mass earth) (planet earth))");
}

#[test]
fn clips_defrule_with_a_not_condition_imports_and_runs_correctly() {
    // Was skipped entirely as of clips-import.my Step 5, back when
    // lib/forward.lisp's match-conditions had no negation-as-failure
    // handling. Step 6 added it (match-one-condition/
    // match-negated-condition), so this now imports normally and derives
    // exactly the right fact: tweety (animal, not penguin) becomes a
    // bird; pingu (a penguin) does not.
    let source = r#"
        (def imported (clips-import (quote (
            (deffacts init (animal tweety) (animal pingu) (penguin pingu))
            (defrule bird-rule (animal ?x) (not? (penguin ?x)) => (assert (bird ?x)))
        ))))
        (defmodule zoo imported)
        (forward-in (quote zoo))
    "#;
    assert_eq!(
        eval_import(source),
        "((bird tweety) (penguin pingu) (animal pingu) (animal tweety))"
    );
}

#[test]
fn clips_defrule_with_printout_alongside_assert_still_imports_the_assert() {
    // Regression: a rule mixing printout (debug output) with assert used
    // to import as no clauses at all, silently dropping a perfectly
    // representable assertion just because printout sat next to it.
    let source = r#"
        (clips-import (quote ((defrule mass-rule (planet ?x)
            => (printout t "found planet " ?x crlf) (assert (has-mass ?x))))))
    "#;
    assert_eq!(
        eval_import(source),
        "(((has-mass (var x)) (planet (var x))))"
    );
}

#[test]
fn clips_defrule_with_retract_still_imports_as_no_clauses() {
    // retract refers to a fact by CLIPS fact-address, a concept this
    // project's set-of-facts model has no equivalent for — still
    // disqualifying, unlike the harmless printout above.
    let source = r#"
        (clips-import (quote ((defrule broken (planet ?x) => (retract ?x) (assert (has-mass ?x))))))
    "#;
    assert_eq!(eval_import(source), "()");
}

#[test]
fn clips_deftemplate_converts_named_slots_to_positional_order() {
    let source = r#"
        (clips-import (quote (
            (deftemplate reading (slot sensor) (slot value))
            (deffacts init (reading (value 98) (sensor probe1)))
        )))
    "#;
    assert_eq!(eval_import(source), "(((reading probe1 98)))");
}

#[test]
fn clips_deftemplate_slot_order_holds_regardless_of_slot_order_in_the_fact() {
    let source = r#"
        (clips-import (quote (
            (deftemplate reading (slot sensor) (slot value))
            (deffacts init (reading (sensor probe1) (value 98)))
        )))
    "#;
    assert_eq!(eval_import(source), "(((reading probe1 98)))");
}

#[test]
fn clips_deftemplate_applies_inside_defrule_conditions_and_conclusions() {
    let source = r#"
        (clips-import (quote (
            (deftemplate reading (slot sensor) (slot value))
            (defrule hot-rule (reading (sensor ?s) (value 98))
                => (assert (alert (sensor ?s))))
            (deftemplate alert (slot sensor))
        )))
    "#;
    assert_eq!(
        eval_import(source),
        "(((alert (var s)) (reading (var s) 98)))"
    );
}

#[test]
fn clips_deftemplate_works_end_to_end_through_forward_in() {
    let source = r#"
        (def imported (clips-import (quote (
            (deftemplate reading (slot sensor) (slot value))
            (deffacts init (reading (sensor probe1) (value 98)))
            (defrule hot-rule (reading (sensor ?s) (value 98)) => (assert (alert ?s)))
        ))))
        (defmodule sensors imported)
        (forward-in (quote sensors))
    "#;
    assert_eq!(eval_import(source), "((alert probe1) (reading probe1 98))");
}

#[test]
fn clips_deftemplate_converts_facts_nested_inside_or() {
    // Regression: clips-convert-template used to recurse through a `not`
    // wrapper only, so a template fact inside `or`/`and` never got its
    // named slots converted to positional form, silently never matching
    // anything.
    let source = r#"
        (def imported (clips-import (quote (
            (deftemplate cat (slot name))
            (deftemplate dog (slot name))
            (deffacts init (cat (name tom)) (dog (name rex)))
            (defrule pet-rule (or (cat (name ?x)) (dog (name ?x))) => (assert (pet ?x)))
        ))))
        (defmodule zoo imported)
        (forward-in (quote zoo))
    "#;
    assert_eq!(
        eval_import(source),
        "((pet rex) (pet tom) (dog rex) (cat tom))"
    );
}

#[test]
fn clips_import_result_feeds_straight_into_defmodule() {
    // The whole point: no hand-editing step between import and use.
    let source = r#"
        (def imported-clauses (clips-import (quote ((deffacts initial-facts (planet earth) (star sun))))))
        (defmodule imported imported-clauses)
        (reason-in (quote imported) (quote (planet earth)))
    "#;
    assert_eq!(
        eval_import(source),
        "((() (proved (planet earth) (planet earth) ())))"
    );
}

#[test]
fn clips_deftemplate_name_is_matched_regardless_of_a_defmodule_qualifier() {
    // Regression: real CLIPS files namespace deftemplate names with a
    // `defmodule` prefix (`QUESTIONS::question`), then assert plain
    // `(question ...)` facts elsewhere — CLIPS resolves that against
    // whichever module is current. This importer models no modules at
    // all, so both the template's own registered name and any fact head
    // referring to it must be compared with the `defmodule::` prefix
    // stripped, or the named-slot conversion silently never fires.
    let source = r#"
        (clips-import (quote (
            (deftemplate QUESTIONS::question (slot attribute) (slot text))
            (deffacts init (question (attribute color) (text "what color?")))
        )))
    "#;
    assert_eq!(eval_import(source), "(((question color \"what color?\")))");
}

#[test]
fn clips_condition_slot_with_no_value_does_not_crash_the_importer() {
    // Regression: a CLIPS condition can name a multislot with no value at
    // all, e.g. `(precursors)`, meaning "match regardless of what's in
    // this slot". clips-slot-value-of used to assume every slot form has
    // a value part and called `second` unconditionally, crashing with
    // "car expects a non-empty list" the first time a real file used this
    // shorthand.
    let source = r#"
        (clips-import (quote (
            (deftemplate question (slot attribute) (multislot precursors))
            (defrule ask (question (attribute ?a) (precursors)) => (assert (asked ?a)))
        )))
    "#;
    assert_eq!(
        eval_import(source),
        "(((asked (var a)) (question (var a) ())))"
    );
}

#[test]
fn clips_import_stays_stack_safe_on_a_deffacts_block_with_many_facts() {
    // Regression: clips-facts->clauses/clips-import-forms used to build
    // their result with `(cons ... (recurse ...))`/`(append ... (recurse
    // ...))`, neither a tail call, so the Rust stack grew one frame per
    // fact/form. A synthetic 5,000-fact deffacts reproduces the same
    // shape as the real external file that first hit this (a 128-fact
    // block in animal-external.clp) without depending on that fixture or
    // network access — mirrors how tests/stack_safety.rs regression-tests
    // lib/core.lisp's own tail-recursive list utilities on a 100,000-element
    // list.
    let mut facts = String::new();
    for i in 0..5000 {
        facts.push_str(&format!("(number {i})"));
    }
    let source =
        format!(r#"(clips-import (quote ((deffacts many (goal x)) (deffacts nums {facts}))))"#);
    let imported = eval_import(&source);
    assert!(
        imported.contains("(number 0)") && imported.contains("(number 4999)"),
        "expected every fact to survive the import, got a result of length {}",
        imported.len()
    );
}

#[test]
fn clips_defrule_with_an_exists_condition_imports_and_converts_its_template() {
    // Once lib/forward.my Step 15 gave `exists`/`forall` real dispatcher
    // support, the Step 19 skip-guard in this file was removed (same as
    // Step 5's `not` guard was removed after lib/forward.my Step 7).
    // `clips-convert-template` also learned to recurse into `exists`
    // (same lesson Step 13 taught for `not`/`or`/`and`), so a named-slot
    // fact nested inside it gets converted to positional form too.
    let source = r#"
        (clips-import (quote (
            (deftemplate unsolved (slot row) (slot column))
            (defrule wait-for-more
                (rank (value ?last))
                (exists (unsolved (row ?r) (column ?c)))
                =>
                (assert (rank (value done)))))))
    "#;
    assert_eq!(
        eval_import(source),
        "(((rank (value done)) (rank (value (var last))) (exists (unsolved (var r) (var c)))))"
    );
}

#[test]
fn clips_defrule_with_a_forall_condition_imports_correctly() {
    let source = r#"
        (clips-import (quote ((defrule all-checked
            (forall (item ?x) (checked ?x))
            =>
            (assert (done))))))
    "#;
    assert_eq!(
        eval_import(source),
        "(((done) (forall (item (var x)) (checked (var x)))))"
    );
}
