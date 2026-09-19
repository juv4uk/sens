use std::path::PathBuf;

use wsm_clips_kernel::{ClipsExecutionResult, ClipsKernel, SemanticId as ClipsSemanticId};
use wsm_common_lisp_kernel::{CommonLispKernel, CommonLispRequest};
use wsm_datalog_kernel::{Atom, Database, Evaluator, Program, Rule, Term, Value};
use wsm_native_result_types::{FourKernelObservation, ProducerSlot};
use wsm_prolog_kernel::{PrologKernel, PrologQuery, PrologRequest};

fn prolog_fixture() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .join("../wsm-prolog-kernel/tests/fixtures/family.pl")
}

fn datalog_closure() -> Database {
    let mut db = Database::new();
    db.add_fact("edge", vec![Value::sym("a"), Value::sym("b")]);
    db.add_fact("edge", vec![Value::sym("b"), Value::sym("c")]);

    let mut program = Program::new();
    program.add_rule(Rule::with_id(
        "path-base",
        Atom::new("path", vec![Term::v("X"), Term::v("Y")]),
        vec![Atom::new("edge", vec![Term::v("X"), Term::v("Y")])],
    ));
    program.add_rule(Rule::with_id(
        "path-step",
        Atom::new("path", vec![Term::v("X"), Term::v("Z")]),
        vec![
            Atom::new("edge", vec![Term::v("X"), Term::v("Y")]),
            Atom::new("path", vec![Term::v("Y"), Term::v("Z")]),
        ],
    ));
    Evaluator::naive_fixpoint(&program, &mut db);
    db
}

#[test]
#[cfg(feature = "native-clips")]
fn four_real_kernels_keep_their_native_results_side_by_side() {
    let common_lisp = CommonLispKernel::default()
        .evaluate(&CommonLispRequest::new(5, "(car (cons 'left 'right))"))
        .expect("real Common Lisp runtime");
    assert_eq!(String::from_utf8_lossy(&common_lisp.stdout).trim(), "LEFT");

    let prolog = PrologKernel::default()
        .execute(
            prolog_fixture(),
            &PrologRequest::new(
                3,
                PrologQuery::new("ancestor(alice, X)", "X"),
            ),
        )
        .expect("real SWI-Prolog runtime");
    assert_eq!(
        String::from_utf8_lossy(&prolog.stdout).trim(),
        "[bob,dave,carol]"
    );

    let clips_kernel = ClipsKernel::discover().expect("real CLIPS runtime");
    let clips_env = clips_kernel
        .create_environment()
        .expect("native CLIPS environment");
    clips_env
        .build("(defrule observe-signal (signal) => (assert (observed)))")
        .expect("native CLIPS rule");
    let _seed = clips_env
        .assert_string("(signal)")
        .expect("native CLIPS fact");
    let facts_before = clips_env.fact_count();
    let fired = clips_env.run(-1);
    let facts_after = clips_env.fact_count();
    let clips = ClipsExecutionResult::new(
        Some(ClipsSemanticId(6)),
        fired,
        facts_before,
        facts_after,
    );
    assert_eq!(clips.fired, 1);
    assert_eq!(clips.facts_before, 1);
    assert_eq!(clips.facts_after, 2);

    let datalog = datalog_closure();
    assert!(datalog
        .relation("path")
        .contains(&vec![Value::sym("a"), Value::sym("c")]));
    assert!(datalog.generation_count() >= 2);

    let observation = FourKernelObservation::new(
        common_lisp,
        prolog,
        clips,
        datalog,
    );

    // Producer identity is retained by concrete field type and field name.
    assert_eq!(
        FourKernelObservation::producer_names(),
        ["common-lisp", "prolog", "clips", "datalog"]
    );

    // No domain is reconstructed from another: each original producer result
    // remains directly inspectable in its own native representation.
    assert_eq!(
        String::from_utf8_lossy(&observation.common_lisp.stdout).trim(),
        "LEFT"
    );
    assert_eq!(
        String::from_utf8_lossy(&observation.prolog.stdout).trim(),
        "[bob,dave,carol]"
    );
    assert_eq!(observation.clips.fired, 1);
    assert!(observation
        .datalog
        .relation("path")
        .contains(&vec![Value::sym("a"), Value::sym("c")]));

    // A semantic graph may refer to result slots without replacing their
    // producer-native values. The relation byte is intentionally opaque here:
    // Lisp owns its meaning.
    const RELATION_CAN_OBSERVE: u8 = 0b1100_0011;
    let refs = FourKernelObservation::result_refs(42);
    let graph_edge = (refs[0], RELATION_CAN_OBSERVE, refs[2]);
    assert_eq!(graph_edge.0.producer, ProducerSlot::CommonLisp);
    assert_eq!(graph_edge.2.producer, ProducerSlot::Clips);

    // Referencing the results did not normalize or mutate them.
    assert_eq!(
        String::from_utf8_lossy(&observation.common_lisp.stdout).trim(),
        "LEFT"
    );
    assert_eq!(observation.clips.fired, 1);
}

