//! Mechanism and history tests; Lisp owns semantic laws.
//!
//! Historical structural/identity relation and T/NIL expectations were retired.
//! Rust tests must not reintroduce those semantic oracles.

use sens::{eval_program, Session};

fn eval_world(source: &str) -> String {
    let mut session = Session::default();
    eval_program(include_str!("../../../lib/core.lisp"), &mut session).unwrap();
    eval_program(include_str!("../../../lib/unify.lisp"), &mut session).unwrap();
    eval_program(include_str!("../../../lib/reason.lisp"), &mut session).unwrap();
    eval_program(include_str!("../../../lib/forward.lisp"), &mut session).unwrap();
    eval_program(include_str!("../../../lib/knowledge.lisp"), &mut session).unwrap();
    eval_program(include_str!("../../../lib/world.lisp"), &mut session).unwrap();
    eval_program(source, &mut session)
        .unwrap()
        .value
        .to_string()
}

#[test]
fn tell_returns_a_new_world_without_changing_the_old_one() {
    assert_eq!(
        eval_world(
            r#"
            (let ((before (empty-world)))
              (let ((after (world-tell before (quote zoo) (quote ((has-fur cat))))))
                (list (world-clauses before (quote zoo))
                      (world-clauses after (quote zoo)))))
            "#
        ),
        "(() (((has-fur cat))))"
    );
}

#[test]
fn later_versions_preserve_every_earlier_snapshot() {
    assert_eq!(
        eval_world(
            r#"
            (let ((w0 (empty-world)))
              (let ((w1 (world-tell w0 (quote zoo) (quote ((has-fur cat))))))
                (let ((w2 (world-tell w1 (quote zoo) (quote ((has-fur dog))))))
                  (list (world-clauses w0 (quote zoo))
                        (world-clauses w1 (quote zoo))
                        (world-clauses w2 (quote zoo))))))
            "#
        ),
        "(() (((has-fur cat))) (((has-fur dog)) ((has-fur cat))))"
    );
}

#[test]
fn repeated_compatible_defmodule_calls_still_accumulate() {
    assert_eq!(
        eval_world(
            r#"
            (defmodule space (quote (((planet earth)))))
            (defmodule space (quote (((planet mars)))))
            (module-clauses-now (quote space))
            "#
        ),
        "(((planet mars)) ((planet earth)))"
    );
}

#[test]
fn advise_compatibility_wrapper_commits_only_the_accepted_world() {
    assert_eq!(
        eval_world(
            r#"
            (list (advise space (quote ((planet earth))))
                  (reason-in (quote space) (quote (planet earth))))
            "#
        ),
        "((accepted (module space) (knowledge ((planet earth)))) ((() (proved (planet earth) (planet earth) ()))))"
    );
}

#[test]
fn advise_compatibility_argument_is_evaluated_once() {
    assert_eq!(
        eval_world(
            r#"
            (def *evaluation-count* 0)
            (def decision
              (advise space
                (second
                  (list (def *evaluation-count* (+ *evaluation-count* 1))
                        (quote ((planet earth)))))))
            (list *evaluation-count* (car decision))
            "#
        ),
        "(1 accepted)"
    );
}

#[test]
fn advise_all_compatibility_wrapper_keeps_atomic_world_transition() {
    assert_eq!(
        eval_world(
            r#"
            (def decision
              (advise-all space
                (quote (((star sun))
                  ((planet earth) (star sun))))))
            (list (car decision)
                  (length (module-clauses-now (quote space))))
            "#
        ),
        "(accepted 2)"
    );
}

#[test]
fn advise_all_compatibility_argument_is_evaluated_once() {
    assert_eq!(
        eval_world(
            r#"
            (def *evaluation-count* 0)
            (def decision
              (advise-all space
                (second
                  (list (def *evaluation-count* (+ *evaluation-count* 1))
                        (quote (((planet earth))))))))
            (list *evaluation-count* (car decision))
            "#
        ),
        "(1 accepted)"
    );
}

