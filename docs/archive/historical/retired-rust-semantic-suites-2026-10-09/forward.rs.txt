//! Exercises lib/forward.my — Step 1 of a CLIPS-style forward-chaining rule
//! engine: one working-memory list, one rule fired against one fact.
//! Pereviriaie lib/forward.my — Krok 1 forward-chaining rushiia v styli CLIPS:
//! odyn spysok working memory, odne pravylo proty odnoho faktu.
//! Prüft lib/forward.my — Schritt 1 einer CLIPS-artigen
//! Forward-Chaining-Regel-Engine: eine Working-Memory-Liste, eine Regel
//! gegen einen Fakt angewendet.

use sens::{eval_program, Session};

fn eval_forward(source: &str) -> String {
    let mut session = Session::default();
    eval_program(include_str!("../../../lib/core.lisp"), &mut session).unwrap();
    eval_program(include_str!("../../../lib/unify.lisp"), &mut session).unwrap();
    eval_program(include_str!("../../../lib/forward.lisp"), &mut session).unwrap();
    eval_program(source, &mut session)
        .unwrap_or_else(|e| panic!("evaluation failed: {e}\nsource: {source}"))
        .value
        .to_string()
}

#[test]
fn fire_rule_produces_a_new_fact_when_the_pattern_matches() {
    let source = r#"
        (fire-rule (list (list (quote planet) (logic-var (quote x))) (list (quote has-mass) (logic-var (quote x))))
                   (quote (planet earth)))
    "#;
    assert_eq!(eval_forward(source), "(has-mass earth)");
}

#[test]
fn fire_rule_returns_no_match_when_the_pattern_fails() {
    let source = r#"
        (fire-rule (list (list (quote planet) (logic-var (quote x))) (list (quote has-mass) (logic-var (quote x))))
                   (quote (star sun)))
    "#;
    assert_eq!(eval_forward(source), "no-match");
}

#[test]
fn fire_rule_on_facts_collects_new_facts_and_drops_non_matches() {
    let source = r#"
        (fire-rule-on-facts (list (list (quote planet) (logic-var (quote x))) (list (quote has-mass) (logic-var (quote x))))
                             (list (quote (planet earth)) (quote (star sun)) (quote (planet mars))))
    "#;
    assert_eq!(eval_forward(source), "((has-mass earth) (has-mass mars))");
}

#[test]
fn fire_rule_on_facts_returns_empty_list_when_nothing_matches() {
    let source = r#"
        (fire-rule-on-facts (list (list (quote planet) (logic-var (quote x))) (list (quote has-mass) (logic-var (quote x))))
                             (list (quote (star sun)) (quote (moon luna))))
    "#;
    assert_eq!(eval_forward(source), "()");
}

#[test]
fn fire_rule_on_working_memory_reads_the_global_fact_list() {
    let source = r#"
        (assert-fact! (quote (planet earth)))
        (assert-fact! (quote (star sun)))
        (assert-fact! (quote (planet mars)))
        (fire-rule-on-working-memory (list (list (quote planet) (logic-var (quote x))) (list (quote has-mass) (logic-var (quote x)))))
    "#;
    assert_eq!(eval_forward(source), "((has-mass mars) (has-mass earth))");
}

#[test]
fn fire_rules_on_facts_applies_every_rule_and_collects_all_results() {
    let source = r#"
        (fire-rules-on-facts
          (list (list (list (quote planet) (logic-var (quote x))) (list (quote has-mass) (logic-var (quote x))))
                (list (list (quote star) (logic-var (quote x))) (list (quote has-mass) (logic-var (quote x)))))
          (list (quote (planet earth)) (quote (star sun)) (quote (moon luna))))
    "#;
    assert_eq!(eval_forward(source), "((has-mass earth) (has-mass sun))");
}

#[test]
fn fire_rules_on_working_memory_reads_the_global_fact_list() {
    let source = r#"
        (assert-fact! (quote (planet earth)))
        (assert-fact! (quote (star sun)))
        (fire-rules-on-working-memory
          (list (list (list (quote planet) (logic-var (quote x))) (list (quote has-mass) (logic-var (quote x))))
                (list (list (quote star) (logic-var (quote x))) (list (quote has-mass) (logic-var (quote x))))))
    "#;
    assert_eq!(eval_forward(source), "((has-mass earth) (has-mass sun))");
}

