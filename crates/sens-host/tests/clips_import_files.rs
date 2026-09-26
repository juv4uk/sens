//! File-based clips-import tests. Moved from crates/sens/tests/
//! clips_import.rs during the core/host split: they read real .clp files
//! through `read-file` (via lib/clips-import.my), which is now
//! language-owned (lib/fs.lisp) over this crate's `read-file-bytes` raw
//! capability.

use sens::{eval_program, Session};
use sens_host::install;

fn eval_import(source: &str) -> String {
    install();
    let mut session = Session::default();
    eval_program(include_str!("../../../lib/core.lisp"), &mut session).unwrap();
    eval_program(include_str!("../../../lib/utf8.lisp"), &mut session).unwrap();
    eval_program(include_str!("../../../lib/fs.lisp"), &mut session).unwrap();
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
fn clips_import_file_imports_a_second_real_external_clp_file_correctly() {
    // tests/fixtures/auto-external.clp is CLIPS's own "Automotive Expert
    // System" example — every one of its 21 rules has an empty docstring,
    // several also a (declare (salience N)); before Step 16 every single
    // one silently never fired. Checking a handful of representative
    // rules imported with clean condition lists (no stray "" or declare)
    // is enough to prove the fix, without pinning all 21 verbatim.
    let source = r#"
        (clips-import-file "../../tests/fixtures/auto-external.clp")
    "#;
    let imported = eval_import(source);
    assert!(
        !imported.contains("declare"),
        "a stray (declare ...) leaked into a condition list: {imported}"
    );
    // The very first clause: no leading "" docstring before its conditions.
    assert!(
        imported.starts_with("(((engine-starts"),
        "expected the first clause to start cleanly with the engine-starts fact, got: {imported}"
    );
}

#[test]
fn clips_import_file_imports_a_real_external_clp_file_from_the_official_clips_examples() {
    // tests/fixtures/wordgame-external.clp is CLIPS's own GERALD+DONALD=
    // ROBERT word-puzzle example, downloaded verbatim — the actual
    // interoperability test: does our importer handle a file we didn't
    // write, not tailored to our importer's coverage?
    let source = r#"
        (clips-import-file "../../tests/fixtures/wordgame-external.clp")
    "#;
    // All twenty facts from startup's single multi-fact assert import
    // correctly, plus generate-combinations' single-fact rule; find-solution
    // has no assert at all (printout only) so contributes nothing — none
    // of that is a bug, that's this rule genuinely having nothing to
    // assert.
    assert_eq!(
        eval_import(source),
        "(((number 0)) ((number 1)) ((number 2)) ((number 3)) ((number 4)) ((number 5)) ((number 6)) ((number 7)) ((number 8)) ((number 9)) ((letter G)) ((letter E)) ((letter R)) ((letter A)) ((letter L)) ((letter D)) ((letter O)) ((letter N)) ((letter B)) ((letter T)) ((combination (var a) (var x)) (number (var x)) (letter (var a))))"
    );
}

#[test]
fn clips_import_file_reads_and_imports_a_real_clp_file() {
    // tests/fixtures/astronomy.clp is a genuine CLIPS source file, not a
    // caller-supplied quoted literal — the actual "connect to old
    // symbolic-AI systems" tool this whole file exists to build.
    let source = r#"
        (def imported (clips-import-file "../../tests/fixtures/astronomy.clp"))
        (defmodule imported-astro imported)
        (forward-in (quote imported-astro))
    "#;
    assert_eq!(
        eval_import(source),
        "((orbits earth sun) (orbits mars sun) (star sun) (planet mars) (planet earth))"
    );
}

#[test]
fn clips_import_file_imports_a_third_real_external_clp_file_with_module_qualified_templates() {
    // wine.clp (CLIPS's own "Wine Expert Sample Problem") is the first
    // real external example to combine defmodule-qualified deftemplate
    // names with deffacts entries that reference them by bare name, and
    // to use CLIPS's valueless-multislot condition shorthand — both bugs
    // above were found through this exact file.
    let source = r#"
        (clips-import-file "../../tests/fixtures/wine-external.clp")
    "#;
    let imported = eval_import(source);
    assert!(
        imported.contains(
            "(question main-component \"Is the main component of the meal meat, fish, or poultry? \" meat () ())"
        ),
        "expected the main-component question fact to be converted to positional form, got: {imported}"
    );
    assert!(
        imported.contains("(wine Gamay red medium medium)"),
        "expected a wine fact to be converted to positional form, got: {imported}"
    );
}

#[test]
fn clips_import_file_imports_a_fourth_real_external_clp_file_with_a_large_deffacts_block() {
    // animal.clp ("Animal Identification Expert System") is the real file
    // that first crashed the process outright with a Rust stack overflow
    // (not a graceful LanguageError) — its knowledge-base deffacts has 128
    // facts, enough non-tail recursion depth (compounded across all 37 of
    // the file's top-level forms) to blow the stack before the fix above.
    let source = r#"
        (clips-import-file "../../tests/fixtures/animal-external.clp")
    "#;
    let imported = eval_import(source);
    assert!(
        imported.contains("(goal type.animal)"),
        "expected the initial goal fact to survive the import, got: {imported}"
    );
    assert!(
        imported.contains("(legalanswers yes)"),
        "expected a converted deftemplate fact to survive the import, got: {imported}"
    );
}

#[test]
fn clips_import_file_imports_a_fifth_real_external_clp_file_with_mostly_disqualified_rules() {
    // manners.clp (the classic OPS5-derived "Manners Benchmark", also
    // distributed with CLIPS) didn't surface a new bug — every one of its
    // 8 rules already exercises policy this importer already has right:
    // `defglobal` is ignored (not a deffacts/defrule, produces no
    // clauses), 6 of the 8 rules use `modify`/`retract`/`(halt)` on their
    // right-hand side and correctly import as no clauses, and one
    // condition even uses CLIPS's `~?var` connective-constraint syntax
    // (documented as unsupported — read as an oddly-named ordinary
    // variable) inside a rule that's disqualified anyway. Only
    // `make_path`, whose RHS is a single plain `assert`, survives. Worth
    // locking in as a regression precisely because it's a differently-
    // shaped real file (no deffacts at all — this benchmark loads its
    // guest data separately) that exercises almost every disqualification
    // rule at once without crashing or importing anything incorrect.
    let source = r#"
        (clips-import-file "../../tests/fixtures/manners-external.clp")
    "#;
    assert_eq!(
        eval_import(source),
        "(((path (var id) (var n1) (var s)) (context make_path) (seating () () () () (var id) (var pid) no) (path (var pid) (var n1) (var s)) (not? (path (var id) (var n1) ()))))"
    );
}

#[test]
fn clips_import_file_imports_a_sixth_real_external_clp_file_with_duplicate_and_embedded_constraints(
) {
    // dilemma1.clp ("Farmer's Dilemma", CLIPS's own cannibals-and-goat
    // search example) is another clean confirmation, not a new bug.
    // Every one of its defrules uses `duplicate` (a CLIPS action this
    // importer has never seen before — an unrecognized non-assert action,
    // same "not an assert form" bucket as `halt`), `retract`, or `modify`
    // on its right-hand side, so all of them correctly import as no
    // clauses. One condition even writes an embedded test constraint
    // directly against a symbol with no separating whitespace —
    // `(search-depth ?sd2&:(< ?sd1 ?sd2))` — which the reader splits into
    // a stray extra list item rather than one token; harmless here since
    // that whole rule (`circular-path`) is disqualified by its own
    // `retract` anyway. Only the two `deffacts` blocks (module-qualified
    // `MAIN::status`/`MAIN::opposites`, exercising the Step 17 prefix fix
    // again) survive.
    let source = r#"
        (clips-import-file "../../tests/fixtures/dilemma1-external.clp")
    "#;
    assert_eq!(
        eval_import(source),
        "(((status 1 no-parent shore-1 shore-1 shore-1 shore-1 no-move)) ((opposite-of shore-1 shore-2)) ((opposite-of shore-2 shore-1)))"
    );
}

#[test]
fn clips_import_file_imports_a_seventh_real_external_clp_file_at_scale() {
    // zebra.clp (the classic "Who owns the Zebra?" logic puzzle) is
    // another clean confirmation, not a new bug — but it's the first real
    // file to exercise the importer at real scale and hit two genuinely
    // new-in-combination edge cases without crashing:
    //
    // - `find-solution` has 25 conditions, all against the same
    //   `(deftemplate avh (field a) (field v) (field h))` template (note
    //   `field`, not `slot` — irrelevant to this importer, which only
    //   ever reads the slot *name*, never the keyword in front of it),
    //   most wrapped in CLIPS connective-constraint syntax (`~?n1`,
    //   `&=(+ ?c2 1)`, `&:(or ...)`) already known to be read as odd
    //   variable names or stray extra list elements rather than
    //   evaluated — confirmed harmless at 25-conditions-on-one-template
    //   scale, not just in isolation.
    // - `startup` is the first *surviving* rule (RHS is `printout` +
    //   `assert`, no retract/modify) whose left-hand side has zero
    //   conditions at all — straight from the rule name to `=>`. Earlier
    //   zero-condition rules (wine.clp's `start`, dilemma2.clp's
    //   `start-it`) were always disqualified for an unrelated reason
    //   before this path mattered.
    //
    // `print-solution` and `generate-combinations` both use `retract` and
    // correctly contribute no clauses.
    let source = r#"
        (clips-import-file "../../tests/fixtures/zebra-external.clp")
    "#;
    let imported = eval_import(source);
    assert!(
        imported.contains("(value color red)"),
        "expected startup's zero-condition rule to survive and produce a clause, got: {imported}"
    );
    assert!(
        imported.contains("(solution pet zebra (var p5)) (avh nationality englishman (var n1))"),
        "expected find-solution's 25-condition body to convert correctly, got: {imported}"
    );
    let source_count = format!("(length {source})");
    assert_eq!(
        eval_import(&source_count),
        "50",
        "expected 25 clauses from find-solution's 25 asserts plus 25 from startup's 25 asserts"
    );
}

#[test]
fn clips_import_file_imports_an_eighth_real_external_clp_file_with_bare_tilde_constraints() {
    // mab.clp ("Monkees and Bananas", CLIPS's own planning-problem
    // example) is another clean confirmation, not a new bug, but the
    // first real file to use a *bare* `~var`/`~symbol` connective
    // constraint as a whole slot value on its own — e.g. `(monkey
    // (holding ~?chest))` and `(thing (on-top-of ~floor) ...)` — rather
    // than only ever appearing as the tail of an `&`-chain like
    // `?x&~?y`. Same known limitation (read as one oddly-shaped symbol,
    // not evaluated), confirmed harmless in this new shape too. It's
    // also the first file with 33 defrules at once, most combining
    // fact-address bindings (`?monkey <-`) with both `not` conditions and
    // `modify` on the right-hand side — every `modify`-bearing rule
    // correctly disqualifies, every pure-assert rule (all with an empty
    // `""` docstring, per Step 16) correctly survives.
    let source = r#"
        (clips-import-file "../../tests/fixtures/mab-external.clp")
    "#;
    let imported = eval_import(source);
    assert!(
        imported.contains("(monkey () () ~?chest)"),
        "expected a bare ~?var connective constraint to survive as an odd symbol, got: {imported}"
    );
    assert!(
        imported.contains("(thing (var chest) () ~floor light)"),
        "expected a bare ~symbol connective constraint to survive as an odd symbol, got: {imported}"
    );
    assert!(
        imported.contains("(monkey t5-7 green-couch blank)"),
        "expected startup's zero-condition rule to survive and produce a clause, got: {imported}"
    );
    let source_count = format!("(length {source})");
    assert_eq!(
        eval_import(&source_count),
        "30",
        "expected 17 goal-directed rules plus startup's 13 asserted facts to survive"
    );
}

#[test]
fn clips_import_file_imports_a_ninth_real_external_clp_file_with_a_real_exists_condition() {
    // sudoku.clp (CLIPS's own Sudoku solver) is the real file that first
    // used `exists` — `(exists (unsolved))`, "true if at least one
    // unsolved cell remains" — inside a rank-selection rule. No deffacts
    // in this file (puzzle data loads separately); 12 defrules, most
    // disqualified by `not`/`test`-heavy conditions converting correctly
    // (already-known limitations, not bugs) or surviving as genuine
    // working clauses, including the one with `exists` itself.
    let source = r#"
        (clips-import-file "../../tests/fixtures/sudoku-external.clp")
    "#;
    let imported = eval_import(source);
    assert!(
        imported.contains("(exists (unsolved () ()))"),
        "expected the exists-bearing rule to import with its template converted, got: {imported}"
    );
    assert!(
        imported.contains("(size-value 1 1)"),
        "expected a converted deftemplate fact to survive the import, got: {imported}"
    );
}