#[test]
fn package_import_compatibility_wrapper_commits_the_accepted_world() {
    assert_eq!(
        eval_world(
            r#"
            (def package
              (make-knowledge-package (quote space) (quote (((planet earth))))))
            (list (car (import-knowledge-package package))
                  (car (reason-in (quote space) (quote (planet earth)))))
            "#
        ),
        "(accepted (() (proved (planet earth) (planet earth) ())))"
    );
}

#[test]
fn package_import_compatibility_argument_is_evaluated_once() {
    assert_eq!(
        eval_world(
            r#"
            (def *evaluation-count* 0)
            (def decision
              (import-knowledge-package
                (second
                  (list (def *evaluation-count* (+ *evaluation-count* 1))
                        (make-knowledge-package
                          (quote space) (quote (((planet earth)))))))))
            (list *evaluation-count* (car decision))
            "#
        ),
        "(1 accepted)"
    );
}

#[test]
fn retract_creates_history_instead_of_erasing_it() {
    assert_eq!(
        eval_world(
            r#"
            (let ((w0 (empty-world)))
              (let ((w1 (world-tell w0 (quote zoo) (quote ((has-fur cat))))))
                (let ((w2 (world-retract w1 (quote zoo) (quote ((has-fur cat))))))
                  (list (world-clauses w1 (quote zoo))
                        (world-clauses w2 (quote zoo))))))
            "#
        ),
        "((((has-fur cat))) ())"
    );
}

#[test]
fn independent_branches_can_grow_from_the_same_world() {
    assert_eq!(
        eval_world(
            r#"
            (let ((root (empty-world)))
              (let ((cats (world-tell root (quote zoo) (quote ((has-fur cat)))))
                    (dogs (world-tell root (quote zoo) (quote ((has-fur dog))))))
                (list (world-clauses cats (quote zoo))
                      (world-clauses dogs (quote zoo))
                      (world-clauses root (quote zoo)))))
            "#
        ),
        "((((has-fur cat))) (((has-fur dog))) ())"
    );
}

#[test]
fn forward_reasoning_materializes_only_the_selected_world() {
    assert_eq!(
        eval_world(
            r#"
            (let ((w0 (empty-world)))
              (let ((w1 (world-tell w0 (quote physics) (quote ((has-mass apple))))))
                (let ((w2 (world-tell w1 (quote physics)
                                      (quote ((attracted-by-gravity (var x))
                                        (has-mass (var x)))))))
                  (list (forward-in-world w1 (quote physics))
                        (forward-in-world w2 (quote physics))))))
            "#
        ),
        "(((has-mass apple)) ((attracted-by-gravity apple) (has-mass apple)))"
    );
}

#[test]
fn world_reasoning_reports_an_unknown_module_without_global_fallback() {
    assert_eq!(
        eval_world("(reason-in-world (empty-world) (quote missing) (quote (fact x)))"),
        "Module-not-found"
    );
    assert_eq!(
        eval_world("(forward-in-world (empty-world) (quote missing))"),
        "Module-not-found"
    );
}

#[test]
fn advise_world_does_not_read_the_global_knowledge_journal() {
    assert_eq!(
        eval_world(
            r#"
            (advise astronomy (quote ((not? (planet mars)))))
            (let ((result (advise-world (empty-world)
                                        (quote astronomy)
                                        (quote ((planet mars))))))
              (list (car (car result))
                    (world-clauses (second result) (quote astronomy))))
            "#
        ),
        "(accepted (((planet mars))))"
    );
}

#[test]
fn advise_all_world_ignores_conflicts_in_the_global_journal() {
    assert_eq!(
        eval_world(
            r#"
            (advise astronomy (quote ((not? (planet mars)))))
            (let ((result
                    (advise-all-world (empty-world)
                                      (quote astronomy)
                                      (quote (((planet mars)))))))
              (list (car (car result))
                    (world-clauses (second result) (quote astronomy))))
            "#
        ),
        "(accepted (((planet mars))))"
    );
}

#[test]
fn world_package_export_reads_the_selected_snapshot_only() {
    assert_eq!(
        eval_world(
            r#"
            (let ((w1 (world-tell (empty-world) (quote astronomy) (quote ((planet earth))))))
              (let ((w2 (world-tell w1 (quote astronomy) (quote ((planet mars))))))
                (list (knowledge-package-field
                        (quote clauses) (make-world-knowledge-package w1 (quote astronomy)))
                      (knowledge-package-field
                        (quote clauses) (make-world-knowledge-package w2 (quote astronomy))))))
            "#
        ),
        "((((planet earth))) (((planet mars)) ((planet earth))))"
    );
}