#[test]
fn run_reaches_a_fixpoint_by_chaining_rules_across_passes() {
    // orbits(x, sun) -> has-mass(x); has-mass(x) -> heavy(x). Earth's
    // "heavy" fact only appears two passes after the initial orbits fact,
    // so this only passes if `run` actually loops to a fixpoint.
    let source = r#"
        (run (list (list (list (quote orbits) (logic-var (quote x)) (quote sun)) (list (quote has-mass) (logic-var (quote x))))
                    (list (list (quote has-mass) (logic-var (quote x))) (list (quote heavy) (logic-var (quote x)))))
              (list (quote (orbits earth sun))))
    "#;
    assert_eq!(
        eval_forward(source),
        "((heavy earth) (has-mass earth) (orbits earth sun))"
    );
}

#[test]
fn run_does_not_loop_forever_when_a_rule_reproduces_an_existing_fact() {
    let source = r#"
        (run (list (list (list (quote planet) (logic-var (quote x))) (list (quote planet) (logic-var (quote x)))))
              (list (quote (planet earth))))
    "#;
    assert_eq!(eval_forward(source), "((planet earth))");
}

#[test]
fn assert_facts_merges_run_results_into_the_global_working_memory() {
    let source = r#"
        (assert-fact! (quote (orbits earth sun)))
        (assert-facts!
          (run (list (list (list (quote orbits) (logic-var (quote x)) (quote sun)) (list (quote has-mass) (logic-var (quote x)))))
                *working-memory*))
        *working-memory*
    "#;
    assert_eq!(
        eval_forward(source),
        "((has-mass earth) (orbits earth sun))"
    );
}

#[test]
fn retract_fact_removes_a_matching_fact_from_a_list() {
    let source = r#"
        (retract-fact (quote (star sun)) (list (quote (planet earth)) (quote (star sun)) (quote (planet mars))))
    "#;
    assert_eq!(eval_forward(source), "((planet earth) (planet mars))");
}

#[test]
fn retract_fact_leaves_the_list_unchanged_when_nothing_matches() {
    let source = r#"
        (retract-fact (quote (moon luna)) (list (quote (planet earth)) (quote (star sun))))
    "#;
    assert_eq!(eval_forward(source), "((planet earth) (star sun))");
}

#[test]
fn retract_fact_bang_removes_from_the_global_working_memory() {
    let source = r#"
        (assert-fact! (quote (planet earth)))
        (assert-fact! (quote (star sun)))
        (retract-fact! (quote (star sun)))
        *working-memory*
    "#;
    assert_eq!(eval_forward(source), "((planet earth))");
}

#[test]
fn retract_fact_bang_does_not_undo_facts_it_already_helped_derive() {
    // Deliberately demonstrates the Step 5a limitation: retracting the
    // source fact leaves the already-derived fact behind untouched, since
    // there is no support tracking yet (that's Step 5b).
    let source = r#"
        (assert-fact! (quote (orbits earth sun)))
        (assert-facts!
          (run (list (list (list (quote orbits) (logic-var (quote x)) (quote sun)) (list (quote has-mass) (logic-var (quote x)))))
                *working-memory*))
        (retract-fact! (quote (orbits earth sun)))
        *working-memory*
    "#;
    assert_eq!(eval_forward(source), "((has-mass earth))");
}

#[test]
fn assert_fact_tms_stores_an_axiom_with_no_support() {
    let source = r#"
        (assert-fact-tms! (quote (orbits earth sun)))
        *justified-memory*
    "#;
    assert_eq!(eval_forward(source), "(((orbits earth sun)))");
}

#[test]
fn run_tms_bang_derives_a_fact_with_its_support_recorded() {
    let source = r#"
        (assert-fact-tms! (quote (orbits earth sun)))
        (run-tms! (list (list (list (quote orbits) (logic-var (quote x)) (quote sun)) (list (quote has-mass) (logic-var (quote x))))))
        *justified-memory*
    "#;
    assert_eq!(
        eval_forward(source),
        "(((has-mass earth) (orbits earth sun)) ((orbits earth sun)))"
    );
}

