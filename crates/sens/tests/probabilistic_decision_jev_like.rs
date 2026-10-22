//! Regression witnesses for the Lisp-owned Jev/System-One-like probabilistic decision slice.
//!
//! These tests exercise the SENS-owned contract and a fixture-backed local model adapter.
//! No external provider is called; no new SID or Rust Value variant is introduced.

use sens::{
    eval_program, exact_domain_fraction_parts, load_core_library, BinaryNumber, Session, Value,
};
use std::{
    io::{Read, Write},
    net::TcpListener,
    thread,
    time::Duration,
};

fn d48_probability_word(value: u64) -> BinaryNumber {
    const WIDTH: usize = 48;
    assert!(
        value < (1_u64 << (WIDTH - 1)),
        "value must fit positive D48"
    );
    let bits: Vec<u8> = (0..WIDTH)
        .rev()
        .map(|shift| ((value >> shift) & 1) as u8)
        .collect();
    BinaryNumber::from_numeric_domain_bits(WIDTH, &bits).expect("explicit D48 word")
}

fn d48_probability(numerator: u64, denominator: u64) -> Value {
    assert!(denominator > 0, "probability denominator must be nonzero");
    let numerator = d48_probability_word(numerator);
    let denominator = d48_probability_word(denominator);
    exact_domain_fraction_parts(false, &numerator, &denominator)
        .expect("exact, same-domain D48 probability")
}

fn eval_probabilistic_decision(source: &str) -> String {
    let mut session = Session::default();
    load_core_library(&mut session).expect("core library should load");
    eval_program(
        include_str!("../../../lib/result-status.lisp"),
        &mut session,
    )
    .expect("result-status should load");
    eval_program(
        include_str!("../../../experiments/probabilistic-decision-jev-like.lisp"),
        &mut session,
    )
    .expect("probabilistic decision layer should load");
    eval_program(
        include_str!("../../../research/probabilistic-decision-auto-choice-20261021.lisp"),
        &mut session,
    )
    .expect("automatic choice policy should load");
    eval_program(
        include_str!("../../../research/probabilistic-decision-system-one-20261022.lisp"),
        &mut session,
    )
    .expect("typed System One contract should load");
    // Probability data must retain its domain width. Bare Rational literals are
    // deliberately rejected by SENS mathematical operations.
    for (name, numerator, denominator) in [
        ("доля-3-4", 3, 4),
        ("доля-1-4", 1, 4),
        ("доля-1-3", 1, 3),
        ("доля-2-3", 2, 3),
        ("доля-4-5", 4, 5),
        ("доля-1-2", 1, 2),
        ("доля-3-2", 3, 2),
    ] {
        session
            .environment
            .define(name, d48_probability(numerator, denominator));
    }
    eval_program(source, &mut session)
        .unwrap_or_else(|e| panic!("evaluation failed: {e}\nsource: {source}"))
        .value
        .to_string()
}

#[test]
fn choice_observation_keeps_probability_confidence_and_provenance() {
    let source = r#"
        (нехай-послідовно ((question
                (запит-вибору
                  (як-є route)
                  (як-є (billing technical))))
              (observation
                (спостерегти-вибір
                  question
                  (список (список (як-є billing) доля-3-4) (список (як-є technical) доля-1-4))
                  (як-є ((source synthetic) (revision 1))))))
          (список
            (упевненість-спостереження observation)
            (походження-спостереження observation)
            (друге (правило-вибору observation (як-є billing) доля-2-3))))
    "#;

    assert_eq!(
        eval_probabilistic_decision(source),
        r#"(3/4 ((source synthetic) (revision 1)) accept)"#
    );
}

#[test]
fn invalid_choice_distribution_fails_closed_when_not_normalized() {
    let source = r#"
        (нехай-послідовно ((question
                (запит-вибору
                  (як-є route)
                  (як-є (billing technical)))))
          (результат-стан
            (спостерегти-вибір
              question
              (список (список (як-є billing) доля-2-3) (список (як-є technical) доля-1-4))
              (як-є ((source malformed))))))
    "#;

    assert_eq!(eval_probabilistic_decision(source), "invalid");
}

#[test]
fn noul_policy_is_explicit_threshold_control_not_truthiness() {
    let source = r#"
        (нехай-послідовно ((question (запит-так-ні (як-є urgent)))
              (observation
                (спостерегти-так-ні
                  question
                  (список
                    (список (як-є yes) доля-3-4)
                    (список (як-є no) доля-1-4))
                  (як-є ((source synthetic))))))
          (список
            (друге (правило-так-ні observation доля-2-3))
            (друге (правило-так-ні observation доля-4-5))
            (упевненість-спостереження observation)))
    "#;

    assert_eq!(eval_probabilistic_decision(source), "(accept defer 3/4)");
}

