use wsm_common_lisp_kernel::{CommonLispAbiAdapter, SemanticId};
use wsm_kernel_c_abi::{
    WsmByteSpan, WsmKernelKind, WsmKernelRequest, WsmMutableByteSpan, WsmStatus,
};

const CAR_ID: u8 = 0b0000_0101;

fn integration_enabled() -> bool {
    std::env::var_os("WSM_COMMON_LISP_INTEGRATION").is_some()
}

#[test]
fn semantic_id_crosses_c_abi_and_returns_native_common_lisp_result() {
    if !integration_enabled() {
        return;
    }

    let adapter = CommonLispAbiAdapter::default();
    let vtable = adapter.vtable();
    assert_eq!(vtable.kernel, WsmKernelKind::CommonLisp);

    let start = vtable.start.expect("Common Lisp start callback");
    let exchange = vtable.exchange.expect("Common Lisp exchange callback");
    let stop = vtable.stop.expect("Common Lisp stop callback");

    assert_eq!(unsafe { start(vtable.context) }, WsmStatus::Ok);

    let input = b"(car (cons 'left 'right))";
    let mut output = [0u8; 64];
    let mut written = 0usize;

    let status = unsafe {
        exchange(
            vtable.context,
            WsmKernelRequest {
                semantic_id: CAR_ID,
                payload: WsmByteSpan {
                    ptr: input.as_ptr(),
                    len: input.len(),
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
    assert_eq!(String::from_utf8_lossy(&output[..written]).trim(), "LEFT");
    assert_eq!(adapter.last_semantic_id(), Some(SemanticId(CAR_ID)));

    assert_eq!(unsafe { stop(vtable.context) }, WsmStatus::Ok);
}
