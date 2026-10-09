//! Disposable diagnostic for exact D1 control; NOT a ratified source fixture.
use sens::{eval_program, Session};

fn with_dependencies() -> Session {
    let mut session = Session::default();
    for source in [
        include_str!("../../../lib/core.lisp"),
        include_str!("../../../lib/unify.lisp"),
        include_str!("../../../lib/reason.lisp"),
        include_str!("../../../lib/forward.lisp"),
        include_str!("../../../lib/knowledge.lisp"),
        include_str!("../../../lib/persistent-map.lisp"),
        include_str!("../../../lib/world.lisp"),
        include_str!("../../../lib/content-store.lisp"),
        include_str!("../../../lib/lisp-fs.lisp"),
    ] {
        eval_program(source, &mut session).expect("dependency");
    }
    session
}

#[test]
fn inspect_each_lexical_d1_relation_without_changing_runtime() {
    let fixture = include_str!("../../../tests/fixtures/content-store-authority-witness.lisp");
    let marker = "      (00000111\n        (root-relation";
    assert_eq!(fixture.matches(marker).count(), 1, "fixture changed");
    let head = fixture.split(marker).next().unwrap();
    let mut session = with_dependencies();
    for probe in [
        "root-a", "root-b", "object-a", "object-b",
        "root-relation", "object-relation", "projection-relation",
        "(content-store-no? root-relation)",
        "(content-store-no? object-relation)",
        "(content-store-no? projection-relation)",
        "(00000111 (root-relation (00000001 pass)) ((content-store-no? root-relation) (00000001 fail)))",
    ] {
        let redefined = format!("{head}{probe}\n))");
        let loaded = eval_program(&redefined, &mut session);
        match loaded {
            Ok(_) => match eval_program("(content-store-authority-witness)", &mut session) {
                Ok(v) => eprintln!("SCOPE-PROBE {probe} => {}", v.value),
                Err(e) => eprintln!("SCOPE-PROBE {probe} => EVAL ERROR {e}"),
            },
            Err(e) => eprintln!("SCOPE-PROBE {probe} => LOAD ERROR {e}"),
        };
    }
    let original = eval_program(fixture, &mut session).expect("actual fixture must load");
    eprintln!("SCOPE-PROBE fixture load {}", original.value);
    let verdict = eval_program("(content-store-authority-witness)", &mut session)
       .expect("actual fixture must evaluate");
    eprintln!("SCOPE-PROBE final verdict => {}", verdict.value);
}