#[test]
fn score_observation_uses_the_same_typed_distribution_contract() {
    let source = r#"
        (нехай-послідовно ((question
                (запит-шкали
                  (як-є severity)
                  (як-є (low medium high))))
              (observation
                (спостерегти-шкалу
                  question
                  (список (список (як-є low) доля-1-4) (список (як-є medium) доля-1-2) (список (як-є high) доля-1-4))
                  (як-є ((source synthetic))))))
          (список
            (перше observation)
            (упевненість-спостереження observation)
            (походження-спостереження observation)))
    "#;

    assert_eq!(
        eval_probabilistic_decision(source),
        "(score-observation/1 1/2 ((source synthetic)))"
    );
}

#[test]
fn independent_questions_do_not_invent_joint_consistency() {
    let source = r#"
        (нехай ((left
                (спостерегти-вибір
                  (запит-вибору
                    (як-є route)
                    (як-є (billing technical)))
                  (список (список (як-є billing) доля-3-4) (список (як-є technical) доля-1-4))
                  (як-є ((source a)))))
              (right
                (спостерегти-вибір
                  (запит-вибору
                    (як-є route-2)
                    (як-є (billing technical)))
                  (список (список (як-є billing) доля-1-4) (список (як-є technical) доля-3-4))
                  (як-є ((source b))))))
          (перше (узгодженість-двох-запитів left right (як-є independent))))
    "#;

    assert_eq!(eval_probabilistic_decision(source), "decision-relation-1");
}

#[test]
fn declared_agreement_with_different_distributions_is_disputed() {
    let source = r#"
        (нехай ((left
                (спостерегти-вибір
                  (запит-вибору
                    (як-є route)
                    (як-є (billing technical)))
                  (список (список (як-є billing) доля-3-4) (список (як-є technical) доля-1-4))
                  (як-є ((source a)))))
              (right
                (спостерегти-вибір
                  (запит-вибору
                    (як-є route)
                    (як-є (billing technical)))
                  (список (список (як-є billing) доля-1-4) (список (як-є technical) доля-3-4))
                  (як-є ((source b))))))
          (результат-стан
            (узгодженість-двох-запитів left right (як-є agree))))
    "#;

    assert_eq!(eval_probabilistic_decision(source), "disputed");
}

#[test]
fn noul_policy_rejects_out_of_domain_threshold() {
    let source = r#"
        (нехай-послідовно ((question (запит-так-ні (як-є urgent)))
              (observation
                (спостерегти-так-ні
                  question
                  (список
                    (список (як-є yes) доля-3-4)
                    (список (як-є no) доля-1-4))
                  (як-є ((source synthetic))))))
          (результат-стан
            (правило-так-ні observation доля-3-2)))
    "#;

    assert_eq!(eval_probabilistic_decision(source), "invalid");
}

#[test]
fn choice_policy_rejects_out_of_domain_threshold() {
    let source = r#"
        (нехай-послідовно ((question
                (запит-вибору
                  (як-є route)
                  (як-є (billing technical))))
              (observation
                (спостерегти-вибір
                  question
                  (список (список (як-є billing) доля-3-4) (список (як-є technical) доля-1-4))
                  (як-є ((source synthetic))))))
          (результат-стан
            (правило-вибору observation (як-є billing) доля-3-2)))
    "#;

    assert_eq!(eval_probabilistic_decision(source), "invalid");
}

