use std::path::PathBuf;

use wsm_kernel_c_abi::{
    WsmByteSpan, WsmKernelKind, WsmKernelRequest, WsmMutableByteSpan, WsmStatus,
};
use wsm_prolog_kernel::{PrologAbiAdapter, PrologKernel, SemanticId};

const PROBE_ID: u8 = 0b0000_0011;

fn swipl_available() -> bool {
    PrologKernel::default().version().is_ok()
}

fn fixture() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("tests/fixtures/family.pl")
}

#[test]
fn opaque_semantic_id_crosses_same_c_abi_into_real_prolog_backtracking() {
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
    assert_eq!(adapter.last_semantic_id(), Some(SemanticId(PROBE_ID)));

    assert_eq!(
        unsafe { vtable.stop.expect("stop")(vtable.context) },
        WsmStatus::Ok
    );
}
