use sens::{Bija3, Bit3, CoreDomainIdentity};
use wsm_common_lisp_kernel::{CommonLispKernel, CommonLispRequest};

fn d3(bits: u8) -> CoreDomainIdentity {
    CoreDomainIdentity::D3(Bija3::from_word(Bit3::new(bits).unwrap()))
}

fn stdout_text(bytes: &[u8]) -> String {
    String::from_utf8_lossy(bytes).trim().to_string()
}

fn integration_enabled() -> bool {
    std::env::var_os("WSM_COMMON_LISP_INTEGRATION").is_some()
}

#[test]
fn common_lisp_car_witness_preserves_exact_d3_identity() {
    if !integration_enabled() { return; }
    let kernel = CommonLispKernel::default();
    let identity = d3(0b101);
    let request = CommonLispRequest::new(identity, "(car '(left right))");
    let result = kernel.evaluate(&request).expect("SBCL must execute CAR witness");

    assert_eq!(result.identity, identity);
    assert_eq!(stdout_text(&result.stdout), "LEFT");
}

#[test]
fn common_lisp_cdr_witness_preserves_exact_d3_identity() {
    if !integration_enabled() { return; }
    let kernel = CommonLispKernel::default();
    let identity = d3(0b110);
    let request = CommonLispRequest::new(identity, "(cdr '(left right))");
    let result = kernel.evaluate(&request).expect("SBCL must execute CDR witness");

    assert_eq!(result.identity, identity);
    assert_eq!(stdout_text(&result.stdout), "(RIGHT)");
}

#[test]
fn common_lisp_cons_then_car_reproduces_the_car_cons_law_slice() {
    if !integration_enabled() { return; }
    let kernel = CommonLispKernel::default();

    let car = d3(0b101);
    let request = CommonLispRequest::new(car, "(car (cons 'left 'right))");
    let result = kernel.evaluate(&request).expect("SBCL must execute witness");

    assert_eq!(result.identity, car);
    assert_eq!(stdout_text(&result.stdout), "LEFT");

    // Related identities remain exact D3 coordinates, not legacy bytes.
    assert_ne!(d3(0b100), car);
}
