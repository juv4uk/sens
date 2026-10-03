#![cfg(feature = "native-clips")]

use std::path::PathBuf;

use wsm_clips_kernel::{
    ClipsAbiAdapter, ClipsExecutionResult, ClipsKernel, LegacyAbiSemanticId as ClipsLegacyAbiSemanticId,
};
use wsm_common_lisp_kernel::{
    CommonLispAbiAdapter, CommonLispKernel, CommonLispRequest,
    LegacyAbiSemanticId as CommonLispLegacyAbiSemanticId,
};
use wsm_datalog_kernel::{
    Atom, Database, DatalogAbiAdapter, Evaluator, Program, Rule, Term, Value,
};
use wsm_kernel_c_abi::{
    WsmByteSpan, WsmKernelRequest, WsmKernelVTable, WsmMutableByteSpan, WsmStatus,
};
use wsm_native_result_types::{FourKernelObservation, ProducerSlot};
use wsm_prolog_kernel::{
    LegacyAbiSemanticId as PrologLegacyAbiSemanticId, PrologAbiAdapter, PrologKernel,
    PrologQuery, PrologRequest,
};

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
        .evaluate(&CommonLispRequest::new(
            CommonLispLegacyAbiSemanticId(5),
            "(car (cons 'left 'right))",
        ))
        .expect("real Common Lisp runtime");
    assert_eq!(String::from_utf8_lossy(&common_lisp.stdout).trim(), "LEFT");

    let prolog = PrologKernel::default()
        .execute(
            prolog_fixture(),
            &PrologRequest::new(
                PrologLegacyAbiSemanticId(3),
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
        Some(ClipsLegacyAbiSemanticId(6)),
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



const INVOKE_ID: u8 = 0b1010_1000;

fn invoke_vtable(vtable: WsmKernelVTable, payload: &[u8]) -> Vec<u8> {
    let start = vtable.start.expect("kernel start callback");
    let exchange = vtable.exchange.expect("kernel exchange callback");
    let stop = vtable.stop.expect("kernel stop callback");

    assert_eq!(unsafe { start(vtable.context) }, WsmStatus::Ok);

    let mut output = vec![0u8; 1024];
    let mut written = 0usize;
    let status = unsafe {
        exchange(
            vtable.context,
            WsmKernelRequest {
                semantic_id: INVOKE_ID,
                payload: WsmByteSpan {
                    ptr: payload.as_ptr(),
                    len: payload.len(),
                },
            },
            WsmMutableByteSpan {
                ptr: output.as_mut_ptr(),
                len: output.len(),
            },
            &mut written,
        )
    };
    assert_eq!(status, WsmStatus::Ok);
    output.truncate(written);

    assert_eq!(unsafe { stop(vtable.context) }, WsmStatus::Ok);
    output
}

#[test]
#[cfg(feature = "native-clips")]
fn one_invoke_sid_crosses_all_four_kernel_boundaries_without_owning_payload_semantics() {
    let common_lisp = CommonLispAbiAdapter::default();
    let common_lisp_output =
        invoke_vtable(common_lisp.vtable(), b"(car (cons 'left 'right))");
    assert_eq!(
        String::from_utf8_lossy(&common_lisp_output).trim(),
        "LEFT"
    );
    assert_eq!(
        common_lisp.last_legacy_abi_id().map(|id| id.0),
        Some(INVOKE_ID)
    );

    let prolog = PrologAbiAdapter::new(PrologKernel::default(), prolog_fixture(), "X");
    let prolog_output = invoke_vtable(prolog.vtable(), b"ancestor(alice, X)");
    assert_eq!(
        String::from_utf8_lossy(&prolog_output).trim(),
        "[bob,dave,carol]"
    );
    assert_eq!(prolog.last_legacy_abi_id().map(|id| id.0), Some(INVOKE_ID));

    let clips = ClipsAbiAdapter::new(
        "(defrule observe-signal (signal) => (assert (observed)))",
        "(signal)",
    );
    let clips_output = invoke_vtable(clips.vtable(), b"run");
    assert_eq!(String::from_utf8_lossy(&clips_output), "fired=1\n");
    assert_eq!(clips.last_legacy_abi_id().map(|id| id.0), Some(INVOKE_ID));

    let mut datalog_db = Database::new();
    datalog_db.add_fact("edge", vec![Value::int(1), Value::int(2)]);
    datalog_db.add_fact("edge", vec![Value::int(2), Value::int(3)]);
    datalog_db.add_fact("edge", vec![Value::int(3), Value::int(4)]);
    let mut datalog_program = Program::new();
    datalog_program.add_rule(Rule::with_id(
        "path-base",
        Atom::new("path", vec![Term::v("X"), Term::v("Y")]),
        vec![Atom::new("edge", vec![Term::v("X"), Term::v("Y")])],
    ));
    datalog_program.add_rule(Rule::with_id(
        "path-rec",
        Atom::new("path", vec![Term::v("X"), Term::v("Y")]),
        vec![
            Atom::new("edge", vec![Term::v("X"), Term::v("Z")]),
            Atom::new("path", vec![Term::v("Z"), Term::v("Y")]),
        ],
    ));
    let datalog = DatalogAbiAdapter::new(datalog_db, datalog_program);
    let datalog_output = invoke_vtable(datalog.vtable(), b"path");
    let datalog_text = String::from_utf8_lossy(&datalog_output);
    assert!(datalog_text.contains("path(1,4)"));
    assert_eq!(
        datalog.last_legacy_abi_id().map(|id| id.0),
        Some(INVOKE_ID)
    );

    // One shared SID names only the act of invocation. Payload interpretation
    // and native result domains remain producer-owned.
    assert_ne!(common_lisp_output, prolog_output);
    assert_ne!(prolog_output, clips_output);
    assert_ne!(clips_output, datalog_output);
}
