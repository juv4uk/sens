use sens::{
    eval_parsed_expressions, eval_program, parse_canonical_binary, parse_exact_domain_source,
    parse_mixed_exact_domain_reasoning_source, ExprKind, Session,
};

fn session() -> Session {
    let mut session = Session::default();
    sens::eval_core_library_source(include_str!("../../../lib/core.lisp"), &mut session)
        .expect("канонічний Core має завантажуватись власним точним reader");
    for (path, source) in [
        ("lib/unify.lisp", include_str!("../../../lib/unify.lisp")),
        ("lib/reason.lisp", include_str!("../../../lib/reason.lisp")),
    ] {
        let parsed = parse_mixed_exact_domain_reasoning_source(path, source)
            .unwrap_or_else(|error| panic!("{path}: exact source reader: {error}"));
        eval_parsed_expressions(&parsed, &mut session)
            .unwrap_or_else(|error| panic!("{path}: exact source evaluator: {error}"));
    }
    session
}

fn eval(session: &mut Session, source: &str) -> String {
    eval_program(source, session)
        .unwrap_or_else(|e| panic!("evaluation failed: {e}\nsource: {source}"))
        .value
        .to_string()
}

#[test]
fn reason_index_d1_verdicts_from_real_predicates() {
    // Виконується нативний reader/eval SENS з lib/reason.lisp.
    // Значення мають бути саме D1-бітами, не цитованими 'так'/'ні'.
    let mut s = session();
    for (expression, expected) in [
        (
            "(індекс-міркування? (як-є (reason-index-1 indexed () ())))",
            true,
        ),
        (
            "(індекс-міркування? (як-є (reason-index-1 linear () ())))",
            true,
        ),
        (
            "(індекс-міркування? (як-є (other-index indexed () ())))",
            false,
        ),
        (
            "(індекс-міркування? (як-є ((complex-head) indexed () ())))",
            false,
        ),
        ("(індекс-міркування? (як-є ()))", false),
        ("(міркування-змінний-терм? (як-є (var x)))", true),
        ("(міркування-змінний-терм? (як-є (p x)))", false),
        ("(міркування-змінний-терм? (як-є ()))", false),
        ("(міркування-змінний-терм? (як-є (x)))", false),
        // Локальне обернення — виконується SENS, D5:10100 тут не викликається.
        ("(уніфікація-рівні? (міркування-зворот (як-є ())) (як-є ()))", true),
        ("(уніфікація-рівні? (міркування-зворот (як-є (p))) (як-є (p)))", true),
        ("(уніфікація-рівні? (міркування-зворот (як-є (p q p r))) (як-є (r p q p)))", true),
        ("(уніфікація-рівні? (міркування-зворот (як-є (p q r))) (як-є (p q r)))", false),
        // D11: не дублюємо батьківські D3/D4-селектори.
        // Ці перевірки виконують справжню політику індексу та fallback у SENS.
        ("(індекс-міркування? (лінійний-індекс-міркування (як-є (((p a))))))", true),
        ("(уніфікація-рівні? (лінійний-індекс-міркування (як-є (((p a))))) (як-є (reason-index-1 linear (((p a))) ())))", true),
        ("(уніфікація-рівні? (лінійний-індекс-міркування (як-є (((p a))))) (як-є (reason-index-1 indexed (((p a))) ())))", false),
        ("(уніфікація-рівні? (міркування-пошук-кошика (як-є p) (як-є ((p ((p a))) (q ((q b)))))) (як-є (p ((p a)))))", true),
        ("(уніфікація-рівні? (міркування-пошук-кошика (як-є q) (як-є ((p ((p a))) (q ((q b)))))) (як-є (q ((q b)))))", true),
        ("(уніфікація-рівні? (міркування-пошук-кошика (як-є немає) (як-є ((p ((p a))) (q ((q b)))))) (як-є ()))", true),
        ("(уніфікація-рівні? (міркування-пошук-кошика (як-є p) (як-є (зламане (p ((p a)))))) (як-є (p ((p a)))))", true),
        ("(уніфікація-рівні? (кандидати-індексу-міркування (як-є (p a)) (лінійний-індекс-міркування (як-є (((p a)) ((q b)))))) (як-є (((p a)) ((q b)))))", true),
        ("(уніфікація-рівні? (кандидати-індексу-міркування (як-є (p a)) (лінійний-індекс-міркування (як-є (((p a)) ((q b)))))) (як-є (((p a)))))", false),
        ("(уніфікація-рівні? (кандидати-індексу-міркування (як-є (p a)) (побудувати-індекс-міркування (як-є (((p a)) ((q b)))))) (як-є (((p a)))))", true),
        ("(уніфікація-рівні? (кандидати-індексу-міркування (як-є (var x)) (побудувати-індекс-міркування (як-є (((p a)) ((q b)))))) (як-є (((p a)) ((q b)))))", true),
        ("(уніфікація-рівні? (кандидати-індексу-міркування (як-є (немає a)) (побудувати-індекс-міркування (як-є (((p a)) ((q b)))))) (як-є ()))", true),
    ] {
        let result = eval_program(expression, &mut s)
            .unwrap_or_else(|error| panic!("SENS D1 недоступний: {expression}: {error}"));
        assert_eq!(
            result.value.as_predicate_bit(),
            Some(expected),
            "функція повинна повернути обчислений D1: {expression}",
        );
    }

    // D11 research law: semantic predicate extraction, not a bare CAR alias.
    // Real SENS distinguishes compound predicate heads from logic variables,
    // malformed compound heads, and atomic/empty terms.
    for (case, program, expected) in [
        (
            "терм-складений",
            "(уніфікація-рівні? (предикат-терма-міркування (як-є (факт а))) (як-є факт))",
            true,
        ),
        (
            "терм-змінна",
            "(уніфікація-рівні? (предикат-терма-міркування (як-є (var х))) (як-є ()))",
            true,
        ),
        (
            "змінна-не-предикат",
            "(уніфікація-рівні? (предикат-терма-міркування (як-є (var х))) (як-є var))",
            false,
        ),
        (
            "терм-атом",
            "(уніфікація-рівні? (предикат-терма-міркування (як-є факт)) (як-є ()))",
            true,
        ),
        (
            "терм-порожній",
            "(уніфікація-рівні? (предикат-терма-міркування (як-є ())) (як-є ()))",
            true,
        ),
        (
            "терм-складена-голова",
            "(уніфікація-рівні? (предикат-терма-міркування (як-є ((факт) а))) (як-є ()))",
            true,
        ),
        (
            "правило-з-головою",
            "(уніфікація-рівні? (предикат-правила-міркування (як-є ((факт а) (висновок а)))) (як-є факт))",
            true,
        ),
        (
            "правило-атом",
            "(уніфікація-рівні? (предикат-правила-міркування (як-є відсутнє)) (як-є ()))",
            true,
        ),
        (
            "правило-зі-змінною",
            "(уніфікація-рівні? (предикат-правила-міркування (як-є ((var х) (висновок а)))) (як-є ()))",
            true,
        ),
        (
            "правило-складений-предикат",
            "(уніфікація-рівні? (предикат-правила-міркування (як-є (((факт) а) (висновок а)))) (як-є ()))",
            true,
        ),
        (
            "правило-хибна-голова",
            "(уніфікація-рівні? (предикат-правила-міркування (як-є ((факт а) (висновок а)))) (як-є висновок))",
            false,
        ),
    ] {
        let actual = eval_program(program, &mut s)
            .unwrap_or_else(|error| panic!(
                "test_id=D11-REASON-TERM-RULE-PREDICATE-{case} layer=SENS input={program} error={error}"
            ))
            .value;
        assert_eq!(
            actual.as_predicate_bit(),
            Some(expected),
            "test_id=D11-REASON-TERM-RULE-PREDICATE-{case} layer=SENS input={program} expected=D1:{expected} actual={actual}"
        );
    }
}

