use std::path::PathBuf;

use wsm_kernel_c_abi::{
    WsmByteSpan, WsmKernelKind, WsmKernelRequest, WsmMutableByteSpan, WsmStatus,
};
use wsm_prolog_kernel::{PrologAbiAdapter, PrologKernel, LegacyAbiSemanticId};

const PROBE_ID: u8 = 0b0000_0011;

fn swipl_available() -> bool {
    PrologKernel::default().version().is_ok()
}

fn fixture() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("tests/fixtures/family.pl")
}

#[test]
fn opaque_legacy_abi_id_crosses_same_c_abi_into_real_prolog_backtracking() {
    if !swipl_available() {
        eprintln!("SKIP: swipl is not installed on this machine");
        return;
    }

    let adapter = PrologAbiAdapter::new(PrologKernel::default(), fixture(), "X");
    let vtable = adapter.vtable();

    assert_eq!(vtable.kernel, WsmKernelKind::Prolog);
    assert_eq!(
        unsafe { vtable.start.expect("start")(vtable.context) },
        WsmStatus::Ok
    );

    let goal = b"ancestor(alice, X)";
    let mut output = [0u8; 128];
    let mut written = 0usize;

    let status = unsafe {
        vtable.exchange.expect("exchange")(
            vtable.context,
            WsmKernelRequest {
                semantic_id: PROBE_ID,
                payload: WsmByteSpan {
                    ptr: goal.as_ptr(),
                    len: goal.len(),
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
    assert_eq!(
        String::from_utf8_lossy(&output[..written]).trim(),
        "[bob,dave,carol]"
    );
    assert_eq!(adapter.last_legacy_abi_id(), Some(LegacyAbiSemanticId(PROBE_ID)));

    assert_eq!(
        unsafe { vtable.stop.expect("stop")(vtable.context) },
        WsmStatus::Ok
    );
}


fn exchange_with_sid(
    adapter: &PrologAbiAdapter,
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

fn exchange_goal(adapter: &PrologAbiAdapter, goal: &[u8]) -> (WsmStatus, Vec<u8>) {
    let vtable = adapter.vtable();
    let mut output = vec![0u8; 128];
    let mut written = 0usize;
    let status = unsafe {
        vtable.exchange.expect("exchange")(
            vtable.context,
            WsmKernelRequest {
                semantic_id: PROBE_ID,
                payload: WsmByteSpan {
                    ptr: goal.as_ptr(),
                    len: goal.len(),
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

fn started_adapter() -> PrologAbiAdapter {
    let adapter = PrologAbiAdapter::new(PrologKernel::default(), fixture(), "X");
    let vtable = adapter.vtable();
    assert_eq!(
        unsafe { vtable.start.expect("start")(vtable.context) },
        WsmStatus::Ok
    );
    adapter
}

#[test]
fn semantic_add_uses_sid8_and_arguments_only() {
    if !swipl_available() {
        eprintln!("SKIP: swipl is not installed on this machine");
        return;
    }

    let adapter = started_adapter();
    let (status, output) = exchange_with_sid(&adapter, 0b0000_1100, b"2 3");
    assert_eq!(status, WsmStatus::Ok);
    assert_eq!(String::from_utf8_lossy(&output).trim(), "[5]");

    let (status, output) =
        exchange_with_sid(&adapter, 0b0000_1100, b"X is 7 - 3");
    assert_eq!(
        status,
        WsmStatus::InvalidArgument,
        "goal/operator text must not override the + SID"
    );
    assert!(output.is_empty());
}

#[test]
fn prolog_native_substitutions_preserve_zero_one_many_without_truth_projection() {
    if !swipl_available() {
        eprintln!("SKIP: swipl is not installed on this machine");
        return;
    }

    let zero = started_adapter();
    let (status, output) = exchange_goal(&zero, b"ancestor(carol, X)");
    assert_eq!(status, WsmStatus::Ok);
    assert_eq!(String::from_utf8_lossy(&output).trim(), "[]");

    let one = started_adapter();
    let (status, output) = exchange_goal(&one, b"parent(bob, X)");
    assert_eq!(status, WsmStatus::Ok);
    assert_eq!(String::from_utf8_lossy(&output).trim(), "[carol]");

    let many = started_adapter();
    let (status, output) = exchange_goal(&many, b"ancestor(alice, X)");
    assert_eq!(status, WsmStatus::Ok);
    assert_eq!(String::from_utf8_lossy(&output).trim(), "[bob,dave,carol]");

    // These are native Prolog answer lists. This witness deliberately does
    // not reinterpret [] as false or [..] as truth.
    assert_eq!(zero.last_legacy_abi_id(), Some(LegacyAbiSemanticId(PROBE_ID)));
    assert_eq!(one.last_legacy_abi_id(), Some(LegacyAbiSemanticId(PROBE_ID)));
    assert_eq!(many.last_legacy_abi_id(), Some(LegacyAbiSemanticId(PROBE_ID)));
}
