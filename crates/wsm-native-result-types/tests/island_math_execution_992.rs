#![cfg(feature = "native-clips")]

use std::fs;
use std::path::PathBuf;

use my_lisp::{parse, Expr, ExprKind};
use wsm_clips_kernel::ClipsKernel;
use wsm_common_lisp_kernel::{CommonLispKernel, CommonLispRequest};
use wsm_datalog_kernel::{
    DatalogAbiAdapter, Database, Program, SemanticId as DatalogSemanticId,
};
use wsm_kernel_c_abi::{
    WsmByteSpan, WsmKernelRequest, WsmMutableByteSpan, WsmStatus,
};
use wsm_prolog_kernel::{PrologKernel, PrologQuery, PrologRequest};

fn repo_root() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .parent()
        .and_then(|path| path.parent())
        .expect("repo root")
        .to_path_buf()
}

fn corpus_source() -> String {
    fs::read_to_string(repo_root().join("contracts/island-math-execution-992.lisp"))
        .expect("#992 execution corpus must exist")
}

fn pair_value<'a>(row: &'a [Expr], key: &str) -> Option<&'a Expr> {
    row.iter().find_map(|entry| {
        let ExprKind::Pair(k, v) = &entry.kind else {
            return None;
        };
        let ExprKind::Symbol(name) = &k.kind else {
            return None;
        };
        (&**name == key).then_some(v.as_ref())
    })
}

fn string_value<'a>(row: &'a [Expr], key: &str) -> &'a str {
    let value = pair_value(row, key).expect("corpus field");
    match &value.kind {
        ExprKind::String(value) | ExprKind::Symbol(value) => value.as_ref(),
        other => panic!("corpus field {key} must be string/symbol, got {other:?}"),
    }
}

fn case_row<'a>(top: &'a [Expr], case_id: &str) -> &'a [Expr] {
    top.iter()
        .find_map(|expr| {
            let ExprKind::List(items) = &expr.kind else {
                return None;
            };
            let Some(id) = pair_value(items, "case-id") else {
                return None;
            };
            let ExprKind::String(id) | ExprKind::Symbol(id) = &id.kind else {
                return None;
            };
            (id.as_ref() == case_id).then_some(items.as_ref())
        })
        .expect("named #992 corpus case")
}

fn semantic_id(bits: &str) -> u8 {
    u8::from_str_radix(bits, 2).expect("8-bit binary semantic id")
}

fn prolog_fixture() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .join("../wsm-prolog-kernel/tests/fixtures/family.pl")
}

fn datalog_exchange(adapter: &DatalogAbiAdapter, query: &[u8], semantic_id: u8) -> (WsmStatus, Vec<u8>) {
    let vtable = adapter.vtable();
    let mut output = vec![0u8; 256];
    let mut written = 0usize;
    let status = unsafe {
        vtable.exchange.expect("exchange callback")(
            vtable.context,
            WsmKernelRequest {
                semantic_id,
                payload: WsmByteSpan {
                    ptr: query.as_ptr(),
                    len: query.len(),
                },
            },
            WsmMutableByteSpan {
                ptr: output.as_mut_ptr(),
                len: output.len(),
            },
            &mut written,
        )
    };
    output.truncate(written.min(output.len()));
    (status, output)
}

#[test]
fn corpus_case_has_one_explicit_probe_per_island() {
    let forms = parse(&corpus_source()).expect("#992 corpus parses");
    assert_eq!(forms.len(), 1);

    let ExprKind::List(top) = &forms[0].kind else {
        panic!("#992 corpus top form must be a list");
    };
    assert!(matches!(
        &top[0].kind,
        ExprKind::Symbol(name) if &**name == "island-math-execution/1"
    ));

    let row = case_row(top, "add-small-exact-integer");
    assert_eq!(string_value(row, "operation"), "+");
    assert_eq!(string_value(row, "semantic-id"), "00001100");
    assert!(pair_value(row, "common-lisp-form").is_some());
    assert!(pair_value(row, "prolog-goal").is_some());
    assert!(pair_value(row, "prolog-template").is_some());
    assert!(pair_value(row, "clips-rule").is_some());
    assert!(pair_value(row, "clips-trigger").is_some());
    assert!(pair_value(row, "datalog-query").is_some());
    assert_eq!(string_value(row, "datalog-status"), "unsupported-current-kernel");
}

