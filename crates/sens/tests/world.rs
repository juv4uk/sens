//! #1312 observer for world system transitions, history preservation, and relations.
//!
//! Rust observes mechanism; Lisp owns semantic meaning (see #112/#113, #1312).
//! Tests observe four distinct classes of laws defined in contracts/world-transition-contract.lisp:
//! 1. World snapshot parentage and historical preservation: verified via structural-relation (equal?).
//! 2. Content-address equality: independently observed via the current exact-domain evaluator.
//! 3. Transaction receipts: embed structural-relation records (conflict, rejected, accepted).
//! 4. Compatibility wrappers: maintain journal transitions without universal-T authority.

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
fn empty_world_is_an_ordinary_first_class_value() {
    assert_eq!(eval_world("(world? (empty-world))"), "t");
    assert_eq!(eval_world("(world? (quote (not-a-world)))"), "()");
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
fn each_world_keeps_its_immediate_parent() {
    // #1312: parent equality observed as structural-relation same, not universal-t
    assert_eq!(
        eval_world(
            r#"
            (let ((before (empty-world)))
              (let ((after (world-tell before (quote zoo) (quote ((has-fur cat))))))
                (equal? before (world-parent after))))
            "#
        ),
        "(1)"
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
fn defmodule_compatibility_wrapper_uses_the_world_transition() {
    // #1312: wrapper journal convergence observed as structural-relation same
    assert_eq!(
        eval_world(
            r#"
            (let ((clauses (quote (((planet earth)) ((star sun))))))
              (let ((expected
                      (world-journal
                        (world-tell-all
                          (make-world (quote ()) *knowledge-journal* (quote ()))
                          (quote space)
                          clauses))))
                ((lambda ()
                   (defmodule space clauses)
                   (equal? *knowledge-journal* expected)))))
            "#
        ),
        "(1)"
    );
}

#[test]
fn defmodule_after_world_load_keeps_legacy_reason_in_behavior() {
    assert_eq!(
        eval_world(
            r#"
            (defmodule space (quote (((planet earth)))))
            (reason-in (quote space) (quote (planet earth)))
            "#
        ),
        "((() (proved (planet earth) (planet earth) ())))"
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
fn tell_knowledge_compatibility_wrapper_uses_the_world_transition() {
    // #1312: tell wrapper journal convergence observed as structural-relation same
    assert_eq!(
        eval_world(
            r#"
            (defmodule space (quote (((planet earth)))))
            (def clauses (quote (((planet mars)))))
            (def expected-journal
              (world-journal
                (world-tell-all
                  (make-world (quote ()) *knowledge-journal* (quote ()))
                  (quote space)
                  clauses)))
            (tell-knowledge space clauses)
            (equal? *knowledge-journal* expected-journal)
            "#
        ),
        "(1)"
    );
}

#[test]
fn conflicting_tell_knowledge_keeps_the_legacy_journal_unchanged() {
    // #1312: tell conflict journal preservation observed as structural-relation same
    assert_eq!(
        eval_world(
            r#"
            (defmodule space (quote (((not? (planet earth))))))
            (let ((before *knowledge-journal*))
              (list (tell-knowledge space (quote (((planet earth)))))
                    (equal? before *knowledge-journal*)))
            "#
        ),
        "(Conflict-detected (1))"
    );
}

#[test]
fn retract_knowledge_compatibility_wrapper_uses_the_world_transition() {
    // #1312: retract wrapper journal observed as structural-relation same and query as ()
    assert_eq!(
        eval_world(
            r#"
            (defmodule space (quote (((planet earth)))))
            (def expected-journal
              (world-journal
                (world-retract
                  (make-world (quote ()) *knowledge-journal* (quote ()))
                  (quote space)
                  (quote ((planet earth))))))
            (retract-knowledge space (quote ((planet earth))))
            (list (equal? *knowledge-journal* expected-journal)
                  (reason-in (quote space) (quote (planet earth))))
            "#
        ),
        "((1) ())"
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
fn advise_compatibility_wrapper_preserves_journal_on_conflict() {
    // #1312: advise conflict receipt preserves journal as structural-relation same
    assert_eq!(
        eval_world(
            r#"
            (defmodule space (quote (((not? (planet earth))))))
            (def before *knowledge-journal*)
            (def decision (advise space (quote ((planet earth)))))
            (list (car decision) (equal? before *knowledge-journal*))
            "#
        ),
        "(conflict (1))"
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
fn advise_all_compatibility_wrapper_rolls_back_invalid_batch() {
    // #1312: advise-all rollback preserves journal as structural-relation same
    assert_eq!(
        eval_world(
            r#"
            (def before *knowledge-journal*)
            (def decision (advise-all space (quote (((planet earth)) malformed))))
            (list (car decision) (equal? before *knowledge-journal*))
            "#
        ),
        "(rejected (1))"
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
fn package_import_compatibility_wrapper_preserves_journal_on_rejection() {
    // #1312: package rejection preserves journal as structural-relation same
    assert_eq!(
        eval_world(
            r#"
            (def before *knowledge-journal*)
            (def package
              (quote ((format . my-lisp-knowledge)
                (version 99 0)
                (module . space)
                (clauses . (((planet earth)))))))
            (def decision (import-knowledge-package package))
            (list (car decision) (equal? before *knowledge-journal*))
            "#
        ),
        "(rejected (1))"
    );
}

#[test]
fn package_import_compatibility_wrapper_preserves_journal_on_conflict() {
    // #1312: package conflict preserves journal as structural-relation same
    assert_eq!(
        eval_world(
            r#"
            (defmodule space (quote (((not? (planet earth))))))
            (def before *knowledge-journal*)
            (def package
              (make-knowledge-package (quote space) (quote (((planet earth))))))
            (def decision (import-knowledge-package package))
            (list (car decision) (equal? before *knowledge-journal*))
            "#
        ),
        "(conflict (1))"
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
                        (world-clauses w2 (quote zoo))
                        (world-module-known? w2 (quote zoo))))))
            "#
        ),
        "((((has-fur cat))) () t)"
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
fn backward_reasoning_reads_the_selected_world_snapshot() {
    assert_eq!(
        eval_world(
            r#"
            (let ((w0 (empty-world)))
              (let ((w1 (world-tell w0 (quote family) (quote ((parent tom bob))))))
                (let ((w2 (world-retract w1 (quote family) (quote ((parent tom bob))))))
                  (list (cond
                          ((atom? (reason-in-world w1 (quote family) (quote (parent tom bob)))) () (quote no))
                          ((atom? (reason-in-world w1 (quote family) (quote (parent tom bob)))) (1) (quote no))
                          (t (quote yes)))
                        (cond
                          ((atom? (reason-in-world w2 (quote family) (quote (parent tom bob)))) () (quote no))
                          ((atom? (reason-in-world w2 (quote family) (quote (parent tom bob)))) (1) (quote no))
                          (t (quote yes)))))))
            "#
        ),
        "(yes no)"
    );
}

#[test]
fn backward_reasoning_keeps_independent_branches_isolated() {
    assert_eq!(
        eval_world(
            r#"
            (let ((root (empty-world)))
              (let ((cats (world-tell root (quote zoo) (quote ((likes alice cats)))))
                    (dogs (world-tell root (quote zoo) (quote ((likes alice dogs))))))
                (list (cond
                        ((atom? (reason-in-world cats (quote zoo) (quote (likes alice cats)))) () (quote no))
                        ((atom? (reason-in-world cats (quote zoo) (quote (likes alice cats)))) (1) (quote no))
                        (t (quote yes)))
                      (cond
                        ((atom? (reason-in-world cats (quote zoo) (quote (likes alice dogs)))) () (quote no))
                        ((atom? (reason-in-world cats (quote zoo) (quote (likes alice dogs)))) (1) (quote no))
                        (t (quote yes)))
                      (cond
                        ((atom? (reason-in-world dogs (quote zoo) (quote (likes alice dogs)))) () (quote no))
                        ((atom? (reason-in-world dogs (quote zoo) (quote (likes alice dogs)))) (1) (quote no))
                        (t (quote yes)))
                      (cond
                        ((atom? (reason-in-world dogs (quote zoo) (quote (likes alice cats)))) () (quote no))
                        ((atom? (reason-in-world dogs (quote zoo) (quote (likes alice cats)))) (1) (quote no))
                        (t (quote yes))))))
            "#
        ),
        "(yes no yes no)"
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
fn advise_world_accepts_into_a_new_queryable_world() {
    assert_eq!(
        eval_world(
            r#"
            (let ((before (empty-world)))
              (let ((result (advise-world before (quote astronomy) (quote ((planet venus))))))
                (let ((after (second result)))
                  (list (car (car result))
                        (world-clauses before (quote astronomy))
                        (cond
                          ((atom? (reason-in-world after (quote astronomy) (quote (planet venus)))) () (quote no))
                          ((atom? (reason-in-world after (quote astronomy) (quote (planet venus)))) (1) (quote no))
                          (t (quote yes)))))))
            "#
        ),
        "(accepted () yes)"
    );
}

#[test]
fn advise_world_rejection_returns_the_unchanged_world() {
    // #1312: advise-world rejection preserves snapshot as structural-relation same
    assert_eq!(
        eval_world(
            r#"
            (let ((before (empty-world)))
              (let ((result (advise-world before (quote astronomy) (quote (planet venus)))))
                (list (car (car result))
                      (equal? before (second result))
                      (world-module-known? (second result) (quote astronomy)))))
            "#
        ),
        "(rejected (1) ())"
    );
}

#[test]
fn advise_world_conflict_preserves_the_existing_snapshot() {
    // #1312: advise-world conflict preserves snapshot as structural-relation same
    assert_eq!(
        eval_world(
            r#"
            (let ((w1 (world-tell (empty-world)
                                  (quote astronomy)
                                  (quote ((not? (planet pluto)))))))
              (let ((result (advise-world w1 (quote astronomy) (quote ((planet pluto))))))
                (list (car (car result))
                      (equal? w1 (second result))
                      (world-clauses (second result) (quote astronomy)))))
            "#
        ),
        "(conflict (1) (((not? (planet pluto)))))"
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
fn advise_all_world_accepts_one_atomic_dependent_batch() {
    // #1312: advise-all atomic accept preserves parent as structural-relation same
    assert_eq!(
        eval_world(
            r#"
            (let ((before (empty-world)))
              (let ((result
                      (advise-all-world
                        before
                        (quote astronomy)
                        (quote (((planet earth))
                          ((has-mass (var x)) (planet (var x))))))))
                (let ((after (second result)))
                  (list (car (car result))
                        (world-clauses before (quote astronomy))
                        (cond
                          ((atom? (reason-in-world after (quote astronomy)
                                                 (quote (has-mass earth)))) () (quote no))
                          ((atom? (reason-in-world after (quote astronomy)
                                                 (quote (has-mass earth)))) (1) (quote no))
                          (t (quote yes)))
                        (equal? before (world-parent after))))))
            "#
        ),
        "(accepted () yes (1))"
    );
}

#[test]
fn advise_all_world_rejects_the_whole_malformed_batch() {
    // #1312: malformed batch rejection preserves snapshot as structural-relation same
    assert_eq!(
        eval_world(
            r#"
            (let ((before (empty-world)))
              (let ((result
                      (advise-all-world before (quote astronomy)
                                        (quote (((planet earth)) (planet mars))))))
                (list (car (car result))
                      (equal? before (second result))
                      (world-module-known? (second result) (quote astronomy)))))
            "#
        ),
        "(rejected (1) ())"
    );
}

#[test]
fn advise_all_world_rejects_an_empty_batch_without_a_new_world() {
    // #1312: empty batch rejection preserves snapshot as structural-relation same
    assert_eq!(
        eval_world(
            r#"
            (let ((before (empty-world)))
              (let ((result (advise-all-world before (quote astronomy) (quote ()))))
                (list (car (car result))
                      (second (second (car result)))
                      (equal? before (second result)))))
            "#
        ),
        "(rejected invalid-batch (1))"
    );
}

#[test]
fn advise_all_world_detects_internal_conflict_without_partial_writes() {
    // #1312: internal batch conflict preserves snapshot as structural-relation same
    assert_eq!(
        eval_world(
            r#"
            (let ((before (empty-world)))
              (let ((result
                      (advise-all-world
                        before
                        (quote astronomy)
                        (quote (((planet pluto)) ((not? (planet pluto))))))))
                (list (car (car result))
                      (equal? before (second result))
                      (world-module-known? (second result) (quote astronomy)))))
            "#
        ),
        "(conflict (1) ())"
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
fn world_package_import_atomically_creates_a_queryable_child() {
    // #1312: package import creates child with parent as structural-relation same
    assert_eq!(
        eval_world(
            r#"
            (let ((before (empty-world)))
              (let ((package
                      (make-knowledge-package
                        (quote astronomy)
                        (quote (((planet earth))
                          ((has-mass (var x)) (planet (var x))))))))
                (let ((result (import-knowledge-package-world before package)))
                  (let ((after (second result)))
                    (list (car (car result))
                          (equal? before (world-parent after))
                          (cond
                            ((atom? (reason-in-world after (quote astronomy)
                                                   (quote (has-mass earth)))) () (quote no))
                            ((atom? (reason-in-world after (quote astronomy)
                                                   (quote (has-mass earth)))) (1) (quote no))
                            (t (quote yes))))))))
            "#
        ),
        "(accepted (1) yes)"
    );
}

#[test]
fn world_package_import_rejects_unsupported_versions_without_transition() {
    // #1312: unsupported version rejection preserves snapshot as structural-relation same
    assert_eq!(
        eval_world(
            r#"
            (def before (empty-world))
            (def result
              (import-knowledge-package-world
                before
                (quote ((format . my-lisp-knowledge)
                  (version 1 0)
                  (module . astronomy)
                  (clauses . (((planet earth))))))))
            (list (car (car result))
                  (second (second (car result)))
                  (equal? before (second result)))
            "#
        ),
        "(rejected unsupported-version (1))"
    );
}

#[test]
fn world_package_import_conflict_preserves_the_target_snapshot() {
    // #1312: package import conflict preserves snapshot as structural-relation same
    assert_eq!(
        eval_world(
            r#"
            (let ((before
                    (world-tell (empty-world)
                                (quote astronomy)
                                (quote ((not? (planet pluto)))))))
              (let ((package
                      (make-knowledge-package (quote astronomy)
                                              (quote (((planet pluto)))))))
                (let ((result (import-knowledge-package-world before package)))
                  (list (car (car result))
                        (equal? before (second result))
                        (world-clauses (second result) (quote astronomy))))))
            "#
        ),
        "(conflict (1) (((not? (planet pluto)))))"
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
fn world_at_depth_recovers_an_exact_historical_snapshot() {
    // #1312: historical recovery observed as triple structural-relation same
    assert_eq!(
        eval_world(
            r#"
            (let ((w0 (empty-world)))
              (let ((w1 (world-tell w0 (quote zoo) (quote ((has-fur cat))))))
                (let ((w2 (world-tell w1 (quote zoo) (quote ((has-fur dog))))))
                  (list (equal? w0 (world-at-depth w2 0))
                        (equal? w1 (world-at-depth w2 1))
                        (equal? w2 (world-at-depth w2 2))))))
            "#
        ),
        "((1) (1) (1))"
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
fn world_common_ancestor_finds_the_branch_point() {
    // #1312: common ancestor branch point observed as structural-relation same
    assert_eq!(
        eval_world(
            r#"
            (let ((root (empty-world)))
              (let ((base (world-tell root (quote zoo) (quote ((animal cat))))))
                (let ((left (world-tell base (quote zoo) (quote ((has-fur cat)))))
                      (right (world-tell base (quote zoo) (quote ((has-tail cat))))))
                  (equal? base (world-common-ancestor left right)))))
            "#
        ),
        "(1)"
    );
}

#[test]
fn world_common_ancestor_aligns_unequal_branch_depths() {
    // #1312: common ancestor alignment observed as structural-relation same
    assert_eq!(
        eval_world(
            r#"
            (let ((root (empty-world)))
              (let ((base (world-tell root (quote zoo) (quote ((animal cat))))))
                (let ((left1 (world-tell base (quote zoo) (quote ((has-fur cat)))))
                      (right (world-tell base (quote zoo) (quote ((has-tail cat))))))
                  (let ((left2 (world-tell left1 (quote zoo) (quote ((likes cat milk))))))
                    (equal? base (world-common-ancestor left2 right))))))
            "#
        ),
        "(1)"
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

#[test]
fn equal_knowledge_has_the_same_canonical_content_address() {
    // #1312: equal content-address byte strings for equal knowledge (not a retired identity relation).
    assert_eq!(
        eval_world(
            r#"
            (eq? (knowledge-content-address (quote ((planet earth))))
                (knowledge-content-address (quote ((planet earth)))))
            "#
        ),
        "(1)"
    );
}

#[test]
fn different_knowledge_has_a_different_content_address() {
    // #1312: distinct content-address byte strings for different knowledge.
    assert_eq!(
        eval_world(
            r#"
            (eq? (knowledge-content-address (quote ((planet earth))))
                (knowledge-content-address (quote ((planet mars)))))
            "#
        ),
        "(0)"
    );
}

#[test]
fn knowledge_content_addresses_round_trip_to_the_same_structure() {
    // #1312: current D8 equality checks readback of the serialized knowledge structure.
    assert_eq!(
        eval_world(
            r#"
            (let ((knowledge
                    (quote ((has-mass (var x)) (planet (var x))))))
              (equal? knowledge
                      (read (knowledge-content-address knowledge))))
            "#
        ),
        "(1)"
    );
}

#[test]
fn independently_reconstructed_worlds_have_the_same_content_address() {
    // #1312: independently reconstructed worlds produce equal content-address bytes.
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
                (eq? (world-content-address source)
                    (world-content-address copy))))
            "#
        ),
        "(1)"
    );
}

#[test]
fn equal_current_clauses_do_not_erase_distinct_world_histories() {
    // #1312: identical clauses (structural same) paired with distinct history addresses (identity distinct)
    assert_eq!(
        eval_world(
            r#"
            (let ((direct
                    (world-tell (empty-world) (quote zoo) (quote ((has-fur cat))))))
              (let ((told
                      (world-tell (empty-world) (quote zoo) (quote ((has-fur cat))))))
                (let ((retracted
                        (world-retract told (quote zoo) (quote ((has-fur cat))))))
                  (let ((retold
                          (world-tell retracted (quote zoo) (quote ((has-fur cat))))))
                    (list (equal? (world-clauses direct (quote zoo))
                                  (world-clauses retold (quote zoo)))
                          (eq? (world-content-address direct)
                              (world-content-address retold)))))))
            "#
        ),
        "((1) (0))"
    );
}

#[test]
fn world_transition_witness_proves_contract_in_lisp() {
    let mut session = Session::default();
    eval_program(include_str!("../../../lib/core.lisp"), &mut session).unwrap();
    eval_program(include_str!("../../../lib/unify.lisp"), &mut session).unwrap();
    eval_program(include_str!("../../../lib/reason.lisp"), &mut session).unwrap();
    eval_program(include_str!("../../../lib/forward.lisp"), &mut session).unwrap();
    eval_program(include_str!("../../../lib/knowledge.lisp"), &mut session).unwrap();
    eval_program(include_str!("../../../lib/world.lisp"), &mut session).unwrap();
    eval_program(
        include_str!("../../../tests/fixtures/world-transition-witness.lisp"),
        &mut session,
    )
    .unwrap();
    let verdict = eval_program("(wt-run-witness)", &mut session)
        .unwrap()
        .value
        .to_string();
    assert_eq!(
        verdict,
        "((ok parent-relation) (ok address-identity-same) (ok address-identity-distinct) (ok depth-recovery) (ok universal-t-forbidden))"
    );
}
