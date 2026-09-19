use wsm_common_lisp_kernel::{CommonLispKernel, CommonLispRequest, SemanticId};

// semantic-registry-experiment.lisp:
//   00000100 cons
//   00000101 car
//   00000110 cdr
const CONS_ID: u8 = 0b0000_0100;
const CAR_ID: u8 = 0b0000_0101;
const CDR_ID: u8 = 0b0000_0110;

fn stdout_text(bytes: &[u8]) -> String {
    String::from_utf8_lossy(bytes).trim().to_string()
}

fn integration_enabled() -> bool {
    std::env::var_os("WSM_COMMON_LISP_INTEGRATION").is_some()
}

#[test]
fn common_lisp_car_witness_preserves_my_lisp_semantic_id() {
    if !integration_enabled() { return; }
    let kernel = CommonLispKernel::default();
    let request = CommonLispRequest::new(CAR_ID, "(car '(left right))");
    let result = kernel.evaluate(&request).expect("SBCL must execute CAR witness");

    assert_eq!(result.semantic_id, SemanticId(CAR_ID));
    assert_eq!(stdout_text(&result.stdout), "LEFT");
}

#[test]
fn common_lisp_cdr_witness_preserves_my_lisp_semantic_id() {
    if !integration_enabled() { return; }
    let kernel = CommonLispKernel::default();
    let request = CommonLispRequest::new(CDR_ID, "(cdr '(left right))");
    let result = kernel.evaluate(&request).expect("SBCL must execute CDR witness");

    assert_eq!(result.semantic_id, SemanticId(CDR_ID));
    assert_eq!(stdout_text(&result.stdout), "(RIGHT)");
}

#[test]
fn common_lisp_cons_then_car_reproduces_the_car_cons_law_slice() {
    if !integration_enabled() { return; }
    let kernel = CommonLispKernel::default();

    // The form exercises CL:CONS and CL:CAR while the externally observed
    // semantic identity is CAR. my-lisp still owns the car(cons(x,y)) = x law.
    let request =
        CommonLispRequest::new(CAR_ID, "(car (cons 'left 'right))");
    let result = kernel.evaluate(&request).expect("SBCL must execute witness");

    assert_eq!(result.semantic_id, SemanticId(CAR_ID));
    assert_eq!(stdout_text(&result.stdout), "LEFT");

    // Keep the related registry identity visible in the executable witness
    // without teaching the adapter what CONS means.
    assert_eq!(SemanticId(CONS_ID), SemanticId(0b0000_0100));
}