#[test]
fn one_corpus_case_drives_all_four_island_observations() {
    let forms = parse(&corpus_source()).expect("#992 corpus parses");
    let ExprKind::List(top) = &forms[0].kind else {
        panic!("#992 corpus top form must be a list");
    };
    let row = case_row(top, "add-small-exact-integer");

    let sid = semantic_id(string_value(row, "semantic-id"));
    let expected = string_value(row, "expected-comparison");
    let common_lisp_form = string_value(row, "common-lisp-form");
    let prolog_goal = string_value(row, "prolog-goal");
    let prolog_template = string_value(row, "prolog-template");
    let clips_rule = string_value(row, "clips-rule");
    let clips_trigger = string_value(row, "clips-trigger");
    let datalog_query = string_value(row, "datalog-query");

    // Common Lisp: preserve the exact producer-native stdout before comparison.
    let common_lisp = CommonLispKernel::default()
        .evaluate(&CommonLispRequest::new(sid, common_lisp_form))
        .expect("SBCL arithmetic witness");
    assert_eq!(common_lisp.semantic_id.0, sid);
    let common_lisp_native = String::from_utf8_lossy(&common_lisp.stdout).trim().to_owned();
    assert_eq!(common_lisp_native, expected);

    // Prolog: preserve its canonical list/domain before comparison.
    let prolog = PrologKernel::default()
        .execute(
            prolog_fixture(),
            &PrologRequest::new(
                sid,
                PrologQuery::new(prolog_goal, prolog_template),
            ),
        )
        .expect("SWI-Prolog arithmetic witness");
    assert_eq!(prolog.semantic_id.0, sid);
    let prolog_native = String::from_utf8_lossy(&prolog.stdout).trim().to_owned();
    assert_eq!(prolog_native, "[5]");

    // CLIPS: the native witness proves the arithmetic test itself in the
    // producer kernel; its native observation remains a fired-rule count.
    let clips_kernel = ClipsKernel::discover().expect("real CLIPS runtime");
    let clips_env = clips_kernel
        .create_environment()
        .expect("native CLIPS environment");
    clips_env.build(clips_rule).expect("native CLIPS arithmetic rule");
    let _trigger = clips_env
        .assert_string(clips_trigger)
        .expect("native CLIPS trigger fact");
    let facts_before = clips_env.fact_count();
    let fired = clips_env.run(-1);
    let facts_after = clips_env.fact_count();

    assert_eq!(fired, 1, "the CLIPS arithmetic condition must be true");
    assert_eq!(facts_before, 1);
    assert_eq!(facts_after, 2);
    let clips_native = format!("fired={fired}");
    assert_eq!(clips_native, "fired=1");

    // Datalog: same corpus case is sent to the real current kernel, but its
    // native payload language is relational. Arithmetic remains an explicit
    // capability gap, so the comparison is intentionally not performed.
    let datalog = DatalogAbiAdapter::new(Database::new(), Program::new());
    let vtable = datalog.vtable();
    assert_eq!(
        unsafe { vtable.start.expect("start callback")(vtable.context) },
        WsmStatus::Ok
    );
    let (status, output) = datalog_exchange(&datalog, datalog_query.as_bytes(), sid);
    assert_eq!(status, WsmStatus::Ok);
    assert!(output.is_empty(), "Datalog must not invent arithmetic evaluation");
    assert_eq!(
        datalog.last_semantic_id(),
        Some(DatalogSemanticId(sid))
    );
    assert_eq!(
        unsafe { vtable.stop.expect("stop callback")(vtable.context) },
        WsmStatus::Ok
    );

    // The normalized comparison is deliberately one-way: only the producer
    // domains that actually expose this operation are compared to the expected
    // mathematical result. Datalog stays an explicit gap rather than a fake
    // fourth result.
    assert_eq!(common_lisp_native, expected);
    assert_eq!(prolog_native, "[5]");
    assert_eq!(clips_native, "fired=1");
}
