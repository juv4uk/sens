//! Exercises lib/narrate.my — the "structure -> text" half of the bridge
//! from private/lisp-to-knowledge.md §6, the reverse of lib/understand.lisp's
//! "text -> structure" half.
//! Pereviriaie lib/narrate.my — polovynu mostu "struktura -> tekst" z
//! private/lisp-to-knowledge.md §6, obernenu do "tekst -> struktura" z
//! lib/understand.my.
//! Prüft lib/narrate.my — die Hälfte "Struktur -> Text" der Brücke aus
//! private/lisp-to-knowledge.md §6, das Gegenstück zu "Text -> Struktur"
//! aus lib/understand.my.

use sens::{eval_program, Session};

fn eval_narrate(source: &str) -> String {
    let mut session = Session::default();
    eval_program(include_str!("../../../lib/core.lisp"), &mut session).unwrap();
    eval_program(include_str!("../../../lib/unify.lisp"), &mut session).unwrap();
    eval_program(include_str!("../../../lib/reason.lisp"), &mut session).unwrap();
    eval_program(include_str!("../../../lib/understand.lisp"), &mut session).unwrap();
    eval_program(include_str!("../../../lib/narrate.lisp"), &mut session).unwrap();
    eval_program(source, &mut session)
        .unwrap_or_else(|e| panic!("evaluation failed: {e}\nsource: {source}"))
        .value
        .to_string()
}

#[test]
fn narrate_fact_undoes_understand_is_a() {
    // Round-trip: understand turns "earth is a planet" into a fact, and
    // narrate-fact turns that fact back into the original words.
    let source = r#"
        (narrate-fact (car (understand (quote (earth is a planet)))))
    "#;
    assert_eq!(eval_narrate(source), "(earth is a planet)");
}

#[test]
fn narrate_fact_undoes_understand_relation() {
    let source = r#"
        (narrate-fact (car (understand (quote (earth orbits sun)))))
    "#;
    assert_eq!(eval_narrate(source), "(earth orbits sun)");
}

#[test]
fn narrate_provenance_explains_a_bare_fact_with_no_because() {
    let source = r#"
        (let ((rules (quote (((parent alice bob))))))
             (let* ((results (reason (quote (parent alice bob)) rules))
                    (proof (second (car results))))
               (narrate-provenance (provenance proof))))
    "#;
    assert_eq!(eval_narrate(source), "(alice parent bob)");
}

#[test]
fn narrate_provenance_explains_a_derived_fact_with_because_and_and() {
    let source = r#"
        (let ((rules (quote (
                 ((grandparent (var x) (var y)) (parent (var x) (var z)) (parent (var z) (var y)))
                 ((parent alice bob))
                 ((parent bob charlie))
               ))))
             (let* ((results (reason (list (quote grandparent) (logic-var (quote a)) (logic-var (quote b))) rules))
                    (proof (second (car results))))
               (narrate-provenance (provenance proof))))
    "#;
    let output = eval_narrate(source);
    // The two sub-facts are ground (parent alice bob / parent bob
    // charlie), joined by "because"/"and" — but the derived head itself
    // already shows the documented limitation: `(var (x . 0))` and
    // `(var (y . 0))`, not `alice`/`charlie`. See the dedicated test below
    // for why, rather than leaving it as an unlabeled surprise here.
    assert_eq!(
        output,
        "((var (x . 0)) grandparent (var (y . 0)) because alice parent bob and bob parent charlie)"
    );
}

#[test]
fn narrate_provenance_surfaces_unresolved_variables_in_a_derived_rule_head() {
    // lib/narrate.lisp's own header comment documents this limitation:
    // `provenance` doesn't carry the query's final substitution, only the
    // proof tree — so a rule's own head, as stored in that tree, keeps
    // whatever `(var name)` placeholders `prove-rule` renamed it to,
    // even though `reason`'s top-level result *does* know grandparent is
    // really (alice, charlie) once its substitution is applied elsewhere.
    // This test exists so that limitation can't silently regress into
    // "actually resolved after all" without a test noticing — or silently
    // get worse without anyone deciding that on purpose.
    let source = r#"
        (let ((rules (quote (
                 ((grandparent (var x) (var y)) (parent (var x) (var z)) (parent (var z) (var y)))
                 ((parent alice bob))
                 ((parent bob charlie))
               ))))
             (let* ((results (reason (list (quote grandparent) (logic-var (quote a)) (logic-var (quote b))) rules))
                    (proof (second (car results)))
                    (narration (narrate-provenance (provenance proof))))
               ; First three words = the narrated head. If this limitation
               ; were ever fixed (provenance starting to carry/apply the
               ; final substitution), these would read `(alice grandparent
               ; charlie)` instead — this test would then fail loudly,
               ; which is the point: a real fix should update this test on
               ; purpose, not slide past it unnoticed.
               (list (car narration) (second narration) (third narration))))
    "#;
    assert_eq!(
        eval_narrate(source),
        "((var (x . 0)) grandparent (var (y . 0)))"
    );
}

#[test]
fn narrate_answer_uses_the_ground_query_and_the_real_proof_premises() {
    let source = r#"
        (let* ((rules (quote (((has (var x) mass) (planet (var x)))
                        ((planet earth)))))
               (goal (quote (has earth mass)))
               (proof (second (car (reason goal rules)))))
          (narrate-answer goal proof))
    "#;
    assert_eq!(
        eval_narrate(source),
        "(earth has mass because earth is a planet)"
    );
}
