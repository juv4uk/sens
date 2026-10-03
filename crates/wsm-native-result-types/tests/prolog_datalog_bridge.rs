use std::fs;
use std::path::PathBuf;

use sens::{eval_program, load_core_library, parse, Expr, ExprKind, Session};
use wsm_datalog_kernel::{Atom, Database, Evaluator, Program, Rule, Term, Value};
use wsm_native_result_types::{
    FourKernelObservation, ProducerSlot, ProvenanceEdge, ProvenanceEdgeType,
};
use wsm_prolog_kernel::{LegacyAbiSemanticId, 
    decode_canonical_atom_list, PrologKernel, PrologQuery, PrologRequest,
};

const INVOKE_ID: u8 = 0b1010_1000;

fn repo_file(path: &str) -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .join("../..")
        .join(path)
}

fn prolog_fixture() -> PathBuf {
    repo_file("crates/wsm-prolog-kernel/tests/fixtures/family.pl")
}

fn load_bridge(session: &mut Session) {
    let source = fs::read_to_string(repo_file("lib/bridge/prolog-to-datalog.lisp"))
        .expect("#803 bridge Lisp source");
    eval_program(&source, session).expect("#803 bridge Lisp must load");
}

fn load_scheduler(session: &mut Session) {
    let source = fs::read_to_string(repo_file("lib/life-1-scheduler.lisp"))
        .expect("#801 scheduler Lisp source");
    eval_program(&source, session).expect("#801 scheduler Lisp must load");
}

fn eval_text(source: &str, session: &mut Session) -> String {
    eval_program(source, session)
        .expect("LIFE scheduler expression must execute")
        .value
        .to_string()
}

fn list_items(expr: &Expr) -> &[Expr] {
    match &expr.kind {
        ExprKind::List(items) => items,
        other => panic!("expected proper list, got {other:?}"),
    }
}

fn symbol(expr: &Expr) -> &str {
    match &expr.kind {
        ExprKind::Symbol(value) => value,
        other => panic!("expected symbol, got {other:?}"),
    }
}

fn projected_facts(projected: &str) -> (String, Vec<(String, String)>) {
    let forms = parse(projected).expect("Lisp projection result must be readable data");
    assert_eq!(forms.len(), 1);
    let outer = list_items(&forms[0]);
    assert_eq!(symbol(&outer[0]), "projection-result");

    let source_ref_row = outer
        .iter()
        .skip(1)
        .map(list_items)
        .find(|row| row.first().is_some_and(|entry| symbol(entry) == "source-ref"))
        .expect("projection must preserve source-ref");
    assert_eq!(source_ref_row.len(), 2);
    let source_ref = symbol(&source_ref_row[1]).to_string();

    let facts_row = outer
        .iter()
        .skip(1)
        .map(list_items)
        .find(|row| row.first().is_some_and(|entry| symbol(entry) == "facts"))
        .expect("projection must emit facts");
    assert_eq!(facts_row.len(), 2);

    let facts = list_items(&facts_row[1])
        .iter()
        .map(|fact| {
            let fields = list_items(fact);
            assert_eq!(fields.len(), 2);
            (symbol(&fields[0]).to_string(), symbol(&fields[1]).to_string())
        })
        .collect();

    (source_ref, facts)
}

