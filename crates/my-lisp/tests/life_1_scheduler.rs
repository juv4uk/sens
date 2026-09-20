use std::fs;
use std::path::PathBuf;

use my_lisp::{eval_program, load_core_library, Session};

fn repo_file(relative: &str) -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../..").join(relative)
}

fn eval_text(source: &str, session: &mut Session) -> String {
    eval_program(source, session)
        .expect("scheduler probe must execute")
        .value
        .to_string()
}

#[test]
fn life_1_scheduler_witness_is_lisp_owned() {
    let scheduler =
        fs::read_to_string(repo_file("lib/life-1-scheduler.lisp"))
            .expect("#801 scheduler source must be readable");
    let witness =
        fs::read_to_string(repo_file("tests/fixtures/life-1-scheduler-witness.lisp"))
            .expect("#801 scheduler witness must be readable");

    let mut session = Session::default();
    load_core_library(&mut session).expect("core library");
    eval_program(&scheduler, &mut session).expect("#801 scheduler source must execute");

    // Duplicate pending-invocation dedup is tracked separately in #942.
    let invocation =
        "(pending-invocation (producer datalog)           (trigger (projection-ready prolog-substitutions-to-datalog-facts))           (provenance-ref observation-42)           (priority ordinary)           (semantic-id \"00001100\"))";

    assert_eq!(
        eval_text(
            &format!(
                "(life-scheduler-field (quote {invocation}) (quote trigger))"
            ),
            &mut session,
        ),
        "(projection-ready prolog-substitutions-to-datalog-facts)"
    );
    assert_eq!(
        eval_text(
            &format!(
                "(life-scheduler-field (quote {invocation}) (quote provenance-ref))"
            ),
            &mut session,
        ),
        "observation-42"
    );

    assert_eq!(
        eval_text(
            &format!(
                "(life-scheduler-projection-ready?                    (quote {invocation})                    (quote ((projection-ready                      prolog-substitutions-to-datalog-facts observation-42))))"
            ),
            &mut session,
        ),
        "present"
    );
    assert_eq!(
        eval_text(
            &format!(
                "(life-scheduler-projection-ready?                    (quote {invocation})                    (quote ((projection-ready                      prolog-substitutions-to-datalog-facts observation-99))))"
            ),
            &mut session,
        ),
        "absent"
    );
    assert_eq!(
        eval_text(
            &format!(
                "(life-scheduler-projection-ready?                    (quote {invocation})                    (quote ((projection-ready                      different-bridge-contract observation-42))))"
            ),
            &mut session,
        ),
        "absent"
    );

    let selection = eval_text(
        &format!(
            "(life-scheduler-select-ready                (list (quote {invocation}))                (quote ((projection-ready                  prolog-substitutions-to-datalog-facts observation-42))))"
        ),
        &mut session,
    );
    assert!(
        selection.starts_with("(scheduler-selection ready "),
        "unexpected scheduler selection: {selection}"
    );

    assert_eq!(
        eval_text(
            "(life-scheduler-quiescence                (quote ()) (quote ()) (quote no-transition-required))",
            &mut session,
        ),
        "(quiescence-state quiescent)"
    );

    let result =
        eval_program(&witness, &mut session).expect("#801 scheduler witness must execute");
    assert_eq!(
        result.value.to_string(),
        "(life-1-scheduler-witness (status pass) (detail deduplicated-activation-and-quiescence))"
    );
}


#[test]
fn malformed_trigger_is_absent_not_cdr_failure() {
    let scheduler =
        fs::read_to_string(repo_file("lib/life-1-scheduler.lisp"))
            .expect("scheduler source");
    let mut session = Session::default();
    load_core_library(&mut session).expect("core library");
    eval_program(&scheduler, &mut session).expect("scheduler source must execute");

    let malformed =
        "(pending-invocation (producer datalog) (trigger ()) \
          (provenance-ref observation-42) (priority ordinary) \
          (semantic-id \"10101000\"))";

    assert_eq!(
        eval_text(
            &format!(
                "(life-scheduler-projection-ready? \
                   (quote {malformed}) \
                   (quote ((projection-ready prolog-substitutions-to-datalog-facts observation-42))))"
            ),
            &mut session,
        ),
        "absent"
    );

    let valid =
        "(pending-invocation (producer datalog) \
          (trigger (projection-ready prolog-substitutions-to-datalog-facts)) \
          (provenance-ref observation-42) (priority ordinary) \
          (semantic-id \"10101000\"))";

    let selection = eval_text(
        &format!(
            "(life-scheduler-select-ready \
               (list (quote {malformed}) (quote {valid})) \
               (quote ((projection-ready prolog-substitutions-to-datalog-facts observation-42))))"
        ),
        &mut session,
    );
    assert!(
        selection.starts_with("(scheduler-selection ready "),
        "malformed pending entry must be skipped: {selection}"
    );
}
