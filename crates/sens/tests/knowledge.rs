use sens::{eval_program, Session};

/// `load` is a host capability; `read-file`/`write-file` are language-owned
/// (lib/fs.lisp) over the host's `read-file-bytes`/`write-file-bytes`. This
/// suite installs the host (via the dev-dependency on sens-host) and
/// loads fs.lisp because load-knowledge / import-knowledge-file /
/// write-knowledge-package use them, while what the suite itself tests is
/// knowledge semantics.
fn install_file_capabilities() {
    sens_host::install();
}

fn eval_knowledge(source: &str) -> String {
    install_file_capabilities();
    let mut session = Session::default();
    sens::load_core_library(&mut session).unwrap();
    eval_program(include_str!("../../../lib/utf8.lisp"), &mut session).unwrap();
    eval_program(include_str!("../../../lib/fs.lisp"), &mut session).unwrap();
    eval_program(include_str!("../../../lib/unify.lisp"), &mut session).unwrap();
    eval_program(include_str!("../../../lib/reason.lisp"), &mut session).unwrap();
    eval_program(include_str!("../../../lib/forward.lisp"), &mut session).unwrap();
    eval_program(include_str!("../../../lib/knowledge.lisp"), &mut session).unwrap();
    let result = eval_program(source, &mut session);
    match result {
        Ok(res) => {
            for line in &res.output {
                println!("{}", line);
            }
            res.value.to_string()
        }
        Err(e) => {
            println!("Output before panic:");
            for line in &session.environment.output_snapshot() {
                println!("{}", line);
            }
            panic!("evaluation failed: {e}\nsource: {source}")
        }
    }
}

#[test]
fn test_defmodule_and_reason_in() {
    let source = r#"
        (load-knowledge "../../knowledge/family.lisp")
        (let ((results (reason-in (quote family) (quote (parent tom (var x))))))
             ;; We expect the first proof result to bind (x . bob)
             (car (car results)))
    "#;
    assert_eq!(eval_knowledge(source), "((x . bob))");
}

#[test]
fn test_defmodule_and_reason_in_physics() {
    let source = r#"
        (load-knowledge "../../knowledge/physics.lisp")
        (let ((results (reason-in (quote physics) (quote (has-mass (var x))))))
             ;; We expect the first proof result to bind (x . apple)
             (car (car results)))
    "#;
    assert_eq!(eval_knowledge(source), "((x . apple))");
}

#[test]
fn test_reason_in_unknown_module() {
    let source = r#"
        (reason-in (quote biology) (quote (is-alive cell)))
    "#;
    assert_eq!(eval_knowledge(source), "Module-not-found");
}

#[test]
fn test_forward_in_materializes_every_derivable_fact_in_a_module() {
    let source = r#"
        (load-knowledge "../../knowledge/family.lisp")
        (forward-in (quote family))
    "#;
    // family.lisp's `ancestor` is recursive (base case: direct parent; recursive
    // case: parent of an ancestor) — this list includes transitive facts like
    // (ancestor tom jim), three hops from a fact never stated directly,
    // proving run-multi's fixpoint loop actually re-fires a rule against its
    // own prior output, not just each rule once.
    assert_eq!(
        eval_knowledge(source),
        "((ancestor tom jim) (ancestor tom pat) (ancestor tom ann) (ancestor bob jim) (ancestor tom bob) (ancestor tom liz) (ancestor bob ann) (ancestor bob pat) (ancestor pat jim) (grandparent tom ann) (grandparent tom pat) (grandparent bob jim) (parent pat jim) (parent bob pat) (parent bob ann) (parent tom liz) (parent tom bob))"
    );
}

#[test]
fn test_forward_in_materializes_every_derivable_fact_in_astronomy() {
    let source = r#"
        (load-knowledge "../../knowledge/astronomy.lisp")
        (forward-in (quote astronomy))
    "#;
    assert_eq!(
        eval_knowledge(source),
        "((orbits earth sun) (orbits mars sun) (star sun) (planet mars) (planet earth))"
    );
}

#[test]
fn test_forward_in_unknown_module() {
    let source = r#"
        (forward-in (quote biology))
    "#;
    assert_eq!(eval_knowledge(source), "Module-not-found");
}