#[test]
fn exported_snapshot_can_seed_an_independent_world_branch() {
    assert_eq!(
        eval_world(
            r#"
            (let ((source
                    (world-tell (empty-world) (quote zoo) (quote ((has-fur cat))))))
              (let ((package (make-world-knowledge-package source (quote zoo))))
                (let ((target (second
                                (import-knowledge-package-world
                                  (empty-world) package))))
                  (let ((target-grown
                          (world-tell target (quote zoo) (quote ((has-fur dog))))))
                    (list (world-clauses source (quote zoo))
                          (world-clauses target (quote zoo))
                          (world-clauses target-grown (quote zoo)))))))
            "#
        ),
        "((((has-fur cat))) (((has-fur cat))) (((has-fur dog)) ((has-fur cat))))"
    );
}

#[test]
fn world_depth_counts_transitions_from_the_root() {
    assert_eq!(
        eval_world(
            r#"
            (let ((w0 (empty-world)))
              (let ((w1 (world-tell w0 (quote zoo) (quote ((has-fur cat))))))
                (let ((w2 (world-retract w1 (quote zoo) (quote ((has-fur cat))))))
                  (list (world-depth w0)
                        (world-depth w1)
                        (world-depth w2)))))
            "#
        ),
        "(0 1 2)"
    );
}

#[test]
fn world_at_depth_rejects_depths_outside_the_history() {
    assert_eq!(
        eval_world("(list (world-at-depth (empty-world) -1) (world-at-depth (empty-world) 1))"),
        "(World-not-found World-not-found)"
    );
}

#[test]
fn world_diff_returns_chronological_events_across_atomic_transitions() {
    assert_eq!(
        eval_world(
            r#"
            (let ((w0 (empty-world)))
              (let ((w1
                      (world-tell-all
                        w0 (quote zoo)
                        (quote (((has-fur cat)) ((has-fur dog)))))))
                (let ((w2 (world-retract w1 (quote zoo) (quote ((has-fur cat))))))
                  (world-diff w0 w2))))
            "#
        ),
        "((tell zoo ((has-fur cat))) (tell zoo ((has-fur dog))) (retract zoo ((has-fur cat))))"
    );
}

#[test]
fn world_diff_refuses_to_invent_a_path_between_sibling_branches() {
    assert_eq!(
        eval_world(
            r#"
            (let ((root (empty-world)))
              (let ((cats (world-tell root (quote zoo) (quote ((has-fur cat)))))
                    (dogs (world-tell root (quote zoo) (quote ((has-fur dog))))))
                (world-diff cats dogs)))
            "#
        ),
        "World-not-ancestor"
    );
}

#[test]
fn world_branch_diff_reports_both_chronological_deltas() {
    assert_eq!(
        eval_world(
            r#"
            (let ((base (world-tell (empty-world) (quote zoo) (quote ((animal cat))))))
              (let ((left (world-tell base (quote zoo) (quote ((has-fur cat)))))
                    (right (world-tell base (quote zoo) (quote ((has-tail cat))))))
                (let ((comparison (world-branch-diff left right)))
                  (list (second (second comparison))
                        (second (third comparison))))))
            "#
        ),
        "(((tell zoo ((has-fur cat)))) ((tell zoo ((has-tail cat)))))"
    );
}

#[test]
fn reconstructed_equal_worlds_have_no_branch_delta() {
    assert_eq!(
        eval_world(
            r#"
            (let ((source
                    (world-tell (empty-world) (quote zoo) (quote ((has-fur cat))))))
              (let ((copy
                      (second
                        (import-knowledge-package-world
                          (empty-world)
                          (make-world-knowledge-package source (quote zoo))))))
                (let ((comparison (world-branch-diff source copy)))
                  (list (second (second comparison))
                        (second (third comparison))))))
            "#
        ),
        "(() ())"
    );
}

