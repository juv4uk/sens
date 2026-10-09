//! Every witness here drives the real CLIPS 6.4 runtime, so the file builds
//! only with the `native-clips` feature, where CI provides libclips
//! (.github/workflows/clips-kernel-test.yml, native-clips-642).
#![cfg(feature = "native-clips")]

use wsm_clips_kernel::{ClipsAbiAdapter, LegacyAbiSemanticId};
use wsm_clips_kernel::ClipsKernel;
use wsm_kernel_c_abi::{
    WsmByteSpan, WsmKernelKind, WsmKernelRequest, WsmMutableByteSpan, WsmStatus,
};

const PROBE_ID: u8 = 0b0000_0110;

fn exchange_with_sid(
    adapter: &ClipsAbiAdapter,
    semantic_id: u8,
    payload: &[u8],
) -> (WsmStatus, Vec<u8>) {
    let vtable = adapter.vtable();
    let mut output = vec![0u8; 128];
    let mut written = 0usize;
    let status = unsafe {
        vtable.exchange.expect("exchange")(
            vtable.context,
            WsmKernelRequest {
                semantic_id,
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
    output.truncate(written.min(output.len()));
    (status, output)
}

fn exchange(adapter: &ClipsAbiAdapter, command: &[u8]) -> (WsmStatus, Vec<u8>) {
    let vtable = adapter.vtable();
    let mut output = vec![0u8; 128];
    let mut written = 0usize;
    let status = unsafe {
        vtable.exchange.expect("exchange")(
            vtable.context,
            WsmKernelRequest {
                semantic_id: PROBE_ID,
                payload: WsmByteSpan {
                    ptr: command.as_ptr(),
                    len: command.len(),
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
#[cfg(feature = "native-clips")]
fn direct_native_clips_642_smoke() {
    let kernel = ClipsKernel::discover().expect("load external CLIPS 6.4 runtime");
    let environment = kernel
        .create_environment()
        .expect("create native CLIPS environment");
    environment
        .build("(defrule observe-signal (signal) => (assert (observed)))")
        .expect("build native CLIPS rule");
    let fact = environment
        .assert_string("(signal)")
        .expect("assert native CLIPS fact");
    assert_eq!(environment.fact_count(), 1, "seed fact enters working memory");
    assert_eq!(environment.run(-1), 1, "native CLIPS fires the rule");
    assert_eq!(
        environment.fact_count(),
        2,
        "rule firing asserts a second working-memory fact"
    );
    assert_eq!(
        environment.eval_bytes("(+ 2 3)").expect("native CLIPS Eval"),
        b"5"
    );
    environment
        .retract(fact)
        .expect("retract the original seed fact");
    assert_eq!(
        environment.fact_count(),
        1,
        "retract visibly changes native CLIPS working memory"
    );
}

#[test]
fn opaque_legacy_abi_id_crosses_shared_abi_into_native_clips_agenda() {
    let adapter = ClipsAbiAdapter::new(
        "(defrule observe-signal (signal) => (assert (observed)))",
        "(signal)",
    );
    let vtable = adapter.vtable();
    assert_eq!(vtable.kernel, WsmKernelKind::Clips);
    assert_eq!(
        unsafe { vtable.start.expect("start")(vtable.context) },
        WsmStatus::Ok
    );

    let (status, output) = exchange(&adapter, b"run");
    assert_eq!(status, WsmStatus::Ok);
    assert_eq!(String::from_utf8_lossy(&output), "fired=1\n");
    assert_eq!(adapter.last_legacy_abi_id(), Some(LegacyAbiSemanticId(PROBE_ID)));
    assert_eq!(adapter.last_fired(), Some(1));

    assert_eq!(
        unsafe { vtable.stop.expect("stop")(vtable.context) },
        WsmStatus::Ok
    );
}

#[test]
fn semantic_add_executes_from_sid8_and_arguments_only() {
    let adapter = ClipsAbiAdapter::new(
        "(defrule observe-signal (signal) => (assert (observed)))",
        "(signal)",
    );
    let vtable = adapter.vtable();
    assert_eq!(
        unsafe { vtable.start.expect("start")(vtable.context) },
        WsmStatus::Ok
    );

    let (status, output) = exchange_with_sid(&adapter, 0b0000_1100, b"2 3");
    assert_eq!(status, WsmStatus::Ok);
    assert_eq!(output, b"5");
    assert_eq!(
        adapter.last_legacy_abi_id(),
        Some(LegacyAbiSemanticId(0b0000_1100))
    );
    assert_eq!(adapter.last_eval_output(), Some(&b"5"[..]));

    let (status, output) =
        exchange_with_sid(&adapter, 0b0000_1100, b"- 7 3");
    assert_eq!(
        status,
        WsmStatus::InvalidArgument,
        "operator text must not override the + SID"
    );
    assert!(output.is_empty());

    assert_eq!(
        unsafe { vtable.stop.expect("stop")(vtable.context) },
        WsmStatus::Ok
    );
}

#[test]
fn semantic_abi_rejects_text_function_dispatch_even_when_native_clips_can_eval_it() {
    let adapter = ClipsAbiAdapter::new(
        "(defrule observe-signal (signal) => (assert (observed)))",
        "(signal)",
    );
    let vtable = adapter.vtable();
    assert_eq!(
        unsafe { vtable.start.expect("start")(vtable.context) },
        WsmStatus::Ok
    );

    let (status, output) = exchange(&adapter, b"eval:(+ 2 3)");
    assert_eq!(
        status,
        WsmStatus::InvalidArgument,
        "semantic ABI must not accept a function identity encoded as operator text"
    );
    assert!(
        output.is_empty(),
        "rejected semantic text-dispatch must not produce a semantic result"
    );
    assert_eq!(
        adapter.last_legacy_abi_id(),
        None,
        "rejected text-dispatch must not be recorded as semantic SID execution"
    );
    assert_eq!(
        adapter.last_eval_output(),
        None,
        "raw native Eval observation must stay outside the semantic SID8 ABI"
    );

    assert_eq!(
        unsafe { vtable.stop.expect("stop")(vtable.context) },
        WsmStatus::Ok
    );
}

#[test]
fn retracting_native_fact_changes_reachable_agenda_before_run() {
    let adapter = ClipsAbiAdapter::new(
        "(defrule observe-signal (signal) => (assert (observed)))",
        "(signal)",
    );
    let vtable = adapter.vtable();
    assert_eq!(
        unsafe { vtable.start.expect("start")(vtable.context) },
        WsmStatus::Ok
    );

    let (retract_status, retract_output) = exchange(&adapter, b"retract");
    assert_eq!(retract_status, WsmStatus::Ok);
    assert_eq!(String::from_utf8_lossy(&retract_output), "retracted\n");

    let (run_status, run_output) = exchange(&adapter, b"run");
    assert_eq!(run_status, WsmStatus::Ok);
    assert_eq!(String::from_utf8_lossy(&run_output), "fired=0\n");

    assert_eq!(
        unsafe { vtable.stop.expect("stop")(vtable.context) },
        WsmStatus::Ok
    );
}