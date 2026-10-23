//! Rust перевіряє лише **механізм**: що бібліотеки ядра й часу завантажуються
//! і що самоперевірні Lisp-свідки виконуються або відкидаються.
//!
//! Закон часу та власний fail-closed вердикт належать SENS Lisp
//! (`tests/semantic/time-*-law.lisp`, `time-*-mutant.lisp`). Цей адаптер НЕ
//! порівнює мовних значень зі своєю таблицею істинності — інакше він став би
//! другим оракулом семантики, що заборонено `tests/semantic/README.md`.

use sens::{eval_program, load_core_library, load_time_library, Session};

fn time_session() -> Session {
    let mut session = Session::default();
    load_core_library(&mut session).expect("SENS core must load");
    load_time_library(&mut session).expect("SENS time library must load");
    session
}

/// Позитивні мовні закони: кожен має виконатися самим SENS і повернути свій
/// названий статус. Значень тут не порівнюємо.
const TIME_LAWS: &[(&str, &str)] = &[
    ("utc-calendar", include_str!("../../../tests/semantic/time-utc-calendar-law.lisp")),
    ("ntp-fields", include_str!("../../../tests/semantic/time-ntp-fields-law.lisp")),
    ("internet-timestamp", include_str!("../../../tests/semantic/time-internet-timestamp-law.lisp")),
    ("mono-ms", include_str!("../../../tests/semantic/time-mono-ms-law.lisp")),
    ("timezone-policy", include_str!("../../../tests/semantic/time-timezone-policy-law.lisp")),
];

/// Негативні мутанти: рівно одна змінена вимога. SENS має відкинути кожен сам.
const TIME_MUTANTS: &[(&str, &str)] = &[
    ("utc-calendar", include_str!("../../../tests/semantic/time-utc-calendar-mutant.lisp")),
    ("mono-ms", include_str!("../../../tests/semantic/time-mono-ms-mutant.lisp")),
    ("timezone-name", include_str!("../../../tests/semantic/time-timezone-name-mutant.lisp")),
];

#[test]
fn rust_runtime_executes_every_lisp_owned_time_law() {
    for (name, source) in TIME_LAWS {
        let mut session = time_session();
        let _ = eval_program(source, &mut session)
            .unwrap_or_else(|error| panic!("закон {name} має виконати сам SENS: {error}"));
    }
}

#[test]
fn every_lisp_owned_time_mutant_is_rejected_by_sens_itself() {
    for (name, source) in TIME_MUTANTS {
        let mut session = time_session();
        assert!(
            eval_program(source, &mut session).is_err(),
            "мутант {name} має бути відкинутий самим SENS, а не «пройти»"
        );
    }
}