#[test]
fn retract_fact_tms_bang_cascades_to_everything_it_supported() {
    let source = r#"
        (assert-fact-tms! (quote (orbits earth sun)))
        (run-tms! (list (list (list (quote orbits) (logic-var (quote x)) (quote sun)) (list (quote has-mass) (logic-var (quote x))))
                         (list (list (quote has-mass) (logic-var (quote x))) (list (quote heavy) (logic-var (quote x))))))
        (retract-fact-tms! (quote (orbits earth sun)))
        *justified-memory*
    "#;
    // orbits(earth,sun) was retracted, which was the sole support for
    // has-mass(earth), which was in turn the sole support for
    // heavy(earth) — both should cascade away, leaving nothing.
    assert_eq!(eval_forward(source), "()");
}

#[test]
fn retract_fact_tms_bang_leaves_independently_supported_facts_alone() {
    let source = r#"
        (assert-fact-tms! (quote (orbits earth sun)))
        (assert-fact-tms! (quote (orbits mars sun)))
        (run-tms! (list (list (list (quote orbits) (logic-var (quote x)) (quote sun)) (list (quote has-mass) (logic-var (quote x))))))
        (retract-fact-tms! (quote (orbits earth sun)))
        *justified-memory*
    "#;
    assert_eq!(
        eval_forward(source),
        "(((has-mass mars) (orbits mars sun)) ((orbits mars sun)))"
    );
}

#[test]
fn assert_fact_jtms_stores_an_axiom_with_an_empty_justification() {
    let source = r#"
        (assert-fact-jtms! (quote (orbits earth sun)))
        *jtms-memory*
    "#;
    assert_eq!(eval_forward(source), "(((orbits earth sun) ()))");
}

#[test]
fn run_jtms_bang_records_the_derivation_as_a_justification() {
    let source = r#"
        (assert-fact-jtms! (quote (orbits earth sun)))
        (run-jtms! (list (list (list (quote orbits) (logic-var (quote x)) (quote sun)) (list (quote has-mass) (logic-var (quote x))))))
        *jtms-memory*
    "#;
    assert_eq!(
        eval_forward(source),
        "(((has-mass earth) ((orbits earth sun))) ((orbits earth sun) ()))"
    );
}

#[test]
fn retract_fact_jtms_bang_cascades_when_the_only_justification_is_gone() {
    let source = r#"
        (assert-fact-jtms! (quote (orbits earth sun)))
        (run-jtms! (list (list (list (quote orbits) (logic-var (quote x)) (quote sun)) (list (quote has-mass) (logic-var (quote x))))))
        (retract-fact-jtms! (quote (orbits earth sun)))
        *jtms-memory*
    "#;
    assert_eq!(eval_forward(source), "()");
}

#[test]
fn retract_fact_jtms_bang_keeps_a_fact_with_a_surviving_independent_justification() {
    // has-mass(earth) is derivable two independent ways here: from
    // orbits(earth, sun) *and* asserted directly as its own axiom.
    // Retracting the orbits fact should not remove it, since the axiom
    // justification survives untouched.
    let source = r#"
        (assert-fact-jtms! (quote (orbits earth sun)))
        (assert-fact-jtms! (quote (has-mass earth)))
        (run-jtms! (list (list (list (quote orbits) (logic-var (quote x)) (quote sun)) (list (quote has-mass) (logic-var (quote x))))))
        (retract-fact-jtms! (quote (orbits earth sun)))
        *jtms-memory*
    "#;
    assert_eq!(eval_forward(source), "(((has-mass earth) ()))");
}

#[test]
fn fire_rule_multi_requires_every_condition_to_match_before_firing() {
    let source = r#"
        (fire-rule-multi
          (list (list (quote grandparent) (logic-var (quote x)) (logic-var (quote y)))
                (list (quote parent) (logic-var (quote x)) (logic-var (quote z)))
                (list (quote parent) (logic-var (quote z)) (logic-var (quote y))))
          (list (quote (parent alice bob)) (quote (parent bob charlie))))
    "#;
    assert_eq!(eval_forward(source), "((grandparent alice charlie))");
}

#[test]
fn fire_rule_multi_produces_nothing_when_one_condition_has_no_supporting_fact() {
    let source = r#"
        (fire-rule-multi
          (list (list (quote grandparent) (logic-var (quote x)) (logic-var (quote y)))
                (list (quote parent) (logic-var (quote x)) (logic-var (quote z)))
                (list (quote parent) (logic-var (quote z)) (logic-var (quote y))))
          (list (quote (parent alice bob))))
    "#;
    assert_eq!(eval_forward(source), "()");
}