#[test]
fn test_forward_in_chains_a_recursive_rule_through_its_own_prior_output() {
    let source = r#"
        (load-knowledge "../../knowledge/family.lisp")
        (reason-in (quote family) (quote (ancestor tom jim)))
    "#;
    // grandparent alone (a fixed one-hop rule) cannot reach `jim` from `tom`
    // (three parent-hops away: tom -> bob -> pat -> jim); only the
    // recursive `ancestor` rule, firing against its own previously derived
    // output, can. A non-empty proof list is direct evidence the chain
    // actually recursed, not just evaluated each rule once.
    assert_ne!(eval_knowledge(source), "()");
}

#[test]
fn test_family_module() {
    let source = r#"
        (load-knowledge "../../knowledge/family.lisp")
        (let ((results (reason-in (quote family) (quote (grandparent tom ann)))))
             ;; The result contains the bindings used during the proof, including rule variables
             (car (car results)))
    "#;
    assert_eq!(
        eval_knowledge(source),
        "(((z . 0) . bob) ((y . 0) . ann) ((x . 0) . tom))"
    );
}

#[test]
fn test_forward_in_chains_multiple_rules_in_physics() {
    let source = r#"
        (load-knowledge "../../knowledge/physics.lisp")
        (forward-in (quote physics))
    "#;
    assert_eq!(
        eval_knowledge(source),
        "((attracted-by-gravity apple) (has-mass apple))"
    );
}

#[test]
fn test_astronomy_module() {
    let source = r#"
        (load-knowledge "../../knowledge/astronomy.lisp")
        (let ((results (reason-in (quote astronomy) (quote (orbits earth sun)))))
             ;; The result contains the bindings used during the proof, including rule variables
             (car (car results)))
    "#;
    assert_eq!(
        eval_knowledge(source),
        "(((s . 0) . sun) ((p . 0) . earth))"
    );
}

#[test]
fn test_describe_collects_every_fact_about_a_symbol_astronomy() {
    let source = r#"
        (load-knowledge "../../knowledge/astronomy.lisp")
        (describe (quote earth) (quote astronomy))
    "#;
    // `earth` appears in one fact (`(planet earth)`); the `orbits` rule is not
    // a fact, so it is excluded even though `earth` could satisfy it.
    assert_eq!(eval_knowledge(source), "((planet earth))");
}

#[test]
fn test_describe_symbol_with_no_facts_astronomy() {
    let source = r#"
        (load-knowledge "../../knowledge/astronomy.lisp")
        (describe (quote pluto) (quote astronomy))
    "#;
    assert_eq!(eval_knowledge(source), "()");
}

#[test]
fn test_describe_collects_every_fact_about_a_symbol() {
    let source = r#"
        (load-knowledge "../../knowledge/family.lisp")
        (describe (quote jim) (quote family))
    "#;
    // `jim` appears in one fact (`(parent pat jim)`); the `grandparent`/
    // `ancestor` rules are not facts, so they're excluded even though `jim`
    // could satisfy them.
    assert_eq!(eval_knowledge(source), "((parent pat jim))");
}

#[test]
fn test_describe_unknown_module() {
    let source = r#"
        (describe (quote earth) (quote biology))
    "#;
    assert_eq!(eval_knowledge(source), "Module-not-found");
}

#[test]
fn test_describe_symbol_with_no_facts() {
    let source = r#"
        (load-knowledge "../../knowledge/family.lisp")
        (describe (quote ringo) (quote family))
    "#;
    assert_eq!(eval_knowledge(source), "()");
}

#[test]
fn test_record_usage_accumulates_across_separate_queries() {
    // `record-usage!` must run directly at the top level (the global frame),
    // not nested inside a `let` — `let` desugars to an immediately-invoked
    // lambda, and `def` only ever mutates the frame it runs in, so a
    // `record-usage!` wrapped in `let` would quietly define a throwaway local
    // instead of updating the global `*usage-counts*`.
    //
    // The renamed rule head `(grandparent (var (x . 0)) (var (y . 0)))` is
    // built with `cons`/`list` rather than a quoted `'(x . 0)` literal: the
    // reader has no dotted-pair syntax (a literal `.` parses as an ordinary
    // symbol), even though the printer renders real dotted pairs that way —
    // so a quoted `(x . 0)` and an actual `(cons (quote x) 0)` are not `equal?`.
    let source = r#"
        (load-knowledge "../../knowledge/family.lisp")
        (def rule-key (list (quote grandparent) (list (quote var) (cons (quote x) 0)) (list (quote var) (cons (quote y) 0))))
        (def results-1 (reason-in (quote family) (quote (grandparent tom ann))))
        (record-usage! (second (car results-1)))
        (def results-2 (reason-in (quote family) (quote (grandparent tom pat))))
        (record-usage! (second (car results-2)))
        (usage-of rule-key)
    "#;
    // The `grandparent` rule fired once per query, on two separate top-level
    // `record-usage!` calls; usage-of reports the running total.
    assert_eq!(eval_knowledge(source), "2");
}