#[test]
fn synthetic_witness_carries_one_state_through_three_typed_questions() {
    let source = r#"
        (нехай ((witness
                (синтетичний-свідок-рішення
                  (як-є ((case billing) (revision 1)))
                  (запит-вибору
                    (як-є route)
                    (як-є (billing technical)))
                  (запит-так-ні (як-є urgent))
                  (запит-шкали
                    (як-є severity)
                    (як-є (low medium high))))))
          (список
            (перше witness)
            (друге witness)
            (перше (третє witness))
            (упевненість-спостереження (четверте witness))
            (упевненість-спостереження (п'ятий witness))))
    "#;

    assert_eq!(
        eval_probabilistic_decision(source),
        "(probabilistic-witness/1 ((case billing) (revision 1)) choice-observation/1 2/3 1/2)"
    );
}

#[test]
fn automatic_choice_policy_selects_unique_winner_and_defers_unsafe_choices() {
    let selected = r#"
        (нехай-послідовно ((question
                (запит-вибору
                  (як-є route)
                  (як-є (billing technical))))
              (observation
                (спостерегти-вибір
                  question
                  (список (список (як-є billing) доля-3-4) (список (як-є technical) доля-1-4))
                  (як-є ((source synthetic) (revision 1)))))
              (decision (правило-автоматичного-вибору observation доля-2-3)))
          (список
            (друге decision)
            (друге (четверте decision))
            (походження-спостереження (третє decision))))
    "#;
    assert_eq!(
        eval_probabilistic_decision(selected),
        "(accept billing ((source synthetic) (revision 1)))"
    );

    let tied = r#"
        (нехай-послідовно ((question
                (запит-вибору
                  (як-є route)
                  (як-є (billing technical))))
              (observation
                (спостерегти-вибір
                  question
                  (список (список (як-є billing) доля-1-2) (список (як-є technical) доля-1-2))
                  (як-є ((source synthetic) (case tied)))))
              (decision (правило-автоматичного-вибору observation доля-1-2)))
          (список
            (друге decision)
            (друге (четверте decision))
            (друге (п'ятий decision))
            (походження-спостереження (третє decision))))
    "#;
    assert_eq!(
        eval_probabilistic_decision(tied),
        "(defer ambiguous-maximum-probability (billing technical) ((source synthetic) (case tied)))"
    );

    let below_threshold = r#"
        (нехай-послідовно ((question
                (запит-вибору
                  (як-є route)
                  (як-є (billing technical))))
              (observation
                (спостерегти-вибір
                  question
                  (список (список (як-є billing) доля-3-4) (список (як-є technical) доля-1-4))
                  (як-є ((source synthetic)))))
              (decision (правило-автоматичного-вибору observation доля-4-5)))
          (список
            (друге decision)
            (друге (четверте decision))
            (друге (п'ятий decision))
            (упевненість-спостереження (третє decision))))
    "#;
    assert_eq!(
        eval_probabilistic_decision(below_threshold),
        "(defer below-confidence-threshold billing 3/4)"
    );

    let forged_confidence = r#"
        (нехай-послідовно ((question
                (запит-вибору
                  (як-є route)
                  (як-є (billing technical))))
              (observation
                (список
                  (як-є choice-observation/1)
                  question
                  (список (список (як-є billing) доля-3-4) (список (як-є technical) доля-1-4))
                  доля-1-4
                  (як-є ((source synthetic))))))
          (результат-стан (правило-автоматичного-вибору observation доля-2-3)))
    "#;
    assert_eq!(eval_probabilistic_decision(forged_confidence), "invalid");

    let invalid_threshold = r#"
        (нехай-послідовно ((question
                (запит-вибору
                  (як-є route)
                  (як-є (billing technical))))
              (observation
                (спостерегти-вибір
                  question
                  (список (список (як-є billing) доля-3-4) (список (як-є technical) доля-1-4))
                  (як-є ((source synthetic))))))
          (результат-стан (правило-автоматичного-вибору observation доля-3-2)))
    "#;
    assert_eq!(eval_probabilistic_decision(invalid_threshold), "invalid");
}

#[test]
fn system_one_validates_one_state_with_parallel_typed_questions_and_answers() {
    // Цей test_id запускається чинним CI після зміни System One джерела.
    // Без посередництва Python/JSON: SENS сам має відрізняти прямі Д1
    // «так» / «ні», а не успадковувати historical T/NIL truthiness.
    for (source, expected) in [
        (
            "(за-умовою (ні (як-є помилка)) (так (як-є гаразд)))",
            "гаразд",
        ),
        (
            "(за-умовою (так (як-є гаразд)) (ні (як-є помилка)))",
            "гаразд",
        ),
    ] {
        assert_eq!(
            eval_probabilistic_decision(source),
            expected,
            "test_id=system-one-d1-positive-negative layer=actual-SENS source={source}"
        );
    }

    // Точний негативний D24 свідок із самого SENS: старий дріб не
    // дістає арифметичного допуску, навіть коли інший операнд є D24.
    // Не послаблюємо арифметику для того, щоб "позеленів" System One.
    let mut numeric_session = Session::default();
    let bad = eval_program("(додати 1/2 1)", &mut numeric_session)
        .expect_err("SENS має відхилити unqualified Rational + D24");
    assert!(
        bad.message.contains("actual_kind=unqualified-rational"),
        "test_id=system-one-numeric-domain-red layer=actual-SENS expected=unqualified-rational actual={bad}"
    );

    let valid_batch = r#"
      (нехай-послідовно ((state (як-є ((message "double charge") (locale uk))))
             (choice-question (запитання-вибору-системи-один
               (як-є route)
               "Choose the support team for this request."
               (як-є ((billing "Payment or refund issues")
                       (technical "Software malfunction")))))
             (noul-question (запитання-так-ні-системи-один
               (як-є urgent)
               "Does this request need urgent handling?"))
             (score-question (запитання-шкали-системи-один
               (як-є severity)
               "Rate urgency from low to high."
               (як-є ((low "No deadline")
                       (medium "Needed soon")
                       (high "Immediate attention")))))
             (questions (список choice-question noul-question score-question))
             (request (запит-системи-один state questions))
             (answers
               (список
                 (спостерегти-вибір-системи-один choice-question
                   (список (список (як-є billing) доля-3-4)
                           (список (як-є technical) доля-1-4))
                   (як-є ((source synthetic) (question route))))
                 (спостерегти-так-ні noul-question
                   (список
                     (список (як-є yes) доля-2-3)
                     (список (як-є no) доля-1-3))
                   (як-є ((source synthetic) (question urgent))))
                 (спостерегти-шкалу-системи-один score-question
                   (список (список (як-є low) доля-1-4)
                           (список (як-є medium) доля-1-2)
                           (список (як-є high) доля-1-4))
                   (як-є ((source synthetic) (question severity))))))
             (response (відповідь-системи-один request answers)))
        (список
          (за-умовою
            ((перевірити-запит-системи-один? request) (як-є valid))
            (так (як-є invalid)))
          (довжина (третє request))
          (за-умовою
            ((відповідь-системи-один-допустима? response request) (як-є valid))
            (так (як-є invalid)))))
    "#;
    let actual_batch = eval_probabilistic_decision(valid_batch);
    if actual_batch != "(valid 3 valid)" {
        // Лише при RED запускаємо додаткову діагностику тим самим SENS.
        // Це не host-oracle: кожен D1 результат повертає виконаний Lisp.
        let diagnostic = valid_batch.replace(
            "          (довжина (третє request))",
            r#"(список
                (запитання-системи-один-допустиме? choice-question)
                (запитання-системи-один-допустиме? noul-question)
                (запитання-системи-один-допустиме? score-question)
                (спостереження-системи-один-для-запитання-допустиме?
                  choice-question (перше answers))
                (спостереження-системи-один-для-запитання-допустиме?
                  noul-question (друге answers))
                (спостереження-системи-один-для-запитання-допустиме?
                  score-question (третє answers))
                (список-спостережень-системи-один-допустимий?
                  questions answers (як-є ()))
                (усі-запитання-системи-один-відповіли? questions answers)
                ; Точні причини, чому агрегований список міг бути відхилений:
                (рішення-містить? (друге (перше answers)) questions)
                (рішення-містить? (друге (перше (решта answers))) questions)
                (рішення-містить? (друге (перше (решта (решта answers)))) questions)
                (рішення-містить? (друге (друге (перше answers)))
                  (список (друге choice-question) (друге noul-question) (друге score-question)))
                (рішення-містить? (друге (друге (перше (решта answers)))
                  (список (друге choice-question) (друге noul-question) (друге score-question)))
                (рішення-містить? (друге (друге (перше (решта (решта answers))))
                  (список (друге choice-question) (друге noul-question) (друге score-question)))
                (допустимий-розподіл? (як-є (yes no)) (третє (друге answers))))"#,
        );
        let witnesses = eval_probabilistic_decision(&diagnostic);
        panic!(
            "REGRESSION id=system-one-typed-D24 layer=real-SENS expected=(valid 3 valid) actual={actual_batch} diagnostic_D1={witnesses}"
        );
    }
    assert_eq!(actual_batch, "(valid 3 valid)");

    let invalid_batches = r#"
      (нехай-послідовно ((state (як-є ((message "double charge"))))
             (choice-question (запитання-вибору-системи-один
               (як-є route)
               "Choose the support team for this request."
               (як-є ((billing "Payment or refund issues")
                       (technical "Software malfunction")))))
             (noul-question (запитання-так-ні-системи-один
               (як-є urgent)
               "Does this request need urgent handling?"))
             (questions (список choice-question noul-question))
             (request (запит-системи-один state questions))
             (choice-answer (спостерегти-вибір-системи-один choice-question
               (список (список (як-є billing) доля-3-4)
                           (список (як-є technical) доля-1-4))
               (як-є ((source synthetic)))))
             (missing (відповідь-системи-один request (список choice-answer)))
             (duplicate (відповідь-системи-один request (список choice-answer choice-answer)))
             (duplicate-question-request
               (запит-системи-один state
                 (список choice-question
                       (запитання-так-ні-системи-один (як-є route) "Does this request require urgent handling?")))))
        (список
          (за-умовою
            ((відповідь-системи-один-допустима? missing request) (як-є valid))
            (так (як-є invalid)))
          (за-умовою
            ((відповідь-системи-один-допустима? duplicate request) (як-є valid))
            (так (як-є invalid)))
          (за-умовою
            ((перевірити-запит-системи-один? duplicate-question-request) (як-є valid))
            (так (як-є invalid)))))
    "#;
    assert_eq!(
        eval_probabilistic_decision(invalid_batches),
        "(invalid invalid invalid)"
    );

    // Перевіряємо зовнішній механізм на фіктивній локальній моделі.
    // Адаптер повертає розподіл і походження; рішення залишається за SENS.
    let listener = TcpListener::bind(("127.0.0.1", 0)).expect("bind loopback fixture");
    let port = listener.local_addr().expect("fixture address").port();
    let fixture = thread::spawn(move || {
        let (mut stream, _) = listener.accept().expect("accept model request");
        stream
            .set_read_timeout(Some(Duration::from_secs(5)))
            .expect("set fixture read timeout");
        let mut request = Vec::new();
        let mut chunk = [0_u8; 4096];
        loop {
            let received = stream.read(&mut chunk).expect("read HTTP request");
            assert!(received > 0, "client closed before complete HTTP request");
            request.extend_from_slice(&chunk[..received]);
            if let Some(header_end) = request.windows(4).position(|w| w == b"\r\n\r\n") {
                let headers = String::from_utf8_lossy(&request[..header_end]);
                let length: usize = headers
                    .lines()
                    .find_map(|line| {
                        let (name, value) = line.split_once(':')?;
                        name.eq_ignore_ascii_case("content-length")
                            .then(|| value.trim().parse().ok())
                            .flatten()
                    })
                    .expect("Content-Length");
                if request.len() >= header_end + 4 + length {
                    request.truncate(header_end + 4 + length);
                    break;
                }
            }
        }
        let payload = r#"{"choices":[{"logprobs":{"content":[{"top_logprobs":[{"token":"A","logprob":0.0},{"token":"B","logprob":-2.1972245773362196}]}]}}]}"#;
        let response = format!(
            "HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: {}\r\nConnection: close\r\n\r\n{}",
            payload.len(),
            payload
        );
        stream
            .write_all(response.as_bytes())
            .expect("write fixture response");
        String::from_utf8(request).expect("request is UTF-8 JSON")
    });

    sens_host::install();
    let endpoint = format!("http://127.0.0.1:{port}/v1/chat/completions");
    let model_source = format!(
        r#"
        (нехай-послідовно
          ((питання
             (запитання-вибору-системи-один
               (як-є маршрут)
               "Оберіть команду для обробки звернення."
               (як-є ((оплата "Платіж, рахунок або повернення коштів")
                       (технічне "Помилка програми або обладнання")))))
           (сире
             (модельний-розподіл-вибору-сире
               "{endpoint}"
               "fixture-model"
               "З мене двічі списали кошти за одну покупку."
               (третє питання)
               (четверте питання)))
           (спостереження
             (спостерегти-вибір-системи-один
               питання (друге сире) (третє сире))))
          (список
            (перше сире)
            (перше спостереження)
            (за-умовою
              ((спостереження-системи-один-для-запитання-допустиме? питання спостереження)
               (як-є valid))
              (так (як-є invalid)))
            ; Обидві ймовірності — дійсні однодоменні D48 з відповіді моделі.
            ; Штучний поріг, уведений хостом, не є доказом закону SENS.
            (за-умовою
              ((менше? (друге (друге (друге сире)))
                       (друге (перше (друге сире))))
               (як-є найбільша-ймовірність-перша))
              (так (як-є невірний-порядок)))
            (перше (перше (п'ятий спостереження)))
            (друге (перше (п'ятий спостереження)))))
        "#
    );
    assert_eq!(
        eval_probabilistic_decision(&model_source),
        "(model-distribution/1 choice-observation/1 valid найбільша-ймовірність-перша source local-model)"
    );
    let request = fixture.join().expect("fixture server");
    assert!(request.contains("\"top_logprobs\":20"));
    assert!(request.contains("\"structured_outputs\":"));
    assert!(request.contains("\"fixture-model\""));
}
