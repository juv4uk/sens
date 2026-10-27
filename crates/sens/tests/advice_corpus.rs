//! B3: a small adversarial Advice Taker corpus through one semantic path:
//! кандидатні знання -> порадити/порадити-всі -> міркувати-у-спостерігати -> пояснити-підсумок.
//! The cases are chosen for distinct failure/derivation modes, not fixture count.

use sens::{
    eval_parsed_expressions, eval_pinned_reasoning_source, load_core_library, parse,
    parse_exact_domain_source, parse_mixed_exact_domain, Session,
};

fn eval_advice_corpus(source: &str) -> String {
    let mut session = Session::default();
    // Інтерактивний сценарій використовує поточний Core4 та українську
    // людську проєкцію; D3-цитування нижче записане як «як-є», не як цифри.
    load_core_library(&mut session).expect("поточне ядро SENS Core4");
    for (library_path, library) in [
        ("lib/unify.lisp", include_str!("../../../lib/unify.lisp")),
        ("lib/reason.lisp", include_str!("../../../lib/reason.lisp")),
        (
            "lib/forward.lisp",
            include_str!("../../../lib/forward.lisp"),
        ),
        (
            "lib/knowledge.lisp",
            include_str!("../../../lib/knowledge.lisp"),
        ),
        // Admission and package-import policies now belong to immutable World.
        // The host only loads the exact-domain SENS source; it defines no law.
        ("lib/world.lisp", include_str!("../../../lib/world.lisp")),
        (
            "lib/understand.lisp",
            include_str!("../../../lib/understand.lisp"),
        ),
        (
            "lib/result-status.lisp",
            include_str!("../../../lib/result-status.lisp"),
        ),
        (
            "lib/narrate.lisp",
            include_str!("../../../lib/narrate.lisp"),
        ),
    ] {
        let result = match library_path {
            "lib/unify.lisp" | "lib/reason.lisp" | "lib/forward.lisp" | "lib/knowledge.lisp"
            | "lib/world.lisp" => eval_pinned_reasoning_source(library_path, library, &mut session),
            "lib/understand.lisp" => {
                let parsed = parse_mixed_exact_domain(library)
                    .unwrap_or_else(|error| panic!("{library_path}: source reader: {error}"));
                eval_parsed_expressions(&parsed, &mut session)
            }
            "lib/result-status.lisp" | "lib/narrate.lisp" => {
                let parsed = parse_exact_domain_source(library)
                    .unwrap_or_else(|error| panic!("{library_path}: exact reader: {error}"));
                eval_parsed_expressions(&parsed, &mut session)
            }
            _ => unreachable!("only the pinned corpus libraries are admitted"),
        };
        result.unwrap_or_else(|error| {
            panic!("SENS corpus dependency {library_path} failed: {error}")
        });
    }
    let program = parse(source)
        .unwrap_or_else(|e| panic!("Advice Taker Ukrainian source reader: {e}\nsource: {source}"));
    eval_parsed_expressions(&program, &mut session)
        .unwrap_or_else(|e| panic!("Advice Taker exact-domain eval: {e}\nsource: {source}"))
        .value
        .to_string()
}

#[test]
fn direct_controlled_fact_reaches_proved_narration() {
    let source = r#"
        (визначити перехід
          (порадити-світ
            (порожній-світ)
            (як-є astronomy)
            (розібрати (як-є (earth is a planet)))))
        (визначити світ-із-порадою (друге перехід))
        (пояснити-підсумок
          (міркувати-спостерігати
            (як-є (planet earth))
            (світ-клаузи світ-із-порадою (як-є astronomy))))
    "#;
    assert_eq!(eval_advice_corpus(source), "(proved earth is a planet)");
}

#[test]
fn multistep_rules_survive_admission_reasoning_and_presentation() {
    let source = r#"
        (порадити-всі science
          (як-є (
            ((planet earth))
            ((has (мфк x) mass) (planet (мфк x)))
            ((valuable (мфк x)) (has (мфк x) mass))
          )))
        (нехай-послідовно ((outcome
                 (міркувати-у-спостерігати (як-є science) (як-є (valuable earth))))
               (words (пояснити-підсумок outcome)))
          (список (результат-стан outcome) (перше words)))
    "#;
    assert_eq!(eval_advice_corpus(source), "(proved proved)");
}

#[test]
fn recursive_rule_survives_the_same_end_to_end_path() {
    let source = r#"
        (порадити-всі family
          (як-є (
            ((parent alice bob))
            ((parent bob charlie))
            ((ancestor (мфк x) (мфк y)) (parent (мфк x) (мфк y)))
            ((ancestor (мфк x) (мфк y))
              (parent (мфк x) (мфк z))
              (ancestor (мфк z) (мфк y)))
          )))
        (нехай-послідовно ((outcome
                 (міркувати-у-спостерігати
                   (як-є family)
                   (як-є (ancestor alice charlie))))
               (words (пояснити-підсумок outcome)))
          (список (результат-стан outcome) (перше words)))
    "#;
    assert_eq!(eval_advice_corpus(source), "(proved proved)");
}

#[test]
fn explicit_conflict_is_rejected_and_cannot_replace_the_existing_fact() {
    let source = r#"
        (порадити ethics (як-є ((mortal socrates))))
        (нехай-послідовно ((decision
                 (порадити ethics (як-є ((not? (mortal socrates))))))
               (outcome
                 (міркувати-у-спостерігати (як-є ethics) (як-є (mortal socrates)))))
          (список (перше decision) (результат-стан outcome)))
    "#;
    assert_eq!(eval_advice_corpus(source), "(conflict proved)");
}

#[test]
fn knowledge_package_round_trip_precedes_reasoning_without_eval_of_package_data() {
    let source = r#"
        (визначити package
          (створити-пакет-структурованих-знань
            (як-є archive)
            (як-є (((planet mars))))))
        (визначити журнал-знань (як-є ()))
        (імпортувати-пакет-знань package)
        (пояснити-підсумок
          (міркувати-у-спостерігати (як-є archive) (як-є (planet mars))))
    "#;
    assert_eq!(eval_advice_corpus(source), "(proved mars is a planet)");
}