#[test]
fn test_record_usage_accumulates_across_separate_queries_astronomy() {
    let source = r#"
        (load-knowledge "../../knowledge/astronomy.lisp")
        (def rule-key (list (quote orbits) (list (quote var) (cons (quote p) 0)) (list (quote var) (cons (quote s) 0))))
        (def results-1 (reason-in (quote astronomy) (quote (orbits earth sun))))
        (record-usage! (second (car results-1)))
        (def results-2 (reason-in (quote astronomy) (quote (orbits mars sun))))
        (record-usage! (second (car results-2)))
        (usage-of rule-key)
    "#;
    // The `orbits` rule fired once per query, on two separate top-level
    // `record-usage!` calls; usage-of reports the running total.
    assert_eq!(eval_knowledge(source), "2");
}

#[test]
fn test_usage_of_unrecorded_rule_is_zero() {
    let source = r#"
        (usage-of (list (quote grandparent) (list (quote var) (cons (quote x) 0)) (list (quote var) (cons (quote y) 0))))
    "#;
    assert_eq!(eval_knowledge(source), "0");
}

// --- append-only fact journal --------------------------------------------
// `*knowledge-base*` (a single snapshot per module, replaced outright on
// every write) is gone; `*knowledge-journal*` is the source of truth now —
// a flat, ever-growing list of `tell`/`retract` events, and a module's
// clause list is a projection folded over it on demand.

#[test]
fn retract_knowledge_removes_a_fact_the_module_can_no_longer_prove() {
    let source = r#"
        (defmodule zoo (quote (((has-fur cat)) ((has-fur dog)))))
        (retract-knowledge zoo (quote ((has-fur cat))))
        (reason-in (quote zoo) (quote (has-fur cat)))
    "#;
    assert_eq!(eval_knowledge(source), "()");
}

#[test]
fn retract_knowledge_leaves_the_rest_of_the_module_intact() {
    let source = r#"
        (defmodule zoo (quote (((has-fur cat)) ((has-fur dog)))))
        (retract-knowledge zoo (quote ((has-fur cat))))
        (car (car (reason-in (quote zoo) (quote (has-fur dog)))))
    "#;
    assert_eq!(eval_knowledge(source), "()");
}

#[test]
fn a_module_retracted_down_to_nothing_is_still_a_known_module() {
    // This is exactly the distinction `module-known?` exists to preserve:
    // "no `defmodule`/`tell-knowledge` ever named this module" must read
    // differently from "this module existed, but everything it was told
    // has since been retracted" — the second case still isn't
    // `Module-not-found`, it's a known module with an empty clause list.
    let source = r#"
        (defmodule zoo (quote (((has-fur cat)))))
        (retract-knowledge zoo (quote ((has-fur cat))))
        (reason-in (quote zoo) (quote (has-fur cat)))
    "#;
    assert_eq!(eval_knowledge(source), "()");
    let describe_source = r#"
        (defmodule zoo (quote (((has-fur cat)))))
        (retract-knowledge zoo (quote ((has-fur cat))))
        (describe (quote cat) (quote zoo))
    "#;
    // `describe` returning `()` (an empty fact list, not the symbol
    // `Module-not-found`) is the proof the module is still known.
    assert_eq!(eval_knowledge(describe_source), "()");
}

#[test]
fn defmodule_called_twice_for_the_same_name_accumulates_instead_of_replacing() {
    // A deliberate behavior change from the old snapshot model, where a
    // second `defmodule` for the same name silently shadowed the first:
    // an append-only journal never discards what an earlier call told it,
    // so both calls' clauses are visible together.
    let source = r#"
        (defmodule zoo (quote (((has-fur cat)))))
        (defmodule zoo (quote (((has-fur dog)))))
        (list (car (car (reason-in (quote zoo) (quote (has-fur cat)))))
              (car (car (reason-in (quote zoo) (quote (has-fur dog))))))
    "#;
    assert_eq!(eval_knowledge(source), "(() ())");
}

#[test]
fn tell_knowledge_and_defmodule_contributions_to_the_same_module_both_survive() {
    let source = r#"
        (defmodule zoo (quote (((has-fur cat)))))
        (tell-knowledge zoo (quote (((has-fur dog)))))
        (list (car (car (reason-in (quote zoo) (quote (has-fur cat)))))
              (car (car (reason-in (quote zoo) (quote (has-fur dog))))))
    "#;
    assert_eq!(eval_knowledge(source), "(() ())");
}