#[test]
fn proof_mapper_calls_lexically_bound_sens_closure_not_d5_function_identity() {
    // Це живе виконання SENS, не структурний Python-оракул:
    // назва параметра в зіставити-докази не може затіняти D5:00001.
    let mut s = session();
    assert_eq!(
        eval(
            &mut s,
            "(зіставити-докази (функція (значення) (перше значення)) (як-є ((one a) (two b))))"
        ),
        "(one two)",
        "кожен елемент має пройти справжній виклик локального замикання SENS"
    );
    assert_eq!(
        eval(
            &mut s,
            "(зіставити-докази (функція (значення) (перше значення)) (як-є ()))"
        ),
        "()",
        "порожні дані не можуть створювати вигадані докази"
    );
}

#[test]
fn indexed_bucket_preserves_source_rule_order_exactly() {
    let mut s = session();
    let source = r#"
      (визначити rules
        (як-є
          (((p first))
           ((q irrelevant))
           ((p second))
           ((r irrelevant))
           ((p third)))))
      (кандидати-індексу-міркування (як-є (p target)) (побудувати-індекс-міркування rules))
    "#;
    assert_eq!(
        eval(&mut s, source),
        "(((p first)) ((p second)) ((p third)))"
    );
}

#[test]
fn malformed_bucket_does_not_hide_later_valid_sens_rules() {
    // Виконання самого lib/reason.lisp через нативний reader/eval SENS.
    // Пошкоджена комірка перед правильним кошиком не приховує правило.
    let mut s = session();
    for (input, expected) in [
        (
            "(міркування-пошук-кошика (як-є p) (як-є (() (p first))))",
            "(p first)",
        ),
        (
            "(міркування-пошук-кошика (як-є p) (як-є (((bad key) orphan) (q other) (p second))))",
            "(p second)",
        ),
        (
            "(міркування-пошук-кошика (як-є missing) (як-є (() (p first))))",
            "()",
        ),
        (
            "(міркування-пошук-кошика (як-є p) (як-є (((bad key) orphan))))",
            "()",
        ),
        ("(міркування-пошук-кошика (як-є p) (як-є ()))", "()"),
    ] {
        assert_eq!(eval(&mut s, input), expected, "неповний кошик: {input}");
    }
}

