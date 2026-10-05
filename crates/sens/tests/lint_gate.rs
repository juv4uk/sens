use sens::{eval_program, Session};
use std::fs;

/// `read-file` is language-owned (lib/fs.lisp) over the host's
/// `read-file-bytes`; installed here via the dev-dependency plus fs.lisp.
fn install_read_capability() {
    sens_host::install();
}

#[test]
fn linter_gate() {
    install_read_capability();
    let mut session = Session::default();

    // Evaluate the libraries directly to load them into the environment
    let core_src = fs::read_to_string("../../lib/core.lisp").unwrap();
    eval_program(&core_src, &mut session).unwrap();
    let utf8_src = fs::read_to_string("../../lib/utf8.lisp").unwrap();
    eval_program(&utf8_src, &mut session).unwrap();
    let fs_src = fs::read_to_string("../../lib/fs.lisp").unwrap();
    eval_program(&fs_src, &mut session).unwrap();
    let linter_src = fs::read_to_string("../../lib/linter.lisp").unwrap();
    eval_program(&linter_src, &mut session).unwrap();

    // Check if linter.my works by defining the threshold script
    let runner_src = r#"
        (def thresholds (quote ((max-size . 2000) (max-nesting . 30) (max-complexity . 24) (max-globals . 55) (max-effects . 20))))

        (def check-file-loop
          (lambda (path remaining all-violations)
            (cond
              ((атом? remaining) all-violations)
              ((атом? (quote fallback))
               (let ((violations (lint-check (car remaining) thresholds)))
                 (cond
                   ((атом? violations) (check-file-loop path (cdr remaining) all-violations))
                   ((атом? (quote fallback))
                    (check-file-loop path (cdr remaining) (cons (list path (car remaining) violations) all-violations)))))))))

        (def check-file
          (lambda (path)
            (check-file-loop path (read-all (read-file path)) (quote ()))))

        (def append-all
          (lambda (lists)
            (cond
              ((атом? lists) (quote ()))
              ((атом? (quote fallback))
               (append (car lists) (append-all (cdr lists)))))))

        (append-all
          (list
            (check-file "../../lib/core.lisp")
            (check-file "../../lib/linter.lisp")
            (check-file "../../lib/world.lisp")
            (check-file "../../lib/content-store.lisp")
            (check-file "../../lib/reason.lisp")))
    "#;

    match eval_program(runner_src, &mut session) {
        Ok(res) => {
            if !matches!(res.value, sens::Value::Nil) {
                panic!("Lint violations found:\n{}", res.value);
            }
        }
        Err(e) => {
            panic!("Error evaluating runner_src:\n{:?}", e);
        }
    }
}