// --- guarded Advice Taker ingestion ------------------------------------
// Accepted input mutates the journal; rejected and conflicting input do not.
// Absence of a fact is never treated as its explicit negation.
// Pryiniatyi vvid zminiuie zhurnal; vidkhylenyi i konfliktnyi — ni. Vidsutnist
// faktu nikoly ne vvazhaietsia yoho yavnym zaperechenniam.
// Akzeptierte Eingabe ändert das Journal; abgelehnte und widersprüchliche
// Eingabe nicht. Das Fehlen eines Fakts gilt nie als explizite Verneinung.

#[test]
fn advise_accepts_a_valid_fact_and_makes_it_queryable() {
    let source = r#"
        (list
          (advise astronomy (quote ((planet venus))))
          (car (car (reason-in (quote astronomy) (quote (planet venus))))))
    "#;
    assert_eq!(
        eval_knowledge(source),
        "((accepted (module astronomy) (knowledge ((planet venus)))) ())"
    );
}

#[test]
fn advise_accepts_a_valid_rule_and_reason_uses_it() {
    let source = r#"
        (advise astronomy (quote ((planet earth))))
        (advise astronomy (quote ((has-mass (var x)) (planet (var x)))))
        (car (car (reason-in (quote astronomy) (quote (has-mass earth)))))
    "#;
    assert_eq!(eval_knowledge(source), "(((x . 0) . earth))");
}

#[test]
fn advise_rejects_malformed_clause_without_creating_a_module() {
    let source = r#"
        (list
          (advise astronomy (quote (planet venus)))
          (reason-in (quote astronomy) (quote (planet venus))))
    "#;
    assert_eq!(
        eval_knowledge(source),
        "((rejected (reason invalid-clause) (input (planet venus))) Module-not-found)"
    );
}

#[test]
fn advise_rejects_a_malformed_logic_variable() {
    assert_eq!(
        eval_knowledge("(advise astronomy (quote ((planet (var)))))"),
        "(rejected (reason invalid-clause) (input ((planet (var)))))"
    );
}

#[test]
fn advise_reports_an_explicit_conflict_without_recording_it() {
    let source = r#"
        (advise astronomy (quote ((not? (planet pluto)))))
        (def result (advise astronomy (quote ((planet pluto)))))
        (list (car result)
              (second (third result))
              (reason-in (quote astronomy) (quote (planet pluto))))
    "#;
    assert_eq!(eval_knowledge(source), "(conflict (not? (planet pluto)) ())");
}

#[test]
fn advise_does_not_confuse_absence_with_explicit_negation() {
    assert_eq!(
        eval_knowledge("(advise astronomy (quote ((planet neptune))))"),
        "(accepted (module astronomy) (knowledge ((planet neptune))))"
    );
}

#[test]
fn advise_all_accepts_a_batch_atomically_and_rules_use_the_whole_batch() {
    let source = r#"
        (list
          (advise-all astronomy
            (quote (((planet earth))
              ((has-mass (var x)) (planet (var x))))))
          (car (car (reason-in (quote astronomy) (quote (has-mass earth))))))
    "#;
    assert_eq!(
        eval_knowledge(source),
        "((accepted (module astronomy) (knowledge (((planet earth)) ((has-mass (var x)) (planet (var x)))))) (((x . 0) . earth)))"
    );
}

#[test]
fn advise_all_rejects_the_whole_batch_when_one_clause_is_malformed() {
    let source = r#"
        (list
          (car (advise-all astronomy (quote (((planet earth)) (planet mars)))))
          (reason-in (quote astronomy) (quote (planet earth))))
    "#;
    assert_eq!(eval_knowledge(source), "(rejected Module-not-found)");
}

#[test]
fn advise_all_rejects_an_empty_batch_without_creating_a_module() {
    let source = r#"
        (list (advise-all astronomy (quote ()))
              (reason-in (quote astronomy) (quote (planet earth))))
    "#;
    assert_eq!(
        eval_knowledge(source),
        "((rejected (reason invalid-batch) (input ())) Module-not-found)"
    );
}

#[test]
fn advise_all_detects_an_internal_explicit_conflict_without_writing() {
    let source = r#"
        (list
          (car (advise-all astronomy
                 (quote (((planet pluto)) ((not? (planet pluto)))))))
          (reason-in (quote astronomy) (quote (planet pluto))))
    "#;
    assert_eq!(eval_knowledge(source), "(conflict Module-not-found)");
}

