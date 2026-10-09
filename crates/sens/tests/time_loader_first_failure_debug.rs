//! Temporary diagnostics for pinpointing the first failing top-level form in the time library.
//! Remove once the active COND/bootstrap blocker is repaired.

use sens::{eval_parsed_expressions, load_core_library, parse, Session, TIME_LIBRARY_SOURCE};

#[test]
fn report_first_time_library_form_rejected_by_current_core() {
    let mut session = Session::default();
    load_core_library(&mut session).expect("Core4 must load before time diagnostics");
    let forms = parse(TIME_LIBRARY_SOURCE).expect("time source must parse");
    for (index, form) in forms.iter().enumerate() {
        if let Err(error) = eval_parsed_expressions(std::slice::from_ref(form), &mut session) {
            panic!(
                "time library form #{index}, span={:?}, form={:?}, error={error:?}",
                form.span, form.kind
            );
        }
    }
}