#[test]
fn variable_goal_falls_back_to_every_rule() {
    let mut s = session();
    // Довжина як некваліфіковане число нині не є D24+ арифметикою.
    // Перевіряємо сильніший інваріант: усі правила + первісний порядок.
    let source = r#"
      (визначити rules (як-є (((p one)) ((q two)) ((r three)))))
      (кандидати-індексу-міркування
        (як-є (var x))
        (побудувати-індекс-міркування rules))
    "#;
    assert_eq!(eval(&mut s, source), "(((p one)) ((q two)) ((r three)))");
}

#[test]
fn variable_rule_head_disables_index_instead_of_changing_unification() {
    let mut s = session();
    let source = r#"
      (визначити rules
        (як-є
          (((p one))
           ((var whole-head))
           ((q two)))))
      (режим-індексу-міркування (побудувати-індекс-міркування rules))
    "#;
    assert_eq!(eval(&mut s, source), "linear");
}

#[test]
fn too_many_distinct_predicates_fall_back_to_linear_mode() {
    let mut s = session();
    let mut source =
        String::from("(режим-індексу-міркування (побудувати-індекс-міркування (як-є (");
    for i in 0..65 {
        source.push_str(&format!("((pred{i} value))"));
    }
    source.push_str("))))");
    assert_eq!(eval(&mut s, &source), "linear");
}