#[test]
fn run_multi_derives_the_same_conclusion_reason_would_from_the_same_rule_literal() {
    // The exact rule/fact literals crates/sens/tests/reason.rs's
    // rule_with_condition_backward_chaining uses for backward-chaining —
    // proof that the two engines now genuinely share one rule language,
    // not just similar-looking syntax.
    let source = r#"
        (run-multi
          (list (list (list (quote grandparent) (logic-var (quote x)) (logic-var (quote y)))
                      (list (quote parent) (logic-var (quote x)) (logic-var (quote z)))
                      (list (quote parent) (logic-var (quote z)) (logic-var (quote y)))))
          (list (quote (parent alice bob)) (quote (parent bob charlie))))
    "#;
    assert_eq!(
        eval_forward(source),
        "((grandparent alice charlie) (parent alice bob) (parent bob charlie))"
    );
}

#[test]
fn run_multi_supports_negation_as_failure() {
    // Same bird/penguin example lib/reason.lisp's negation_as_failure test
    // uses for backward-chaining — now proven forward too. tweety (an
    // animal, not a penguin) becomes a bird; pingu (a penguin) does not.
    let source = r#"
        (run-multi
          (list (list (list (quote bird) (logic-var (quote x)))
                      (list (quote animal) (logic-var (quote x)))
                      (list (quote not) (list (quote penguin) (logic-var (quote x))))))
          (list (quote (animal tweety)) (quote (animal pingu)) (quote (penguin pingu))))
    "#;
    assert_eq!(
        eval_forward(source),
        "((bird tweety) (animal tweety) (animal pingu) (penguin pingu))"
    );
}

#[test]
fn match_negated_condition_fails_when_the_inner_pattern_matches() {
    let source = r#"
        (match-negated-condition (quote (penguin pingu)) (list (quote (penguin pingu))) (quote ()))
    "#;
    assert_eq!(eval_forward(source), "()");
}

#[test]
fn match_negated_condition_succeeds_when_the_inner_pattern_does_not_match() {
    let source = r#"
        (match-negated-condition (quote (penguin tweety)) (list (quote (penguin pingu))) (quote ()))
    "#;
    assert_eq!(eval_forward(source), "(())");
}

#[test]
fn run_multi_supports_or_conditions() {
    let source = r#"
        (run-multi
          (list (list (list (quote pet) (logic-var (quote x)))
                      (list (quote or) (list (quote cat) (logic-var (quote x))) (list (quote dog) (logic-var (quote x))))))
          (list (quote (cat tom)) (quote (dog rex)) (quote (fish nemo))))
    "#;
    assert_eq!(
        eval_forward(source),
        "((pet rex) (pet tom) (cat tom) (dog rex) (fish nemo))"
    );
}

#[test]
fn match_or_condition_unions_matches_from_every_alternative() {
    let source = r#"
        (match-or-condition (list (quote (cat tom)) (quote (dog rex))) (list (quote (cat tom)) (quote (dog rex)) (quote (fish nemo))) (quote ()))
    "#;
    assert_eq!(eval_forward(source), "(() ())");
}

#[test]
fn match_or_condition_returns_nothing_when_no_alternative_matches() {
    let source = r#"
        (match-or-condition (list (quote (cat tom)) (quote (dog rex))) (list (quote (fish nemo))) (quote ()))
    "#;
    assert_eq!(eval_forward(source), "()");
}

#[test]
fn run_multi_supports_and_conditions_nested_inside_or() {
    let source = r#"
        (run-multi
          (list (list (list (quote match) (logic-var (quote x)))
                      (list (quote or) (list (quote and) (list (quote cat) (logic-var (quote x))) (list (quote small) (logic-var (quote x))))
                                (list (quote dog) (logic-var (quote x))))))
          (list (quote (cat tom)) (quote (small tom)) (quote (dog rex)) (quote (cat garfield))))
    "#;
    assert_eq!(
        eval_forward(source),
        "((match rex) (match tom) (cat tom) (small tom) (dog rex) (cat garfield))"
    );
}

#[test]
fn match_and_condition_requires_every_sub_condition_to_match() {
    let source = r#"
        (match-and-condition (list (quote (cat tom)) (quote (small tom)))
                              (list (quote (cat tom)) (quote (small tom)) (quote (dog rex)))
                              (quote ()))
    "#;
    assert_eq!(eval_forward(source), "(())");
}