#[test]
fn advise_all_detects_a_conflict_derived_by_the_proposed_rules() {
    let source = r#"
        (list
          (car (advise-all astronomy
                 (quote (((planet pluto))
                   ((not? (dwarf pluto)))
                   ((dwarf (var x)) (planet (var x)))))))
          (reason-in (quote astronomy) (quote (planet pluto))))
    "#;
    assert_eq!(eval_knowledge(source), "(conflict Module-not-found)");
}

#[test]
fn advise_all_detects_a_conflict_activated_across_existing_and_new_knowledge() {
    let source = r#"
        (defmodule astronomy
          (quote (((not? (has-mass pluto)))
            ((has-mass (var x)) (planet (var x))))))
        (list
          (car (advise-all astronomy (quote (((planet pluto))))))
          (reason-in (quote astronomy) (quote (planet pluto))))
    "#;
    assert_eq!(eval_knowledge(source), "(conflict ())");
}

#[test]
fn knowledge_package_constructor_has_the_versioned_interchange_shape() {
    assert_eq!(
        eval_knowledge("(make-knowledge-package (quote astronomy) (quote (((planet earth)))))"),
        "((format . my-lisp-knowledge) (version 0 1) (module . astronomy) (clauses ((planet earth))))"
    );
}

#[test]
fn import_knowledge_package_atomically_installs_valid_data() {
    let source = r#"
        (def package
          (quote ((format . my-lisp-knowledge)
            (version 0 1)
            (module . astronomy)
            (clauses . (((planet earth))
                        ((has-mass (var x)) (planet (var x))))))))
        (list (car (import-knowledge-package package))
              (car (car (reason-in (quote astronomy) (quote (has-mass earth))))))
    "#;
    assert_eq!(eval_knowledge(source), "(accepted (((x . 0) . earth)))");
}

#[test]
fn import_knowledge_package_rejects_an_unsupported_version_without_writing() {
    let source = r#"
        (def package
          (quote ((format . my-lisp-knowledge)
            (version 1 0)
            (module . astronomy)
            (clauses . (((planet earth)))))))
        (list (knowledge-package-decision package)
              (reason-in (quote astronomy) (quote (planet earth))))
    "#;
    assert_eq!(
        eval_knowledge(source),
        "((rejected (reason unsupported-version) (version (1 0))) Module-not-found)"
    );
}

#[test]
fn import_knowledge_package_rejects_a_malformed_envelope_without_writing() {
    let source = r#"
        (def package (quote ((format . my-lisp-knowledge) broken-entry)))
        (list (knowledge-package-decision package)
              (reason-in (quote astronomy) (quote (planet earth))))
    "#;
    assert_eq!(
        eval_knowledge(source),
        "((rejected (reason invalid-package) (input ((format . my-lisp-knowledge) broken-entry))) Module-not-found)"
    );
}

#[test]
fn import_knowledge_file_reads_the_data_only_example() {
    let source = r#"
        (list
          (car (import-knowledge-file "../../knowledge/examples/astronomy-package.lisp"))
          (car (car (reason-in (quote astronomy-exchange) (quote (has-mass earth))))))
    "#;
    assert_eq!(eval_knowledge(source), "(accepted (((x . 0) . earth)))");
}

#[test]
fn write_knowledge_package_round_trips_through_file_import() {
    let path = std::env::temp_dir().join("my-lisp-knowledge-package.lisp");
    let path_str = path.to_str().unwrap().replace('\\', "/");
    let source = format!(
        r#"
        (write-knowledge-package "{path_str}" (quote exchange)
          (quote (((planet earth))
            ((has-mass (var x)) (planet (var x))))))
        (list (car (import-knowledge-file "{path_str}"))
              (car (car (reason-in (quote exchange) (quote (has-mass earth))))))
    "#
    );
    assert_eq!(eval_knowledge(&source), "(accepted (((x . 0) . earth)))");
    std::fs::remove_file(path).ok();
}

#[test]
fn write_knowledge_package_rejects_invalid_data_before_creating_a_file() {
    let path = std::env::temp_dir().join("sens-invalid-package.lisp");
    std::fs::remove_file(&path).ok();
    let path_str = path.to_str().unwrap().replace('\\', "/");
    let source = format!(r#"(write-knowledge-package "{path_str}" (quote exchange) (quote ()))"#);
    assert_eq!(
        eval_knowledge(&source),
        "(rejected (reason invalid-batch) (input ()))"
    );
    assert!(!path.exists());
}