#[test]
fn binary_sens_migration_witness_checks_atom_eq_and_domain_boundaries() {
    let mut s = session();

    // The law itself is binary SENS: only admitted D3 ATOM/EQ primitives
    // decide the semantic result. No unratified user function is made callable.
    let law = include_str!("../../../tests/semantic/narrate-d3-atom-eq-law.bits");
    assert!(
        law.bytes()
            .all(|b| b.is_ascii_whitespace() || matches!(b, b'0' | b'1')),
        "the semantic witness must be visible binary words plus separators"
    );
    let forms = parse_canonical_binary(law).expect("canonical binary ATOM/EQ law");
    let verdict =
        eval_parsed_expressions(&forms, &mut s).expect("SENS rejected the canonical ATOM/EQ law");
    assert_eq!(
        verdict.value.as_predicate_bit(),
        Some(true),
        "SENS primitive law must produce exact D1:YES"
    );

    // Поведінка D3 EQ перевіряється справжнім SENS evaluator, а не
    // пошуком історичних 8-бітних текстових шаблонів у сучасному джерелі.
    // Складена голова не може потрапити до атомарного D3 EQ.
    for (source, expected) in [
        ("(індекс-міркування? (як-є ()))", false),
        (
            "(індекс-міркування? (як-є ((складена-голова) запис)))",
            false,
        ),
        (
            "(індекс-міркування? (як-є (reason-index-1 indexed ())))",
            true,
        ),
    ] {
        let result = eval_program(source, &mut s).unwrap_or_else(|error| {
            panic!("реальна перевірка індекс-міркування?: {error}; джерело: {source}")
        });
        assert_eq!(
            result.value.as_predicate_bit(),
            Some(expected),
            "D3 ATOM має захистити EQ від складеної голови: {source}"
        );
    }

    let narration_source = include_str!("../../../lib/narrate.lisp");
    let hs = narration_source
        .find("(визначити список-завершується-порожнім?")
        .expect("D3/D4 helpers exist");
    let he = narration_source[hs..]
        .find("(визначити пояснити-факт")
        .expect("helper span ends")
        .saturating_add(hs);
    let helper_source = &narration_source[hs..he];
    let helper_forms = parse_exact_domain_source(helper_source)
        .expect("arity helpers must retain exact-domain identities");
    assert_eq!(
        helper_forms.len(),
        3,
        "one proper-list helper and two arity helpers"
    );
    let mut widths = Vec::new();
    fn collect_widths(expr: &sens::Expr, widths: &mut Vec<usize>) {
        if let ExprKind::DomainIdentity(identity) = &expr.kind {
            widths.push(identity.width());
        }
        if let ExprKind::List(items) = &expr.kind {
            for item in items.iter() {
                collect_widths(item, widths);
            }
        }
    }
    for form in &helper_forms {
        collect_widths(form, &mut widths);
    }
    widths.sort_unstable();
    widths.dedup();
    // На цьому етапі reader зберігає D3/D4 як українські людські
    // імена до exact-domain lowering; у цьому AST явним є лише D1.
    // Бітовий закон ATOM/EQ та реальна поведінка індексу перевірені
    // вище виконанням SENS, а не самим підрахунком AST-позначок.
    assert_eq!(widths, vec![1], "лише явні D1 значення до lowering");
    assert!(
        helper_source.contains("(атом? значення)"),
        "D3 ATOM українською"
    );
    assert!(
        helper_source.contains("(порожній? значення)"),
        "D4 NULL українською"
    );
    let d3 = include_str!("../../../lib/domains/d3.lisp");
    let d4 = include_str!("../../../lib/domains/d4.lisp");
    assert!(
        d3.contains("(010 (ук атом?) (укр атом?)"),
        "ратифікована D3:010"
    );
    assert!(
        d4.contains("(0101 (ук порожнє?) (укр порожній?)"),
        "ратифікована D4:0101"
    );
    assert!(
        !helper_source.contains("000000"),
        "D6 LENGTH must not return to arity helpers"
    );
    assert!(
        !helper_source.contains("11110111"),
        "D8 EQUAL must not return to arity helpers"
    );
}

#[test]
fn reason_index_migration_exhausts_all_2046_exact_width_coordinate_candidates() {
    // This counts 2046 mechanical coordinates (NOT 2046 callable functions).
    // The test detects truncation, cross-domain aliasing and accidental
    // logical padding, independently of display labels or legacy SID8.
    use sens::domain_ladder::DomainCoordinate;
    use std::collections::HashSet;

    let mut seen = HashSet::new();
    let mut bit_count = 0usize;
    for width in 1u8..=10 {
        let capacity = 1u16 << width;
        for payload in 0..capacity {
            let coordinate = DomainCoordinate::new(width, payload)
                .expect("every in-width pair must be representable");
            assert!(
                seen.insert(coordinate),
                "collision in D{width}: {payload:0w$b}",
                w = usize::from(width)
            );
            bit_count += usize::from(width);
        }
        assert!(
            DomainCoordinate::new(width, capacity).is_none(),
            "oversize value must not truncate into D{width}"
        );
        assert!(DomainCoordinate::new(width, u16::MAX).is_none());
    }
    assert_eq!(seen.len(), 2046);
    assert_eq!(bit_count, 18_434);
    assert_eq!(bit_count.div_ceil(8), 2305);
    assert_eq!(8 * bit_count.div_ceil(8) - bit_count, 6);
    for width in 1u8..=9 {
        assert_ne!(
            DomainCoordinate::new(width, 1),
            DomainCoordinate::new(width + 1, 1)
        );
    }
    assert_eq!(DomainCoordinate::new(10, 1024), None);
}
