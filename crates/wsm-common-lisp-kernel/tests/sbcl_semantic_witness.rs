use sens::{Bija3, Bit3, CoreDomainIdentity};
use wsm_common_lisp_kernel::{CommonLispKernel, CommonLispRequest};

fn d3_car() -> CoreDomainIdentity {
    CoreDomainIdentity::from(Bija3::from_word(Bit3::new(0b101).unwrap()))
}

fn d3_cdr() -> CoreDomainIdentity {
    CoreDomainIdentity::from(Bija3::from_word(Bit3::new(0b110).unwrap()))
}

fn stdout_text(bytes: &[u8]) -> String {
    String::from_utf8_lossy(bytes).trim().to_string()
}

fn integration_enabled() -> bool {
    std::env::var_os("WSM_COMMON_LISP_INTEGRATION").is_some()
}

#[test]
fn common_lisp_car_witness_preserves_domain_qualified_sens_identity() {
    if !integration_enabled() { return; }
    let kernel = CommonLispKernel::default();
    let request = CommonLispRequest::new(d3_car(), "(car '(left right))");
    let result = kernel.evaluate(&request).expect("SBCL must execute CAR witness");

    assert_eq!(result.semantic_identity, d3_car());
    assert_eq!(stdout_text(&result.stdout), "LEFT");
}

#[test]
fn common_lisp_cdr_witness_preserves_domain_qualified_sens_identity() {
    if !integration_enabled() { return; }
    let kernel = CommonLispKernel::default();
    let request = CommonLispRequest::new(d3_cdr(), "(cdr '(left right))");
    let result = kernel.evaluate(&request).expect("SBCL must execute CDR witness");

    assert_eq!(result.semantic_identity, d3_cdr());
    assert_eq!(stdout_text(&result.stdout), "(RIGHT)");
}

#[test]
fn common_lisp_cons_then_car_preserves_external_car_identity() {
    if !integration_enabled() { return; }
    let kernel = CommonLispKernel::default();

    // The mechanism form exercises CL:CONS and CL:CAR while the externally
    // observed canonical semantic identity remains D3 CAR.
    let request = CommonLispRequest::new(d3_car(), "(car (cons 'left 'right))");
    let result = kernel.evaluate(&request).expect("SBCL must execute witness");

    assert_eq!(result.semantic_identity, d3_car());
    assert_eq!(stdout_text(&result.stdout), "LEFT");
}