#[test]
fn match_and_condition_fails_when_one_sub_condition_has_no_match() {
    let source = r#"
        (match-and-condition (list (quote (cat tom)) (quote (small tom)))
                              (list (quote (cat tom)) (quote (dog rex)))
                              (quote ()))
    "#;
    assert_eq!(eval_forward(source), "()");
}

#[test]
fn run_jtms_multi_derives_a_multi_condition_grandparent_fact() {
    let source = r#"
        (assert-fact-jtms! (quote (parent alice bob)))
        (assert-fact-jtms! (quote (parent bob charlie)))
        (run-jtms-multi! (list (list (list (quote grandparent) (logic-var (quote x)) (logic-var (quote y)))
                                      (list (quote parent) (logic-var (quote x)) (logic-var (quote z)))
                                      (list (quote parent) (logic-var (quote z)) (logic-var (quote y))))))
        *jtms-memory*
    "#;
    assert_eq!(
        eval_forward(source),
        "(((grandparent alice charlie) ((parent bob charlie) (parent alice bob))) ((parent bob charlie) ()) ((parent alice bob) ()))"
    );
}

#[test]
fn retract_fact_jtms_bang_cascades_through_a_multi_condition_derivation() {
    let source = r#"
        (assert-fact-jtms! (quote (parent alice bob)))
        (assert-fact-jtms! (quote (parent bob charlie)))
        (run-jtms-multi! (list (list (list (quote grandparent) (logic-var (quote x)) (logic-var (quote y)))
                                      (list (quote parent) (logic-var (quote x)) (logic-var (quote z)))
                                      (list (quote parent) (logic-var (quote z)) (logic-var (quote y))))))
        (retract-fact-jtms! (quote (parent alice bob)))
        *jtms-memory*
    "#;
    assert_eq!(eval_forward(source), "(((parent bob charlie) ()))");
}

#[test]
fn assert_fact_adds_to_the_global_working_memory() {
    let source = r#"
        (assert-fact! (quote (planet earth)))
        (assert-fact! (quote (planet mars)))
        *working-memory*
    "#;
    assert_eq!(eval_forward(source), "((planet mars) (planet earth))");
}

#[test]
fn run_multi_supports_exists_conditions() {
    // Step 15: `(exists (unsolved ?u))` succeeds if at least one matching
    // fact exists, but — unlike an ordinary condition — binds nothing
    // back into the rule's own substitution: `?u` never appears in the
    // derived fact, only `?c` does.
    let source = r#"
        (run-multi
          (list (list (list (quote found) (logic-var (quote c)))
                      (list (quote cell) (logic-var (quote c)))
                      (list (quote exists) (list (quote unsolved) (logic-var (quote u))))))
          (list (quote (cell a)) (quote (unsolved x))))
    "#;
    assert_eq!(eval_forward(source), "((found a) (cell a) (unsolved x))");
}

#[test]
fn match_exists_condition_fails_when_no_fact_matches() {
    let source = r#"
        (run-multi
          (list (list (list (quote found) (logic-var (quote c)))
                      (list (quote cell) (logic-var (quote c)))
                      (list (quote exists) (list (quote unsolved) (logic-var (quote u))))))
          (list (quote (cell a))))
    "#;
    assert_eq!(eval_forward(source), "((cell a))");
}

#[test]
fn run_multi_supports_forall_conditions() {
    // Step 15: `(forall (item ?x) (color ?x red))` succeeds only if every
    // `item` fact's own `?x` also satisfies `(color ?x red)` — here both
    // `a` and `b` are red, so the rule fires.
    let source = r#"
        (run-multi
          (list (list (list (quote all-red))
                      (list (quote forall) (list (quote item) (logic-var (quote x))) (list (quote color) (logic-var (quote x)) (quote red)))))
          (list (quote (item a)) (quote (item b)) (quote (color a red)) (quote (color b red))))
    "#;
    assert_eq!(
        eval_forward(source),
        "((all-red) (item a) (item b) (color a red) (color b red))"
    );
}

#[test]
fn match_forall_condition_fails_when_one_candidate_does_not_satisfy_the_rest() {
    let source = r#"
        (run-multi
          (list (list (list (quote all-red))
                      (list (quote forall) (list (quote item) (logic-var (quote x))) (list (quote color) (logic-var (quote x)) (quote red)))))
          (list (quote (item a)) (quote (item b)) (quote (color a red)) (quote (color b blue))))
    "#;
    assert_eq!(
        eval_forward(source),
        "((item a) (item b) (color a red) (color b blue))"
    );
}