#[test]
fn real_prolog_lisp_projection_real_datalog_preserves_domains() {
    let prolog = PrologKernel::default()
        .execute(
            prolog_fixture(),
            &PrologRequest::new(
                LegacyAbiSemanticId(INVOKE_ID),
                PrologQuery::new("ancestor(alice, X)", "X"),
            ),
        )
        .expect("real SWI-Prolog runtime");

    let values = decode_canonical_atom_list(&prolog.stdout)
        .expect("bounded Prolog canonical atom list");
    assert_eq!(values, ["bob", "dave", "carol"]);

    let source_observation = format!(
        "(prolog-substitution-observation \
           (source-ref observation-42) \
           (variable ancestor-answer) \
           (values {}))",
        values.join(" ")
    );

    let mut session = Session::default();
    load_core_library(&mut session).expect("core library");
    load_bridge(&mut session);

    // Lisp owns the admitted mapping from selected variable role + bound
    // values into ordinary Datalog fact data.
    let projected = eval_program(
        &format!(
            "(prolog-substitutions-to-datalog-facts (quote {source_observation}))"
        ),
        &mut session,
    )
    .expect("Lisp-owned projection must execute")
    .value
    .to_string();

    let (source_ref, facts) = projected_facts(&projected);
    assert_eq!(source_ref, "observation-42");
    assert_eq!(
        facts,
        vec![
            ("ancestor-answer".to_string(), "bob".to_string()),
            ("ancestor-answer".to_string(), "dave".to_string()),
            ("ancestor-answer".to_string(), "carol".to_string()),
        ]
    );

    // Host materializes only facts already selected by Lisp.
    let mut db = Database::new();
    for (relation, value) in &facts {
        db.add_fact(relation, vec![Value::sym(value)]);
    }

    let mut program = Program::new();
    program.add_rule(Rule::with_id(
        "life-1-projected-ancestor",
        Atom::new("life-ancestor", vec![Term::v("Who")]),
        vec![Atom::new("ancestor-answer", vec![Term::v("Who")])],
    ));
    Evaluator::naive_fixpoint(&program, &mut db);

    assert_eq!(db.relation("life-ancestor").len(), 3);
    assert!(db.relation("life-ancestor").contains(&vec![Value::sym("bob")]));
    assert!(db.relation("life-ancestor").contains(&vec![Value::sym("dave")]));
    assert!(db.relation("life-ancestor").contains(&vec![Value::sym("carol")]));
    assert!(db.generation_count() >= 2);

    // LIFE-1 trace mechanics retain only stable identities and the admitted
    // bridge contract. They do not decode or normalize either native domain.
    let refs = FourKernelObservation::observation_refs(42, Some(INVOKE_ID));
    let prolog_ref = refs[1];
    let datalog_ref = refs[3];
    let edge = ProvenanceEdge {
        edge_id: 1,
        edge_type: ProvenanceEdgeType::ProjectedInto,
        from_observation: prolog_ref,
        bridge_contract_ref: "prolog-substitutions-to-datalog-facts".to_string(),
        to_observation: datalog_ref,
    };

    assert_eq!(edge.from_observation.producer, ProducerSlot::Prolog);
    assert_eq!(edge.from_observation.native_slot, ProducerSlot::Prolog);
    assert_eq!(edge.to_observation.producer, ProducerSlot::Datalog);
    assert_eq!(edge.to_observation.native_slot, ProducerSlot::Datalog);
    assert_eq!(edge.from_observation.observation_id, 42);
    assert_eq!(edge.to_observation.observation_id, 42);
    assert_eq!(edge.from_observation.semantic_id, Some(INVOKE_ID));
    assert_eq!(edge.to_observation.semantic_id, Some(INVOKE_ID));
    assert_eq!(edge.edge_type, ProvenanceEdgeType::ProjectedInto);
    assert_eq!(
        edge.bridge_contract_ref,
        "prolog-substitutions-to-datalog-facts"
    );

    // #903: scheduler consumes only explicit readiness/provenance data.
    load_scheduler(&mut session);
    let invocation = format!(
        "(pending-invocation (producer datalog) (trigger (projection-ready {})) (provenance-ref {}) (priority ordinary) (semantic-id \"{:08b}\"))",
        edge.bridge_contract_ref,
        source_ref,
        INVOKE_ID
    );
    let projection_ready =
        format!("(projection-ready {} {})", edge.bridge_contract_ref, source_ref);

    assert_eq!(
        eval_text(
            &format!(
                "(life-scheduler-projection-ready? (quote {invocation}) (quote ({projection_ready})))"
            ),
            &mut session,
        ),
        "present"
    );
    assert_eq!(
        eval_text(
            &format!(
                "(life-scheduler-projection-ready? (quote {invocation}) (quote ((projection-ready {} observation-99))))",
                edge.bridge_contract_ref
            ),
            &mut session,
        ),
        "absent"
    );
    assert_eq!(
        eval_text(
            &format!(
                "(life-scheduler-projection-ready? (quote {invocation}) (quote ((projection-ready different-bridge-contract {}))))",
                source_ref
            ),
            &mut session,
        ),
        "absent"
    );

    let selection = eval_text(
        &format!(
            "(life-scheduler-select-ready (list (quote {invocation})) (quote ({projection_ready})))"
        ),
        &mut session,
    );
    assert!(
        selection.starts_with("(scheduler-selection ready "),
        "real LIFE readiness did not activate Datalog: {selection}"
    );
    assert_eq!(
        eval_text(
            "(life-scheduler-quiescence (quote ()) (quote ()) (quote no-transition-required))",
            &mut session,
        ),
        "(quiescence-state quiescent)"
    );

    // Projection did not normalize or mutate the producer-native observation.
    assert_eq!(
        String::from_utf8_lossy(&prolog.stdout).trim(),
        "[bob,dave,carol]"
    );
}

#[test]
fn malformed_projection_input_is_named_failure_not_false() {
    let mut session = Session::default();
    load_core_library(&mut session).expect("core library");
    load_bridge(&mut session);

    let result = eval_program(
        "(prolog-substitutions-to-datalog-facts \
           (quote (prolog-substitution-observation \
             (variable ancestor-answer) \
             (values bob))))",
        &mut session,
    )
    .expect("malformed projection input returns ordinary named data")
    .value
    .to_string();

    assert_eq!(result, "(projection-failure missing-source-ref)");
}
