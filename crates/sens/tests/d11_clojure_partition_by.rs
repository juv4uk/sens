//! Механіка Rust: завантаження UTF-8, створення сесії та виклик SENS.
//! 39 законів групування, включно з 11 контрприкладами, належать двом Lisp-свідкам.
//! Фізичний D1-вердикт свідків перевіряє Zig/T5M → SENS, не Rust.

use sens::{eval_program, load_core_library, Session};
use std::path::PathBuf;

fn прочитати_джерело(відносний_шлях: &str) -> String {
    let корінь = PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../..");
    let шлях = корінь.join(відносний_шлях);
    std::fs::read_to_string(&шлях)
        .unwrap_or_else(|помилка| panic!("Rust I/O path={} error={помилка}", шлях.display()))
}

#[test]
fn rust_mechanism_loads_and_runs_clojure_lisp_witnesses() {
    for свідок in [
        "tests/semantic/d11-clojure-partition-by-laws.lisp",
        "tests/semantic/d11-clojure-dedupe-laws.lisp",
    ] {
        let mut сеанс = Session::bare();
        load_core_library(&mut сеанс).expect("Rust має створити робочу сесію SENS");
        for бібліотека in [
            "lib/d11-srfi1-span-break.lisp",
            "lib/d11-clojure-partition-by.lisp",
        ] {
            let джерело = прочитати_джерело(бібліотека);
            eval_program(&джерело, &mut сеанс)
                .unwrap_or_else(|помилка| panic!("SENS load path={бібліотека} error={помилка}"));
        }
        let джерело = прочитати_джерело(свідок);
        eval_program(&джерело, &mut сеанс)
            .unwrap_or_else(|помилка| panic!("SENS eval path={свідок} error={помилка}"));
        // Жодного очікуваного true/false у Rust: норма написана мовою Lisp.
        // Парний і самостійний D1-вердикт засвідчує prove-lisp-semantic-t5m.sh.
    }
}
